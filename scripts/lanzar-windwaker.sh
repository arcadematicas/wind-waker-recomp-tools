#!/usr/bin/env bash
# Lanzador de Wind Waker Recomp sobre Proton (Linux).
# Alfred, 01/10/2026.
#
# Por defecto usa el ISO EN ESPANOL (discos/WindWaker-ES.iso): disco USA (GZLE01 rev 0,
# con su main.dol intacto) + el texto/dialogo espanol del disco PAL (GZLP01) injertado.
#
#   - Disco USA original:  WINDWAKER_DISC="$ROOT/discos/WindWaker-USA.iso" lanzar-windwaker.sh
#   - Opciones al juego:   lanzar-windwaker.sh --64hz   (se pasan tal cual)
#   - Forzar un Proton:    PROTONPATH=/ruta/a/Proton lanzar-windwaker.sh
#
# Saves, ajustes y logs:
#   ~/Games/umu/umu-windwaker/drive_c/users/steamuser/AppData/Roaming/BlueWake/
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ---------------------------------------------------------------------------
# EL PROTON NO SE DA POR HECHO: SE BUSCA  (arreglado 01/10/2026)
# ---------------------------------------------------------------------------
# Antes esto era una sola linea:
#   export PROTONPATH="${PROTONPATH:-/usr/share/steam/compatibilitytools.d/proton-cachyos-native}"
# ...o sea, la ruta del Proton de UNA maquina concreta. En cualquier otro equipo umu
# revienta con un traceback de Python:
#   FileNotFoundError: PROTONPATH '...' is not valid, toolmanifest.vdf not found
#
# Ahora: 1) si el usuario trae PROTONPATH, se respeta (validandolo antes), 2) si no, se
# busca un Proton instalado, y 3) si no hay ninguno, NO se pone PROTONPATH y umu se
# descarga el suyo (UMU-Proton), que es lo mas portable para quien no tenga Steam.

# Un directorio es un Proton de verdad si lleva toolmanifest.vdf dentro: es exactamente
# el fichero cuya ausencia provocaba el error de arriba.
es_proton() {
    [ -n "${1:-}" ] && [ -f "$1/toolmanifest.vdf" ]
}

# Donde suele haber Proton: Steam del sistema, del usuario y Flatpak.
PROTON_DIRS=(
    "$HOME/.steam/root/compatibilitytools.d"
    "$HOME/.local/share/Steam/compatibilitytools.d"
    "/usr/share/steam/compatibilitytools.d"
    "$HOME/.var/app/com.valvesoftware.Steam/data/Steam/compatibilitytools.d"
    "$HOME/.steam/steam/steamapps/common"
    "$HOME/.local/share/Steam/steamapps/common"
    "/usr/share/steam/steamapps/common"
    "$HOME/.var/app/com.valvesoftware.Steam/data/Steam/steamapps/common"
)

# Busca Proton por ORDEN DE PREFERENCIA DEL NOMBRE, mirando todas las carpetas en cada vuelta.
# OJO CON EL ORDEN: primero el nombre, y solo despues la carpeta. Si se recorrieran las carpetas
# primero (como en el primer intento), en el PC de Fransis ganaria el GE-Proton que tiene en
# ~/.steam/root/ y le cambiariamos el Proton que ya le iba a 60 fps.
buscar_proton() {
    local patron dir c
    for patron in 'proton-cachyos-native' 'proton-cachyos' 'GE-Proton*' 'Proton*' '*'; do
        for dir in "${PROTON_DIRS[@]}"; do
            [ -d "$dir" ] || continue
            while IFS= read -r c; do
                [ -n "$c" ] || continue
                c="${c%/}"
                if es_proton "$c"; then printf '%s' "$c"; return 0; fi
            done < <(find "$dir" -maxdepth 1 -mindepth 1 -type d -name "$patron" 2>/dev/null | sort -V -r)
        done
    done
    return 1
}

if [ -n "${PROTONPATH:-}" ]; then
    if ! es_proton "$PROTONPATH"; then
        echo "ERROR: PROTONPATH=$PROTONPATH no parece un Proton (no tiene toolmanifest.vdf)." >&2
        echo "  - quita la variable y se detectara solo, o" >&2
        echo "  - apunta a la carpeta que contiene toolmanifest.vdf." >&2
        exit 1
    fi
    echo "Proton: $PROTONPATH (forzado con PROTONPATH)"
elif PROTON_DETECTADO="$(buscar_proton)"; then
    export PROTONPATH="$PROTON_DETECTADO"
    echo "Proton: $PROTONPATH"
else
    unset PROTONPATH 2>/dev/null || true
    echo "Proton: (ninguno instalado: umu se descargara el suyo, UMU-Proton)"
    echo "        si prefieres usar uno tuyo:  PROTONPATH=/ruta/a/Proton $0"
fi

export GAMEID=umu-windwaker
# 0 = umu no toca su runtime. Era necesario con el umu que trae WProton (le falta la clave
# 'steamrt4-arm64' en su runtime y se cae en cada arranque); con el umu normal de la
# distribucion es inofensivo. Si algun dia hace falta que se actualice:
#   UMU_RUNTIME_UPDATE=1 lanzar-windwaker.sh
export UMU_RUNTIME_UPDATE="${UMU_RUNTIME_UPDATE:-0}"
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
