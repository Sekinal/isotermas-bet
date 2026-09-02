// =============================================================================
// INFORME DE ÁREA SUPERFICIAL BET
//
// Este archivo contiene únicamente la presentación del informe. Los valores
// numéricos provienen del análisis reproducible de `analyze_isotherms.py`.
// Para validar formato y compilación, ejecute `./verificar_informe.sh`.
// =============================================================================

// Paleta breve y deliberadamente sobria. Centralizar los colores aquí permite
// modificar la identidad visual sin buscar valores RGB por todo el documento.
#let azul = rgb("1f4e78")
#let azul-claro = rgb("d9eaf7")
#let gris = rgb("5f6b73")
#let gris-claro = rgb("eef2f4")
#let amarillo-claro = rgb("fff4cc")

// Metadatos internos del PDF. El campo de autor se deja vacío porque el archivo
// original no proporciona un nombre y no conviene inventarlo.
#set document(
  title: "Análisis de isotermas y área superficial BET",
  author: "",
  date: datetime(year: 2026, month: 9, day: 1),
)

// Configuración de página: A4, márgenes aptos para impresión y folio centrado.
#set page(
  paper: "a4",
  margin: (x: 2cm, y: 1.8cm),
  numbering: "1",
  number-align: center,
)

// Tipografía y reglas globales. `lang: "es"` activa las convenciones de idioma
// correspondientes, mientras que la justificación mantiene un aspecto técnico.
#set text(
  font: "Libertinus Serif",
  size: 10.5pt,
  lang: "es",
)
#set par(justify: true, leading: 0.68em)
#set heading(numbering: "1.")
#show heading: set text(fill: azul)
#show heading.where(level: 1): set block(above: 1.2em, below: 0.55em)
#show heading.where(level: 2): set block(above: 0.9em, below: 0.4em)

// Portada compacta: evita una página de título aislada y lleva al lector
// directamente a la advertencia experimental y a los resultados.
#align(center)[
  #text(19pt, weight: "bold", fill: azul)[
    Análisis de isotermas de adsorción
  ]
  #v(3pt)
  #text(14pt, weight: "semibold", fill: gris)[
    Determinación del área superficial específica mediante el método BET
  ]
  #v(8pt)
  #line(length: 100%, stroke: 1.5pt + azul)
  #v(6pt)
  #text(9.5pt, fill: gris)[
    Archivo analizado: _Isotermas.xlsx_ · Fecha del informe: 1 de septiembre de 2026
  ]
]

#v(10pt)

// Esta advertencia debe permanecer cerca del inicio. La identidad del gas y la
// temperatura cambian el factor de conversión y, por tanto, el área calculada.
#block(
  width: 100%,
  fill: amarillo-claro,
  stroke: 0.8pt + rgb("d6b656"),
  radius: 4pt,
  inset: 10pt,
)[
  *Suposición indispensable.* El archivo original presenta $P/P_0$ y volumen
  adsorbido en cm³(STP)/g, pero no identifica el adsorbato ni la temperatura.
  Los cálculos de este informe suponen adsorción de *nitrógeno a 77 K*, un área
  transversal molecular de 0,162 nm² y un volumen molar de 22 414 cm³/mol en
  condiciones estándar. Si el gas o la temperatura fueron diferentes, las áreas
  deberán recalcularse.
]

= Resumen ejecutivo

Se analizaron las ramas de adsorción y desorción de cinco materiales. El área
superficial específica se obtuvo con la ecuación de Brunauer–Emmett–Teller (BET),
empleando únicamente la rama de adsorción y seleccionando intervalos lineales que
cumplen criterios físicos de consistencia.

#v(4pt)

// Tabla principal. Se usan comas decimales por tratarse de un informe en español.
// `n` es la cantidad de puntos incluida en cada regresión BET.
#table(
  columns: (2fr, 0.9fr, 1.25fr, 0.42fr, 0.78fr, 0.72fr, 0.85fr),
  align: (left, right, center, center, right, right, right),
  inset: (x: 5pt, y: 5.5pt),
  stroke: 0.45pt + rgb("b8c2c8"),
  table.header(
    table.cell(fill: azul)[#text(weight: "bold", fill: white)[Material]],
    table.cell(fill: azul)[#text(weight: "bold", fill: white)[Área BET\ (m²/g)]],
    table.cell(fill: azul)[#text(weight: "bold", fill: white)[Intervalo\ $P/P_0$]],
    table.cell(fill: azul)[#text(weight: "bold", fill: white)[$n$]],
    table.cell(fill: azul)[#text(weight: "bold", fill: white)[$R^2$]],
    table.cell(fill: azul)[#text(weight: "bold", fill: white)[$C$]],
    table.cell(fill: azul)[#text(weight: "bold", fill: white)[Error C4]],
  ),
  [Óxido de grafeno], [116,0], [0,0497–0,3010], [6], [0,999937], [121,1], [3,38 %],
  [$gamma$-Al₂O₃], [251,3], [0,02946–0,66990], [22], [0,999771], [70,5], [1,73 %],
  [Allende-100], [1,23], [0,01804–0,24772], [11], [0,999781], [63,2], [0,27 %],
  [Zeolita Y\ (Si/Al = 15)], [993,9], [0,00979–0,06078], [3], [0,999991], [1986,9], [4,33 %],
  [8 % ZrO₂/SBA-15], [663,4], [0,06278–0,20012], [8], [0,999948], [116,1], [0,92 %],
)

#v(5pt)

El orden de área superficial es:

// La jerarquía visual resume la comparación sin reemplazar los valores numéricos.
#align(center)[
  #block(
    fill: azul-claro,
    radius: 4pt,
    inset: 8pt,
  )[
    *Zeolita Y > 8 % ZrO₂/SBA-15 > $gamma$-Al₂O₃ > óxido de grafeno >> Allende-100*
  ]
]

= Metodología

== Transformación BET

// Las ecuaciones siguientes documentan exactamente la transformación y evitan
// que el resultado quede presentado como una "caja negra".
Para cada punto de la rama de adsorción se calculó la ordenada BET:

#align(center)[
  $ y = (P/P_0) / (V (1 - P/P_0)) $
]

La regresión lineal se expresó como $y = s x + i$, donde $x = P/P_0$,
$s$ es la pendiente e $i$ la intersección. A partir de estos parámetros se
obtuvieron el volumen de monocapa y la constante BET:

#align(center)[
  $ V_m = 1 / (s + i) quad "y" quad C = 1 + s/i $
]

El área superficial específica se calculó mediante:

#align(center)[
  $ S_("BET") = (V_m N_A sigma) / V_("molar") $
]

Con nitrógeno y las constantes indicadas, el factor de conversión empleado fue
aproximadamente 4,3526 m² por cada cm³(STP) de volumen de monocapa y por gramo de
muestra.

== Selección del intervalo lineal

// R² no es suficiente para validar un ajuste BET. Estos criterios representan
// las verificaciones físicas empleadas en la selección de los intervalos.
No se eligieron los intervalos únicamente por el valor de $R^2$. Cada ajuste
aceptado cumplió las siguientes condiciones:

- pendiente e intersección BET positivas;
- aumento de $V(1-P/P_0)$ dentro del intervalo seleccionado;
- presión correspondiente a la monocapa leída en la isoterma dentro del intervalo de ajuste;
- diferencia máxima del 20 % entre la presión de monocapa BET y la leída en la isoterma;
- número suficiente de puntos medidos, cuando la resolución experimental lo permitió;
- uso exclusivo de la rama de adsorción.

Se enumeraron todas las ventanas consecutivas posibles con tres puntos o más y
$R^2 >= 0,995$. Siguiendo la estrategia BETSI, se eligió la ventana que termina
en la mayor presión permisible y, entre las que comparten ese extremo, la de menor
error de presión de monocapa. No se añadieron puntos experimentales interpolados.

= Interpretación de las isotermas

// Cada subsección combina el valor cuantitativo con una lectura prudente de la
// forma de la isoterma. No se infieren distribuciones de poro que no fueron medidas.
== Óxido de grafeno

El área BET calculada es *116,0 m²/g*. La adsorción apreciable a presiones
relativas muy bajas indica una contribución de poros pequeños o sitios de alta
energía. La histéresis amplia a presiones mayores sugiere además una contribución
mesoporosa. En conjunto, la isoterma es compatible con una textura de porosidad
mixta y con heterogeneidad superficial.

== $gamma$-Al₂O₃

El área BET es *251,3 m²/g*. El perfil es semejante a una isoterma tipo IV, con
una región de histéresis amplia a presiones relativas intermedias y altas. Este
comportamiento es característico de un sólido predominantemente mesoporoso.

== Allende-100

El área BET obtenida es *1,23 m²/g*, muy inferior a la de los demás materiales.
La captación de gas es pequeña en casi todo el intervalo y aumenta principalmente
cerca de la saturación. Esto indica una superficie accesible reducida y una
contribución limitada de micro- y mesoporos al área total.

== Zeolita Y (Si/Al = 15)

El área BET calculada es *993,9 m²/g*, la mayor del conjunto. La elevada captación
a baja presión seguida por una meseta es semejante a una isoterma tipo I y confirma
el carácter fuertemente microporoso de la zeolita.

// La zeolita requiere una advertencia propia: el ajuste convencional es
// matemáticamente lineal, pero físicamente inválido según los criterios BET.
#block(
  width: 100%,
  fill: amarillo-claro,
  stroke: 0.7pt + rgb("d6b656"),
  radius: 4pt,
  inset: 9pt,
)[
  *Precaución para la zeolita Y.* El ajuste convencional entre $P/P_0 = 0,05$ y
  0,30 produce una intersección y una constante $C$ negativas, además de incumplir
  el criterio de crecimiento de $V(1-P/P_0)$. Por ello se rechazó. El valor
  reportado utiliza los únicos tres puntos disponibles que satisfacen los criterios,
  entre 0,00979 y 0,06078. Aunque el ajuste tiene un $R^2$ alto, el resultado es
  sensible a la escasa resolución experimental en esta región.
]

== 8 % ZrO₂/SBA-15

El área BET es *663,4 m²/g*. La isoterma presenta un comportamiento semejante al
tipo IV y un aumento abrupto asociado con condensación capilar aproximadamente
entre $P/P_0 = 0,74$ y 0,78. El perfil concuerda con una estructura mesoporosa de
alta área, propia de materiales basados en SBA-15.

= Calidad y limitaciones del resultado

// Estas limitaciones separan lo que sí sustenta el archivo de lo que requeriría
// información experimental adicional o un método complementario.
- Los valores son áreas específicas BET, no distribuciones de tamaño de poro ni
  áreas externas obtenidas por métodos como el gráfico $t$.
- El archivo no contiene información sobre masa de muestra, desgasificación,
  equilibrio, adsorbato o temperatura. Estas condiciones deben documentarse para
  una trazabilidad experimental completa.
- En materiales microporosos, especialmente la zeolita Y, el modelo BET tiene
  limitaciones conceptuales y una fuerte sensibilidad al intervalo seleccionado.
- La norma ISO 9277 advierte que el momento cuadrupolar del N₂ puede causar
  desviaciones del orden del 20 % en algunas superficies. Para microporos puede
  ser preferible Ar a 87 K; para áreas cercanas a 1 m²/g, como Allende-100, se
  recomienda comprobar la sensibilidad mediante adsorción de Kr a 77 K.
- Los elevados valores de $R^2$ describen la linealidad de los puntos elegidos,
  pero no sustituyen los criterios físicos de validez.
- No se estimó una incertidumbre instrumental porque el archivo no incluye
  réplicas, errores de medición ni especificaciones metrológicas.

= Conclusiones

// La conclusión conserva una cifra decimal, salvo Allende-100, cuyo valor bajo
// necesita dos decimales para no perder información relevante por redondeo.
La zeolita Y y el material 8 % ZrO₂/SBA-15 presentan las áreas superficiales más
altas, con *993,9* y *663,4 m²/g*, respectivamente. La $gamma$-Al₂O₃ muestra un
área mesoporosa intermedia de *251,3 m²/g*, mientras que el óxido de grafeno alcanza
*116,0 m²/g*. Allende-100 posee un área accesible muy baja, de aproximadamente
*1,23 m²/g*.

Para fortalecer el resultado de la zeolita Y se recomienda repetir o ampliar la
medición con más puntos a baja presión relativa. También se recomienda confirmar
que el experimento se realizó con nitrógeno a 77 K y documentar el protocolo de
desgasificación antes de usar estas cifras en una publicación o comparación formal.

= Reproducibilidad

// El comando siguiente reconstruye los cálculos con las dependencias fijadas por
// `uv.lock`; el formato Typst se comprueba por separado con el verificador.
El cálculo se ejecutó de manera reproducible con `uv`. El archivo de análisis es
`analyze_isotherms.py` y el libro detallado, que contiene los datos, ajustes y
gráficas, es `BET_surface_area_analysis.xlsx`.

#block(
  width: 100%,
  fill: gris-claro,
  radius: 3pt,
  inset: 8pt,
)[
  `uv run python analyze_isotherms.py datos/Isotermas.xlsx`
]

= Referencias metodológicas

// Las referencias son deliberadamente primarias: una norma internacional, el
// informe técnico de IUPAC y el artículo que formalizó la selección BETSI.

1. *ISO 9277:2022.* Determinación del área superficial específica de sólidos por
  adsorción de gases mediante el método BET.
  #link("https://www.iso.org/standard/71014.html")[Sitio oficial de ISO].
2. Thommes, M. y colaboradores (2015). _Physisorption of gases, with special
  reference to the evaluation of surface area and pore size distribution_.
  Informe técnico IUPAC. #link("https://doi.org/10.1515/pac-2014-1117")[DOI].
3. Osterrieth, J. W. M. y colaboradores (2022). _How reproducible are surface
  areas calculated from the BET equation?_ Advanced Materials, 34, 2201502.
  #link("https://doi.org/10.1002/adma.202201502")[DOI].
