#!/usr/bin/env bash
# Crea discos/WindWaker-ES.iso (USA GZLE01 con el texto espanol del PAL GZLP01).
#
#   scripts/hacer-iso-es.sh                       # usa los discos de discos/
#   scripts/hacer-iso-es.sh USA.iso PAL.iso OUT.iso
#
# Necesita dolphin-tool (paquete dolphin-emu) en el PATH.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v dolphin-tool >/dev/null || { echo "falta dolphin-tool (instala dolphin-emu)" >&2; exit 1; }

if [ $# -eq 3 ]; then
  USA="$1"; PAL="$2"; OUT="$3"
else
  USA="$ROOT/discos/WindWaker-USA.iso"
  OUT="$ROOT/discos/WindWaker-ES.iso"
  PAL="$(find "$ROOT/discos" -maxdepth 3 -iname '*.iso' ! -iname 'WindWaker-USA.iso' ! -iname 'WindWaker-ES.iso' | head -1)"
  if [ -z "$PAL" ]; then
    echo "No encuentro el ISO PAL en $ROOT/discos (que sea el (Europe) (En,Fr,De,Es,It))" >&2
    exit 1
  fi
fi

for f in "$USA" "$PAL"; do
  [ -f "$f" ] || { echo "no existe: $f" >&2; exit 1; }
done

echo "USA : $USA"
echo "PAL : $PAL"
echo "SALIDA: $OUT"
echo

echo "== comprobando las cabeceras de los discos =="
echo "--- USA"; dolphin-tool header -i "$USA" | grep -E 'Game ID|Revision|Country'
echo "--- PAL"; dolphin-tool header -i "$PAL" | grep -E 'Game ID|Revision|Country'
echo

exec python3 "$ROOT/tools/hacer-iso-es.py" "$USA" "$PAL" "$OUT"
