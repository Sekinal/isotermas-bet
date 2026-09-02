#!/usr/bin/env python3
"""Calculate BET specific surface areas from Isotermas.xlsx.

The source workbook does not state the adsorptive or analysis temperature. This
script therefore assumes N2 at 77 K and a molecular cross-section of 0.162 nm2.
Only the adsorption branch is used in the BET regression.
"""

from __future__ import annotations

import argparse
import re
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import xlsxwriter
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

XML_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
N_A = 6.02214076e23
N2_CROSS_SECTION_M2 = 0.162e-18
STP_MOLAR_VOLUME_CM3 = 22_414.0
N2_AREA_FACTOR = N_A * N2_CROSS_SECTION_M2 / STP_MOLAR_VOLUME_CM3

# BETSI recommends ten points when the measurement supports them. This workbook
# has only three valid low-pressure points for zeolite Y, so three is the largest
# minimum that can be applied consistently to every material without inventing
# interpolated measurements.
MIN_FIT_POINTS = 3
MIN_R_SQUARED = 0.995
MAX_MONOLAYER_ERROR_PERCENT = 20.0


@dataclass(frozen=True)
class Point:
    source_row: int
    pressure: float
    volume: float
    branch: str


@dataclass(frozen=True)
class BetFit:
    low: float
    high: float
    n: int
    slope: float
    intercept: float
    r_squared: float
    vm: float
    c_constant: float
    monolayer_pressure: float
    area: float
    rouquerol_q_increasing: bool
    bet_y_increasing: bool
    monolayer_in_range: bool
    monolayer_read_pressure: float
    monolayer_error_percent: float
    valid_window_count: int = 0
    valid_area_min: float = 0.0
    valid_area_max: float = 0.0
    valid_area_std: float = 0.0


MATERIALS = (
    "Oxido de grafeno",
    "γ-Al2O3",
    "Allende-100",
    "Zeolita Y (Si/Al =15)",
    "8%ZrO2/SBA-15",
)


INTERPRETATIONS = {
    "Oxido de grafeno": (
        "Captación intensa a P/P0 muy baja e histéresis amplia a presión alta; "
        "los datos sugieren contribuciones combinadas de micro- y mesoporos."
    ),
    "γ-Al2O3": (
        "Perfil mesoporoso semejante al tipo IV, con histéresis amplia a P/P0 intermedia y alta."
    ),
    "Allende-100": (
        "Adsorción y área específica muy bajas; la mayor captación ocurre cerca de la saturación."
    ),
    "Zeolita Y (Si/Al =15)": (
        "Perfil microporoso semejante al tipo I: captación alta a baja presión seguida de una meseta. "
        "Solo tres puntos satisfacen los criterios BET; el valor es sensible al muestreo."
    ),
    "8%ZrO2/SBA-15": (
        "Perfil mesoporoso semejante al tipo IV, con un escalón de condensación capilar cerca de "
        "P/P0=0,74-0,78."
    ),
}


def column_name(cell_reference: str) -> str:
    match = re.match(r"[A-Z]+", cell_reference)
    if not match:
        raise ValueError(f"Invalid Excel cell reference: {cell_reference}")
    return match.group(0)


def next_column(column: str) -> str:
    value = 0
    for character in column:
        value = value * 26 + ord(character) - ord("A") + 1
    value += 1
    result = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def read_first_sheet(path: Path) -> dict[int, dict[str, str | float]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall(XML_NS + "si"):
                shared_strings.append("".join(node.text or "" for node in item.iter(XML_NS + "t")))

        sheet_root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: dict[int, dict[str, str | float]] = {}
        for row_node in sheet_root.findall(f".//{XML_NS}sheetData/{XML_NS}row"):
            row_number = int(row_node.attrib["r"])
            row: dict[str, str | float] = {}
            for cell in row_node.findall(XML_NS + "c"):
                value_node = cell.find(XML_NS + "v")
                if value_node is None:
                    continue
                column = column_name(cell.attrib["r"])
                if cell.attrib.get("t") == "s":
                    value: str | float = shared_strings[int(value_node.text)]
                else:
                    value = float(value_node.text)
                row[column] = value
            rows[row_number] = row
    return rows


def extract_datasets(path: Path) -> dict[str, list[Point]]:
    rows = read_first_sheet(path)
    header = rows[1]
    datasets: dict[str, list[Point]] = {}
    for pressure_column, material_value in header.items():
        if not isinstance(material_value, str) or material_value not in MATERIALS:
            continue
        volume_column = next_column(pressure_column)
        raw: list[tuple[int, float, float]] = []
        for row_number in sorted(number for number in rows if number >= 3):
            row = rows[row_number]
            pressure = row.get(pressure_column)
            volume = row.get(volume_column)
            if isinstance(pressure, float) and isinstance(volume, float):
                raw.append((row_number, pressure, volume))

        # The first repeated or decreasing pressure marks the desorption branch.
        turn = len(raw)
        for index in range(1, len(raw)):
            if raw[index][1] <= raw[index - 1][1]:
                turn = index
                break
        points = [
            Point(row, pressure, volume, "Adsorption" if i < turn else "Desorption")
            for i, (row, pressure, volume) in enumerate(raw)
        ]
        datasets[material_value] = points
    return datasets


def bet_transform(pressure: np.ndarray, volume: np.ndarray) -> np.ndarray:
    return pressure / (volume * (1.0 - pressure))


def _fit_window(
    pressure: np.ndarray,
    volume: np.ndarray,
    start: int,
    end: int,
    volume_interpolator: PchipInterpolator,
) -> BetFit | None:
    """Fit one inclusive, contiguous window of the adsorption branch.

    The returned object contains every quantity needed by the four Rouquerol
    checks. Invalid algebraic fits return ``None`` before the physical criteria
    are considered.
    """

    window_pressure = pressure[start : end + 1]
    window_volume = volume[start : end + 1]
    transformed = bet_transform(window_pressure, window_volume)
    design = np.column_stack((window_pressure, np.ones_like(window_pressure)))
    slope, intercept = np.linalg.lstsq(design, transformed, rcond=None)[0]

    # Positive slope and intercept are stricter and easier to audit than merely
    # accepting a positive C value that could result from two negative numbers.
    if slope <= 0 or intercept <= 0:
        return None

    fitted = slope * window_pressure + intercept
    residual_sum = float(np.sum((transformed - fitted) ** 2))
    total_sum = float(np.sum((transformed - np.mean(transformed)) ** 2))
    r_squared = 1.0 - residual_sum / total_sum if total_sum else 1.0
    vm = 1.0 / (slope + intercept)
    c_constant = 1.0 + slope / intercept
    if vm <= 0 or c_constant <= 0 or not np.isfinite(c_constant):
        return None

    monolayer_pressure = 1.0 / (np.sqrt(c_constant) + 1.0)

    # Criterion 3 uses the pressure read from the measured isotherm at V=Vm.
    # PCHIP preserves the shape of these monotonic adsorption data. Root finding
    # avoids treating interpolated values as additional experimental points.
    if not volume[0] <= vm <= volume[-1]:
        return None
    monolayer_read_pressure = float(
        brentq(
            lambda relative_pressure: float(volume_interpolator(relative_pressure) - vm),
            float(pressure[0]),
            float(pressure[-1]),
        )
    )
    monolayer_in_range = bool(window_pressure[0] <= monolayer_read_pressure <= window_pressure[-1])
    monolayer_error_percent = (
        abs(monolayer_read_pressure - monolayer_pressure) / monolayer_read_pressure * 100.0
    )
    q_values = window_volume * (1.0 - window_pressure)

    return BetFit(
        low=float(window_pressure[0]),
        high=float(window_pressure[-1]),
        n=len(window_pressure),
        slope=float(slope),
        intercept=float(intercept),
        r_squared=r_squared,
        vm=vm,
        c_constant=c_constant,
        monolayer_pressure=float(monolayer_pressure),
        area=vm * N2_AREA_FACTOR,
        rouquerol_q_increasing=bool(np.all(np.diff(q_values) >= 0)),
        bet_y_increasing=bool(np.all(np.diff(transformed) >= 0)),
        monolayer_in_range=monolayer_in_range,
        monolayer_read_pressure=monolayer_read_pressure,
        monolayer_error_percent=monolayer_error_percent,
    )


def _passes_consistency_checks(fit: BetFit) -> bool:
    """Return whether a candidate satisfies the configured BETSI-style checks."""

    return (
        fit.n >= MIN_FIT_POINTS
        and fit.r_squared >= MIN_R_SQUARED
        and fit.rouquerol_q_increasing
        and fit.bet_y_increasing
        and fit.c_constant > 0
        and fit.monolayer_in_range
        and fit.monolayer_error_percent <= MAX_MONOLAYER_ERROR_PERCENT
    )


def select_optimal_fit(points: list[Point]) -> BetFit:
    """Enumerate and select the optimal BET window without manual endpoints.

    This follows the BETSI strategy: test every consecutive window, retain those
    satisfying the Rouquerol criteria, select windows ending at the highest
    permissible pressure (the isotherm knee), then choose the one with the lowest
    criterion-4 monolayer-pressure error. No synthetic measurement points are added.
    """

    adsorption = [point for point in points if point.branch == "Adsorption"]
    pressure = np.array([point.pressure for point in adsorption], dtype=float)
    volume = np.array([point.volume for point in adsorption], dtype=float)
    if len(pressure) < MIN_FIT_POINTS:
        raise ValueError("Not enough adsorption points for a multipoint BET fit")
    if np.any(np.diff(pressure) <= 0) or np.any(np.diff(volume) <= 0):
        raise ValueError("Adsorption pressure and volume must increase strictly")

    volume_interpolator = PchipInterpolator(pressure, volume)
    candidates: list[tuple[int, BetFit]] = []
    for start in range(len(pressure)):
        for end in range(start + MIN_FIT_POINTS - 1, len(pressure)):
            fit = _fit_window(pressure, volume, start, end, volume_interpolator)
            if fit is not None and _passes_consistency_checks(fit):
                candidates.append((end, fit))

    if not candidates:
        raise ValueError("No BET window satisfies all configured consistency checks")

    knee_index = max(end for end, _ in candidates)
    knee_candidates = [fit for end, fit in candidates if end == knee_index]
    optimal = min(
        knee_candidates,
        key=lambda fit: (fit.monolayer_error_percent, -fit.r_squared, -fit.n),
    )
    valid_areas = np.array([fit.area for _, fit in candidates], dtype=float)
    return replace(
        optimal,
        valid_window_count=len(candidates),
        valid_area_min=float(np.min(valid_areas)),
        valid_area_max=float(np.max(valid_areas)),
        valid_area_std=float(np.std(valid_areas)),
    )


def write_report(
    output_path: Path,
    source_path: Path,
    datasets: dict[str, list[Point]],
    fits: dict[str, BetFit],
) -> None:
    workbook = xlsxwriter.Workbook(output_path)
    workbook.set_properties(
        {
            "title": "BET surface-area analysis of adsorption isotherms",
            "comments": "Assumes N2 at 77 K and 0.162 nm2 molecular cross-section.",
        }
    )
    title = workbook.add_format(
        {"bold": True, "font_size": 16, "font_color": "#FFFFFF", "bg_color": "#1F4E78"}
    )
    heading = workbook.add_format(
        {"bold": True, "font_color": "#FFFFFF", "bg_color": "#5B9BD5", "border": 1}
    )
    subheading = workbook.add_format({"bold": True, "bg_color": "#D9EAF7", "border": 1})
    cell = workbook.add_format({"border": 1})
    number = workbook.add_format({"border": 1, "num_format": "0.0000"})
    area_format = workbook.add_format({"border": 1, "num_format": "0.0"})
    scientific = workbook.add_format({"border": 1, "num_format": "0.000E+00"})
    note = workbook.add_format({"text_wrap": True, "valign": "top", "bg_color": "#FFF2CC"})
    good = workbook.add_format({"border": 1, "font_color": "#006100", "bg_color": "#C6EFCE"})

    summary = workbook.add_worksheet("Summary")
    summary.hide_gridlines(2)
    summary.set_column("A:A", 25)
    summary.set_column("B:B", 18)
    summary.set_column("C:I", 14)
    summary.set_column("J:J", 58)
    summary.merge_range("A1:J1", "BET specific surface-area analysis", title)
    summary.merge_range(
        "A3:J4",
        "Critical assumption: N2 adsorption at 77 K, molecular cross-section 0.162 nm2, "
        "molar gas volume 22,414 cm3/mol at STP. The source workbook does not state "
        "the adsorptive or temperature. Areas must be recalculated if this assumption is wrong.",
        note,
    )
    headers = [
        "Material",
        "BET area (m2/g)",
        "Fit P/P0 low",
        "Fit P/P0 high",
        "Points",
        "R2",
        "C",
        "Criterion 4 error (%)",
        "Valid windows",
        "Interpretation / caveat",
    ]
    for column_index, value in enumerate(headers):
        summary.write(6, column_index, value, heading)
    for row_index, material in enumerate(MATERIALS, start=7):
        fit = fits[material]
        values = [
            material,
            fit.area,
            fit.low,
            fit.high,
            fit.n,
            fit.r_squared,
            fit.c_constant,
            fit.monolayer_error_percent,
            fit.valid_window_count,
            INTERPRETATIONS[material],
        ]
        for column_index, value in enumerate(values):
            fmt = cell
            if column_index == 1:
                fmt = area_format
            elif column_index in (2, 3, 5, 6, 7):
                fmt = number
            summary.write(row_index, column_index, value, fmt)
        summary.set_row(row_index, 42)
    summary.write(14, 0, "Source workbook", subheading)
    summary.write(14, 1, str(source_path), cell)
    summary.write(15, 0, "N2 area factor", subheading)
    summary.write(15, 1, N2_AREA_FACTOR, number)
    summary.write(15, 2, "m2 per cm3(STP)", cell)
    summary.write(17, 0, "Method", subheading)
    summary.merge_range(
        "B18:J22",
        "BET plot: y=(P/P0)/[V(1-P/P0)] versus x=P/P0. From y=sx+i, "
        "Vm=1/(s+i), C=1+s/i, and S_BET=Vm*N_A*sigma/Vmolar. Every consecutive "
        "adsorption-branch window was tested against the four Rouquerol criteria and R2>=0.995. "
        "Following BETSI, the selected window ends at the highest permissible pressure and has "
        "the lowest monolayer-pressure error. No synthetic measurement points were added.",
        cell,
    )

    for sheet_index, material in enumerate(MATERIALS, start=1):
        points = datasets[material]
        fit = fits[material]
        low, high = fit.low, fit.high
        sheet_name = f"{sheet_index}_{material}"[:31].replace("/", "-")
        sheet = workbook.add_worksheet(sheet_name)
        sheet.hide_gridlines(2)
        sheet.freeze_panes(9, 0)
        sheet.set_column("A:A", 12)
        sheet.set_column("B:C", 17)
        sheet.set_column("D:D", 13)
        sheet.set_column("E:G", 18)
        sheet.merge_range("A1:G1", material, title)
        metrics = [
            ("BET area (m2/g)", fit.area, area_format),
            ("Vm (cm3 STP/g)", fit.vm, number),
            ("C constant", fit.c_constant, number),
            ("R2", fit.r_squared, number),
            ("Fit range", f"{fit.low:.6g} to {fit.high:.6g}", cell),
            ("Points / valid windows", f"{fit.n} / {fit.valid_window_count}", cell),
            ("Criterion 4 error (%)", fit.monolayer_error_percent, number),
            ("All criteria", "PASS", good),
        ]
        for metric_index, (label, value, fmt) in enumerate(metrics):
            row = 2 + metric_index % 4
            column = 0 if metric_index < 4 else 3
            sheet.write(row, column, label, subheading)
            sheet.write(row, column + 1, value, fmt)
        raw_headers = [
            "Source row",
            "P/P0",
            "V (cm3 STP/g)",
            "Branch",
            "BET y (selected)",
            "Selected",
            "Fitted y",
        ]
        for column_index, value in enumerate(raw_headers):
            sheet.write(8, column_index, value, heading)
        for point_index, point in enumerate(points, start=9):
            selected = point.branch == "Adsorption" and low <= point.pressure <= high
            y_value = (
                point.pressure / (point.volume * (1.0 - point.pressure))
                if selected and point.pressure < 1.0
                else None
            )
            fitted_y = fit.slope * point.pressure + fit.intercept if selected else None
            sheet.write_number(point_index, 0, point.source_row, cell)
            sheet.write_number(point_index, 1, point.pressure, number)
            sheet.write_number(point_index, 2, point.volume, number)
            sheet.write(point_index, 3, point.branch, cell)
            if y_value is not None:
                sheet.write_number(point_index, 4, y_value, scientific)
            if selected:
                sheet.write(point_index, 5, "Yes", good)
                sheet.write_number(point_index, 6, fitted_y, scientific)

        last_excel_row = 9 + len(points)
        chart = workbook.add_chart({"type": "scatter", "subtype": "straight_with_markers"})
        chart.add_series(
            {
                "name": "Adsorption/desorption data",
                "categories": f"='{sheet_name}'!$B$10:$B${last_excel_row}",
                "values": f"='{sheet_name}'!$C$10:$C${last_excel_row}",
                "marker": {
                    "type": "circle",
                    "size": 3,
                    "border": {"color": "#1F77B4"},
                    "fill": {"color": "#1F77B4"},
                },
                "line": {"color": "#1F77B4", "width": 1.0},
            }
        )
        chart.set_title({"name": f"{material}: isotherm"})
        chart.set_x_axis({"name": "Relative pressure, P/P0", "min": 0, "max": 1})
        chart.set_y_axis(
            {"name": "Adsorbed volume (cm3 STP/g)", "major_gridlines": {"visible": True}}
        )
        chart.set_legend({"none": True})
        chart.set_size({"width": 650, "height": 380})
        sheet.insert_chart("I2", chart)

        bet_chart = workbook.add_chart({"type": "scatter", "subtype": "straight_with_markers"})
        # Excel ignores blank cells, leaving only selected rows in these series.
        bet_chart.add_series(
            {
                "name": "Selected BET points",
                "categories": f"='{sheet_name}'!$B$10:$B${last_excel_row}",
                "values": f"='{sheet_name}'!$E$10:$E${last_excel_row}",
                "marker": {"type": "circle", "size": 5, "fill": {"color": "#ED7D31"}},
                "line": {"none": True},
            }
        )
        bet_chart.add_series(
            {
                "name": "Linear fit",
                "categories": f"='{sheet_name}'!$B$10:$B${last_excel_row}",
                "values": f"='{sheet_name}'!$G$10:$G${last_excel_row}",
                "marker": {"type": "none"},
                "line": {"color": "#C00000", "width": 1.5},
            }
        )
        bet_chart.set_title({"name": "BET linear fit"})
        bet_chart.set_x_axis({"name": "P/P0"})
        bet_chart.set_y_axis({"name": "(P/P0) / [V(1-P/P0)]"})
        bet_chart.set_size({"width": 650, "height": 380})
        sheet.insert_chart("I22", bet_chart)

    workbook.close()


def write_markdown(
    output_path: Path,
    source_path: Path,
    datasets: dict[str, list[Point]],
    fits: dict[str, BetFit],
) -> None:
    lines = [
        "# Análisis de área superficial BET",
        "",
        f"Fuente: `{source_path}`",
        "",
        (
            "> Suposición: adsorción de N2 a 77 K, sección molecular de 0,162 nm2 y "
            "22 414 cm3/mol en STP. El libro fuente no especifica gas ni temperatura."
        ),
        "",
        "| Material | Área BET (m2/g) | Ajuste P/P0 | n | R2 | C | Error C4 (%) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for material in MATERIALS:
        fit = fits[material]
        lines.append(
            f"| {material} | {fit.area:.1f} | {fit.low:.5g}-{fit.high:.5g} | "
            f"{fit.n} | {fit.r_squared:.6f} | {fit.c_constant:.1f} | "
            f"{fit.monolayer_error_percent:.2f} |"
        )
    lines.extend(["", "## Interpretación", ""])
    for material in MATERIALS:
        lines.append(f"- **{material}:** {INTERPRETATIONS[material]}")
    lines.extend(
        [
            "",
            "## Nota de validación importante",
            "",
            (
                "El ajuste convencional 0,05-0,30 de la zeolita Y produce una intersección/C BET "
                "negativa e incumple el criterio de crecimiento de V(1-P/P0), por lo que se "
                "rechazó. El área informada usa los únicos tres puntos medidos que satisfacen "
                "todos los criterios; se recomiendan más puntos a baja presión."
            ),
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent / "datos" / "Isotermas.xlsx",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("BET_surface_area_analysis.xlsx"),
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=Path("BET_surface_area_analysis.md"),
    )
    args = parser.parse_args()
    datasets = extract_datasets(args.input)
    missing = set(MATERIALS) - set(datasets)
    if missing:
        raise RuntimeError(f"Missing datasets in source workbook: {sorted(missing)}")
    fits = {material: select_optimal_fit(datasets[material]) for material in MATERIALS}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    write_report(args.output, args.input, datasets, fits)
    write_markdown(args.markdown, args.input, datasets, fits)
    for material, fit in fits.items():
        print(
            f"{material}: {fit.area:.1f} m2/g "
            f"(P/P0 {fit.low:.5g}-{fit.high:.5g}, n={fit.n}, R2={fit.r_squared:.6f}, "
            f"criterion-4 error={fit.monolayer_error_percent:.2f}%)"
        )


if __name__ == "__main__":
    main()
