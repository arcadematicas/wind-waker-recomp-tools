#!/usr/bin/env bash
# Build a patched ISO: your USA disc + the text of your PAL disc.
#
#   scripts/hacer-iso-es.sh                          # discs in discos/, Spanish
#   scripts/hacer-iso-es.sh USA.iso PAL.iso OUT.iso  # explicit, Spanish
#   LANGUAGE=fr scripts/hacer-iso-es.sh              # French
#
# See tools/windwaker_pal_text.py for what this can and cannot do
# (French / Spanish / Italian work; German needs a full ISO rebuild).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOL="$ROOT/tools/windwaker_pal_text.py"
LANGUAGE="${LANGUAGE:-es}"

if [ ! -f "$TOOL" ]; then
  echo "missing $TOOL" >&2
  exit 1
fi

if [ $# -eq 3 ]; then
  USA="$1"; PAL="$2"; OUT="$3"
else
  USA="$ROOT/discos/WindWaker-USA.iso"
  OUT="$ROOT/discos/WindWaker-${LANGUAGE^^}.iso"
  PAL="$(find "$ROOT/discos" -maxdepth 3 -iname '*.iso' \
          ! -iname 'WindWaker-USA.iso' ! -iname 'WindWaker-??.iso' | head -1)"
  if [ -z "$PAL" ]; then
    echo "No PAL disc found under $ROOT/discos (expected the (Europe) (En,Fr,De,Es,It) one)." >&2
    exit 1
  fi
fi

for f in "$USA" "$PAL"; do
  [ -f "$f" ] || { echo "no such file: $f" >&2; exit 1; }
done

echo "USA      : $USA"
echo "PAL      : $PAL"
echo "OUTPUT   : $OUT"
echo "LANGUAGE : $LANGUAGE"
echo

exec python3 "$TOOL" "$USA" "$PAL" "$OUT" --language "$LANGUAGE"
