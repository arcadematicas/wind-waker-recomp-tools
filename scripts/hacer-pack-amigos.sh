#!/usr/bin/env bash
# Prepara la carpeta que se comparte con los amigos.
#
#   scripts/hacer-pack-amigos.sh [carpeta-destino]
#
# IMPORTANTE - que entra y que NO:
#   SI  -> la app oficial (zip publico del proyecto) + los scripts + las instrucciones.
#   NO  -> el disco del juego (.iso/.rvz/.gcm) ni ficheros extraidos de el.
#   NO  -> el pack de texturas HD (es de terceros, no se redistribuye).
# Cada amigo pone su propio disco GZLE01 (USA) revision 0, y si quiere espanol,
# tambien su disco GZLP01 (PAL).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$ROOT/pack-amigos}"
NAME="WindWaker-Recomp-pack"

VERSION="$(cat "$ROOT/app/.version" 2>/dev/null || echo "desconocida")"
ZIP="$(ls -t "$ROOT"/releases/*.zip 2>/dev/null | grep -Ei 'windows-x64|WWR' | head -1 || true)"

echo "== version: $VERSION =="
if [ -z "$ZIP" ]; then
  echo "No hay zip en releases/. Ejecuta antes: scripts/actualizar.sh" >&2
  exit 1
fi

rm -rf "$DEST"; mkdir -p "$DEST/tools" "$DEST/scripts"

echo "== copiando la app oficial (sin modificar) =="
cp -v "$ZIP" "$DEST/"

echo "== copiando herramientas e instrucciones =="
cp -v "$ROOT/tools/hacer-iso-es.py" "$DEST/tools/"
cp -v "$ROOT/scripts/hacer-iso-es.sh" "$DEST/scripts/"
cp -v "$ROOT/scripts/lanzar-windwaker.sh" "$DEST/scripts/"
cp -v "$ROOT/docs/LEEME-AMIGOS.txt" "$DEST/LEEME-AMIGOS.txt"

echo
echo "== comprobacion de seguridad: que NO haya datos del juego =="
BAD=$(find "$DEST" -iname '*.iso' -o -iname '*.rvz' -o -iname '*.gcm' -o -iname '*.wia' -o -iname '*.gcz' -o -iname '*.dds' -o -iname 'tex1_*' 2>/dev/null | head)
if [ -n "$BAD" ]; then
  echo "!! ABORTANDO: hay ficheros que no se pueden compartir:" >&2
  echo "$BAD" >&2
  exit 1
fi
echo "   limpio (ni discos ni texturas)"

echo
echo "== empaquetando =="
OUT="$ROOT/${NAME}-${VERSION}.zip"
rm -f "$OUT"
( cd "$(dirname "$DEST")" && zip -qr "$OUT" "$(basename "$DEST")" )
echo
ls -lh "$OUT"
echo
echo "Listo. Ese zip es lo unico que se comparte."
