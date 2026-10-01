#!/usr/bin/env bash
# Lanzador de Wind Waker Recomp sobre Proton (Linux).
# Alfred, 01/10/2026.
#
# Por defecto usa el ISO EN ESPANOL (discos/WindWaker-ES.iso): disco USA (GZLE01 rev 0,
# con su main.dol intacto) + el texto/dialogo espanol del disco PAL (GZLP01) injertado.
#
#   - Disco USA original:  WINDWAKER_DISC="$ROOT/discos/WindWaker-USA.iso" lanzar-windwaker.sh
#   - Opciones al juego:   lanzar-windwaker.sh --64hz   (se pasan tal cual)
#
# Saves, ajustes y logs:
#   ~/Games/umu/umu-windwaker/drive_c/users/steamuser/AppData/Roaming/BlueWake/
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export GAMEID=umu-windwaker
export PROTONPATH="${PROTONPATH:-/usr/share/steam/compatibilitytools.d/proton-cachyos-native}"
export UMU_RUNTIME_UPDATE=0
export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-pipewire,pulseaudio,alsa}"

DISC="${WINDWAKER_DISC:-$ROOT/discos/WindWaker-ES.iso}"
APPDIR="$ROOT/app/WindWakerRecomp"

if [ ! -f "$DISC" ]; then
  echo "Falta el disco: $DISC" >&2
  echo "  - el ISO espanol se crea con:  scripts/hacer-iso-es.sh" >&2
  echo "  - o apunta a otro con WINDWAKER_DISC=..." >&2
  exit 1
fi
if [ ! -f "$APPDIR/BlueWake.exe" ]; then
  echo "Falta la app en $APPDIR (usa scripts/actualizar.sh para bajarla)." >&2
  exit 1
fi

cd "$APPDIR"
exec umu-run ./BlueWake.exe --disc "$DISC" "$@"
