from pathlib import Path

import pytest

from analyze_isotherms import MATERIALS, extract_datasets, select_optimal_fit

DATA_FILE = Path(__file__).resolve().parents[1] / "datos" / "Isotermas.xlsx"


@pytest.fixture(scope="module")
def analyses():
    datasets = extract_datasets(DATA_FILE)
    return {material: select_optimal_fit(datasets[material]) for material in MATERIALS}


def test_all_expected_materials_are_extracted():
    datasets = extract_datasets(DATA_FILE)
    assert tuple(datasets) == MATERIALS
    assert all(
        any(point.branch == "Adsorption" for point in points) for points in datasets.values()
    )
    assert all(
        any(point.branch == "Desorption" for point in points) for points in datasets.values()
    )


@pytest.mark.parametrize(
    ("material", "expected_area"),
    [
        ("Oxido de grafeno", 115.9853),
        ("γ-Al2O3", 251.3063),
        ("Allende-100", 1.232864),
        ("Zeolita Y (Si/Al =15)", 993.8712),
        ("8%ZrO2/SBA-15", 663.4084),
    ],
)
def test_reproduces_reviewed_bet_areas(analyses, material, expected_area):
    assert analyses[material].area == pytest.approx(expected_area, rel=1e-5)


def test_every_selected_window_passes_all_consistency_checks(analyses):
    for fit in analyses.values():
        assert fit.rouquerol_q_increasing
        assert fit.bet_y_increasing
        assert fit.c_constant > 0
        assert fit.monolayer_in_range
        assert fit.monolayer_error_percent <= 20.0
        assert fit.r_squared >= 0.995
        assert fit.valid_window_count >= 1
