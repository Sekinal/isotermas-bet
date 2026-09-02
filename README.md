# Análisis BET de isotermas de adsorción

Análisis reproducible de cinco isotermas de adsorción/desorción para determinar el área superficial específica mediante el método BET. El repositorio contiene los datos originales, el cálculo en Python, pruebas automáticas, un informe en Typst y un libro de Excel con los ajustes y las gráficas.

## Resultados

| Material | Área BET (m²/g) | Intervalo P/P₀ | Puntos | R² | Error del criterio 4 |
|---|---:|---:|---:|---:|---:|
| Óxido de grafeno | 116,0 | 0,0497–0,3010 | 6 | 0,999937 | 3,38 % |
| γ-Al₂O₃ | 251,3 | 0,02946–0,66990 | 22 | 0,999771 | 1,73 % |
| Allende-100 | 1,23 | 0,01804–0,24772 | 11 | 0,999781 | 0,27 % |
| Zeolita Y (Si/Al = 15) | 993,9 | 0,00979–0,06078 | 3 | 0,999991 | 4,33 % |
| 8 % ZrO₂/SBA-15 | 663,4 | 0,06278–0,20012 | 8 | 0,999948 | 0,92 % |

> **Suposición crítica:** el archivo original no identifica el adsorbato ni la temperatura. Los cálculos suponen N₂ a 77 K, sección transversal molecular de 0,162 nm² y volumen molar de 22 414 cm³/mol en STP.

## Método

El programa analiza únicamente la rama de adsorción y enumera todas las ventanas consecutivas con tres puntos o más. Cada ventana debe cumplir:

1. crecimiento monótono de `V(1-P/P₀)` y de la ordenada BET;
2. pendiente, intersección y constante C positivas;
3. presión correspondiente a la monocapa leída en la isoterma dentro del intervalo lineal;
4. diferencia menor o igual al 20 % entre la presión de monocapa BET y la leída en la isoterma;
5. R² ≥ 0,995.

Entre las ventanas válidas se seleccionan las que terminan en la mayor presión permisible —la rodilla de la isoterma— y, dentro de ese grupo, la de menor error del cuarto criterio. Esta selección sigue la estrategia BETSI y evita elegir manualmente un intervalo por su R². No se agregan puntos experimentales sintéticos.

La resolución de la zeolita Y obliga a usar un mínimo de tres puntos: es la única ventana válida. Por ello, su resultado debe considerarse un **área BET aparente y sensible al muestreo**, no una medición geométrica absoluta de la superficie microporosa.

## Ejecución

Se requiere `uv` y Python 3.12 o posterior.

```bash
uv sync --dev
uv run python analyze_isotherms.py
```

El comando genera:

- `BET_surface_area_analysis.xlsx`: datos, parámetros, comprobaciones y gráficas;
- `BET_surface_area_analysis.md`: resumen numérico;
- la salida de consola con el intervalo y el error del criterio 4.

Para compilar el informe:

```bash
typst compile Informe_area_superficial_BET.typ Informe_area_superficial_BET.pdf
```

## Validación y estilo

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
./verificar_informe.sh
```

`verificar_informe.sh` usa Typstyle 0.15.1 y Typst. Si falta el formateador local, el propio script muestra el comando de instalación fijado por versión.

## Fundamento científico

- [ISO 9277:2022](https://www.iso.org/standard/71014.html), determinación del área específica por adsorción de gases mediante BET.
- [Recomendaciones IUPAC 2015](https://doi.org/10.1515/pac-2014-1117), evaluación de superficie y porosidad por fisisorción.
- [Osterrieth et al., 2022](https://doi.org/10.1002/adma.202201502), método BETSI para una selección reproducible de la región BET.

ISO 9277 señala que el BET clásico es directamente aplicable a isotermas tipo II y IV y requiere una estrategia específica y cautela para sólidos microporosos tipo I. También advierte que el cuadrupolo del N₂ puede producir desviaciones importantes en algunas superficies; Ar a 87 K es una alternativa más robusta para ciertos sólidos, y Kr a 77 K es preferible alrededor de 1 m²/g o menos.

## Estructura

```text
datos/Isotermas.xlsx              Datos experimentales originales
analyze_isotherms.py              Lectura, selección BETSI y generación de resultados
tests/test_analysis.py            Pruebas de regresión y criterios físicos
Informe_area_superficial_BET.typ  Informe técnico comentado en español
verificar_informe.sh              Linter y compilación de Typst
pyproject.toml / uv.lock          Dependencias reproducibles
```
