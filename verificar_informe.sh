#!/usr/bin/env bash

# Verificación reproducible del informe Typst.
#
# 1. Typstyle actúa como comprobador de formato y legibilidad del archivo fuente.
# 2. Typst compila el documento y detecta errores de sintaxis o composición.
#
# El binario local de Typstyle está fijado en la versión 0.15.1 dentro de `.tools`.

set -euo pipefail

directorio_proyecto="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$directorio_proyecto"

archivo_fuente="Informe_area_superficial_BET.typ"
archivo_pdf="Informe_area_superficial_BET.pdf"
typstyle_local=".tools/bin/typstyle"

if [[ ! -x "$typstyle_local" ]]; then
  echo "No se encontró Typstyle en $typstyle_local." >&2
  echo "Instálelo con: cargo install typstyle --version 0.15.1 --locked --root .tools" >&2
  exit 1
fi

echo "Comprobando el formato del archivo Typst..."
"$typstyle_local" --line-width 100 --indent-width 2 --check "$archivo_fuente"

echo "Compilando el informe..."
typst compile "$archivo_fuente" "$archivo_pdf"

echo "Verificación completada: $archivo_pdf"
