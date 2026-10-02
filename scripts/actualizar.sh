#!/usr/bin/env bash
# Actualiza la app de Wind Waker Recomp a la ultima release de GitHub.
#
#   scripts/actualizar.sh            # comprueba e instala si hay version nueva
#   scripts/actualizar.sh --check    # solo informa
#
# NO toca los discos (el ISO espanol sigue valido entre versiones: la app solo lo lee).
# La version instalada se guarda en app/.version.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO=elliotttate/Wind-Waker-Recomp
APP="$ROOT/app/WindWakerRecomp"
VERSION_FILE="$ROOT/app/.version"
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

command -v curl >/dev/null || { echo "falta curl" >&2; exit 1; }
command -v python3 >/dev/null || { echo "falta python3" >&2; exit 1; }

echo "== consultando la ultima release de $REPO =="
JSON="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest")"
TAG="$(printf '%s' "$JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')"
# El nombre del asset importa: el fichero .sha256 de GitHub contiene "<hash>  <nombre-del-asset>",
# y `sha256sum -c` busca ESE nombre en el directorio. Si guardamos el zip con otro nombre
# (p. ej. "v0.3.0-windows-x64.zip"), la verificacion falla y parece que la descarga esta mal.
ASSET="$(printf '%s' "$JSON" | python3 -c '
import json,sys
d=json.load(sys.stdin)
for a in d["assets"]:
    if "windows-x64" in a["name"] and a["name"].endswith(".zip"):
        print(a["name"]); break
')"
URL="$(printf '%s' "$JSON" | python3 -c '
import json,sys
d=json.load(sys.stdin)
for a in d["assets"]:
    if "windows-x64" in a["name"] and a["name"].endswith(".zip"):
        print(a["browser_download_url"]); break
')"
URLSUM="${URL}.sha256"
INSTALLED="$(cat "$VERSION_FILE" 2>/dev/null || echo "(desconocida)")"

echo "   instalada: $INSTALLED"
echo "   ultima   : $TAG"
if [ "$TAG" = "$INSTALLED" ]; then
  echo "== ya esta al dia =="
  exit 0
fi
if [ "$CHECK_ONLY" = 1 ]; then
  echo "== hay version nueva: $TAG (usa sin --check para instalarla) =="
  exit 0
fi

mkdir -p "$ROOT/releases"
ZIP="$ROOT/releases/$ASSET"
echo "== descargando $TAG =="
curl -fL --retry 3 -o "$ZIP" "$URL"
echo "== verificando sha256 =="
curl -fsSL -o "$ZIP.sha256" "$URLSUM" || true
if [ -s "$ZIP.sha256" ]; then
  ( cd "$(dirname "$ZIP")" && sha256sum -c "$(basename "$ZIP").sha256" ) || { echo "sha256 NO coincide" >&2; exit 1; }
fi

echo "== extrayendo =="
NEW="$ROOT/app.new"
rm -rf "$NEW"; mkdir -p "$NEW"
unzip -q -o "$ZIP" -d "$NEW"

if [ -d "$APP" ]; then
  BAK="$ROOT/app.bak-$(date +%Y%m%d-%H%M%S)"
  echo "== guardando la version anterior en $(basename "$BAK") =="
  mv "$APP" "$BAK"
fi
mv "$NEW/WindWakerRecomp" "$APP" 2>/dev/null || mv "$NEW"/* "$APP"
rmdir "$NEW" 2>/dev/null || true
printf '%s\n' "$TAG" > "$VERSION_FILE"

# el nuevo lanzador tambien en el sitio viejo, por compatibilidad
[ -f "$ROOT/lanzar-windwaker.sh" ] || true

echo "== listo: $TAG instalado =="
ls "$APP" | head
echo
echo "Prueba con:  scripts/lanzar-windwaker.sh"
