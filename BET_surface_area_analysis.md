# Análisis de área superficial BET

Fuente: `datos/Isotermas.xlsx`

> Suposición: adsorción de N2 a 77 K, sección molecular de 0,162 nm2 y 22 414 cm3/mol en STP. El libro fuente no especifica gas ni temperatura.

| Material | Área BET (m2/g) | Ajuste P/P0 | n | R2 | C | Error C4 (%) |
|---|---:|---:|---:|---:|---:|---:|
| Oxido de grafeno | 116.0 | 0.0497-0.301 | 6 | 0.999937 | 121.1 | 3.38 |
| γ-Al2O3 | 251.3 | 0.029456-0.6699 | 22 | 0.999771 | 70.5 | 1.73 |
| Allende-100 | 1.2 | 0.018037-0.24772 | 11 | 0.999781 | 63.2 | 0.27 |
| Zeolita Y (Si/Al =15) | 993.9 | 0.0097903-0.060776 | 3 | 0.999991 | 1986.9 | 4.33 |
| 8%ZrO2/SBA-15 | 663.4 | 0.06278-0.20012 | 8 | 0.999948 | 116.1 | 0.92 |

## Interpretación

- **Oxido de grafeno:** Captación intensa a P/P0 muy baja e histéresis amplia a presión alta; los datos sugieren contribuciones combinadas de micro- y mesoporos.
- **γ-Al2O3:** Perfil mesoporoso semejante al tipo IV, con histéresis amplia a P/P0 intermedia y alta.
- **Allende-100:** Adsorción y área específica muy bajas; la mayor captación ocurre cerca de la saturación.
- **Zeolita Y (Si/Al =15):** Perfil microporoso semejante al tipo I: captación alta a baja presión seguida de una meseta. Solo tres puntos satisfacen los criterios BET; el valor es sensible al muestreo.
- **8%ZrO2/SBA-15:** Perfil mesoporoso semejante al tipo IV, con un escalón de condensación capilar cerca de P/P0=0,74-0,78.

## Nota de validación importante

El ajuste convencional 0,05-0,30 de la zeolita Y produce una intersección/C BET negativa e incumple el criterio de crecimiento de V(1-P/P0), por lo que se rechazó. El área informada usa los únicos tres puntos medidos que satisfacen todos los criterios; se recomiendan más puntos a baja presión.
