#!/usr/bin/env bash
# Crea el pack AUTOCONTENIDO: app + juego (ISO español) + texturas HD + ajustes + saves,
# todo en una carpeta que arranca sin configurar nada.
#
#   scripts/hacer-pack-completo.sh
#
# ⚠️ ESTE PACK INCLUYE EL DISCO DEL JUEGO Y LAS TEXTURAS DE TERCEROS:
#    es para USO PROPIO (backup, llevarlo a otro PC). NO se comparte.
#    Para compartir con amigos usa scripts/hacer-pack-amigos.sh (166 MB, sin juego).
#
# Usa la variable BLUEWAKE_DATA_DIR de la app para que todo lo del jugador viva en
# "datos/" dentro del propio pack (no en %APPDATA%), asi es portable.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(cat "$ROOT/app/.version" 2>/dev/null || echo "desconocida")"
DEST="$ROOT/pack-completo"
APP_SRC="$ROOT/app/WindWakerRecomp"
DATA_SRC="${WINDWAKER_DATA:-$HOME/Games/umu/umu-windwaker/drive_c/users/steamuser/AppData/Roaming/BlueWake}"
TEX_SRC="$DATA_SRC/Load/Textures/GZLE01"
ISO_SRC="$ROOT/discos/WindWaker-ES.iso"

for f in "$APP_SRC/BlueWake.exe" "$ISO_SRC"; do
  [ -e "$f" ] || { echo "falta: $f" >&2; exit 1; }
done

echo "== limpiando =="
rm -rf "$DEST"
mkdir -p "$DEST/app" "$DEST/datos/Load/Textures" "$DEST/discos"

echo "== app =="
cp -r "$APP_SRC" "$DEST/app/WindWakerRecomp"

echo "== disco (enlace duro: no ocupa el doble) =="
cp -l "$ISO_SRC" "$DEST/discos/WindWaker-ES.iso" 2>/dev/null || cp "$ISO_SRC" "$DEST/discos/WindWaker-ES.iso"

echo "== texturas HD =="
if [ -d "$TEX_SRC" ] && [ -n "$(ls -A "$TEX_SRC" 2>/dev/null)" ]; then
  cp -al "$TEX_SRC" "$DEST/datos/Load/Textures/GZLE01" 2>/dev/null || cp -r "$TEX_SRC" "$DEST/datos/Load/Textures/GZLE01"
else
  echo "   (aviso: no hay pack de texturas en $TEX_SRC)"
fi

echo "== ajustes (limpios: sin posicion de ventana) =="
python3 - "$DATA_SRC/settings.ini" "$DEST/datos/settings.ini" <<'PY'
import re, sys
src, dst = sys.argv[1], sys.argv[2]
out = []
try:
    lines = open(src, "rb").read().decode("utf-8", "replace").splitlines()
except OSError:
    lines = []
for l in lines:
    k = l.split("=", 1)[0].strip()
    if k in ("window", "window_position"):
        continue
    out.append(l)
if not any(x.startswith("hd_textures=") for x in out):
    out.append("hd_textures=1")
if not any(x.startswith("betterww=") for x in out):
    out.append("betterww=1")
open(dst, "w", newline="\r\n").write("\n".join(out) + "\n")
print("   %d lineas" % len(out))
PY

echo "== saves (tarjeta de memoria) =="
[ -f "$DATA_SRC/GZLE01.card" ] && cp "$DATA_SRC/GZLE01.card" "$DEST/datos/GZLE01.card" && echo "   copiada"

echo "== lanzadores =="
cat > "$DEST/Lanzar Wind Waker.bat" <<'BAT'
@echo off
rem Wind Waker Recomp - arranque portable. Todo vive en esta carpeta.
setlocal
set "ROOT=%~dp0"
set "BLUEWAKE_DATA_DIR=%ROOT%datos"
cd /d "%ROOT%app\WindWakerRecomp"
start "" "BlueWake.exe" --disc "%ROOT%discos\WindWaker-ES.iso"
BAT

cat > "$DEST/lanzar-windwaker.sh" <<'SH'
#!/usr/bin/env bash
# Arranque portable en Linux (Proton). El exe es de Windows: se le da la ruta
# de datos en formato Windows (Z: = raiz del sistema).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export GAMEID=umu-windwaker
export PROTONPATH="${PROTONPATH:-/usr/share/steam/compatibilitytools.d/proton-cachyos-native}"
export UMU_RUNTIME_UPDATE=0
export BLUEWAKE_DATA_DIR="Z:$(printf '%s' "$ROOT/datos" | tr '/' '\\')"
cd "$ROOT/app/WindWakerRecomp"
exec umu-run ./BlueWake.exe --disc "$ROOT/discos/WindWaker-ES.iso" "$@"
SH
chmod +x "$DEST/lanzar-windwaker.sh"

echo "== LEEME =="
cat > "$DEST/LEEME.txt" <<'TXT'
=========================================================
 Wind Waker Recomp - PACK COMPLETO (todo montado)
=========================================================

Este pack YA ESTA LISTO. No hay que configurar nada.

COMO JUGAR
----------
  Windows:  doble clic en "Lanzar Wind Waker.bat"
  Linux:    ./lanzar-windwaker.sh   (necesita umu-launcher + Proton)

El juego arranca en ESPANOL, con el pack de texturas HD activado y los
ajustes ya puestos (16:9, Better Wind Waker, Smooth Motion a 60 fps).

QUE HAY DENTRO
--------------
  app/WindWakerRecomp/     el programa (recompilacion nativa de Wind Waker)
  discos/WindWaker-ES.iso  el juego: disco USA con el texto espanol injertado
  datos/                   ajustes, saves, partida y texturas HD
  datos/Load/Textures/GZLE01   las 3.737 texturas HD

Todo es portable: la carpeta "datos" se usa en lugar de %APPDATA%.

CONTROLES
---------
  F1 ajustes   F5 guardar estado   F8 cargar el ultimo   F11 pantalla completa
  Teclado: WASD mover, J/K/U/I botones, E/R/Q gatillos, Enter START

AVISO IMPORTANTE
----------------
  Este pack INCLUYE EL DISCO DEL JUEGO. Es para tu uso personal
  (backup, o llevartelo a otro PC). NO LO COMPARTAS NI LO SUBAS a
  ningun sitio: el disco es material con derechos de autor y las
  texturas HD son de terceros.

  Si quieres pasarle el juego a un amigo, dale el pack ligero
  (WindWaker-Recomp-pack-*.zip, 166 MB): lleva el programa y las
  instrucciones, y cada uno pone su propio disco.

  Si te pide el disco y no arranca: comprueba que existe
  discos/WindWaker-ES.iso, o pasa otro con --disc.
TXT

echo
echo "== resultado =="
ls -la "$DEST"
echo
du -sh "$DEST"/* 2>/dev/null
echo "--- total ---"; du -sh "$DEST"

echo
echo "== empaquetando en 7z (comprime bastante mas que zip) =="
OUT="$ROOT/WindWaker-Recomp-COMPLETO-${VERSION}.7z"
rm -f "$OUT"
( cd "$ROOT" && 7z a -mx=6 -bso0 -bsp0 "$OUT" pack-completo >/dev/null )
ls -lh "$OUT"
