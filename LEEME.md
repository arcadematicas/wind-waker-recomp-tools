# Wind Waker Recomp en Linux — EN ESPAÑOL + HD (proyecto de Alfred, 01/10/2026)

**Estado: FUNCIONANDO.** Recompilación nativa de *The Wind Waker* (GameCube) en CachyOS sobre
**Proton**, a 60 fps, con **texto/diálogo en español**, **pack de texturas HD** y **dos packs
listos para usar**.

---

## Uso rápido

```bash
scripts/lanzar-windwaker.sh          # juega (ISO español + HD, por defecto)
scripts/actualizar.sh --check        # ¿hay versión nueva de la app?
scripts/actualizar.sh                # instala la última release
scripts/hacer-iso-es.sh              # rehace el ISO español desde los dos discos
scripts/hacer-pack-amigos.sh         # pack para COMPARTIR   (166 MB, sin juego)
scripts/hacer-pack-completo.sh       # pack AUTOCONTENIDO    (1,3 GB, con juego)
```
Acceso directo en el menú KDE: **"Wind Waker Recomp (Proton)"**.
Disco USA original: `WINDWAKER_DISC=…/discos/WindWaker-USA.iso scripts/lanzar-windwaker.sh`

---

## Los dos packs

| Pack | Tamaño | Contenido | ¿Para quién? |
|---|---|---|---|
| **`WindWaker-Recomp-pack-v0.2.2.zip`** | **166 MB** | App oficial + scripts + `LEEME-AMIGOS.txt` | **Amigos.** Cada uno pone su propio disco |
| **`WindWaker-Recomp-COMPLETO-v0.2.2.7z`** | **1,3 GB** | App + **juego** + texturas HD + ajustes + save | **Solo tuyo** (backup / otro PC) |

### El pack COMPLETO (autocontenido)

```
pack-completo/
  app/WindWakerRecomp/        el programa
  discos/WindWaker-ES.iso     el juego en español
  datos/                      ajustes, saves y TEXTURAS HD (3.737)
  Lanzar Wind Waker.bat       ← doble clic en Windows
  lanzar-windwaker.sh         ← en Linux (Proton)
  LEEME.txt
```
- Es **portátil de verdad**: usa la variable **`BLUEWAKE_DATA_DIR`** de la app para que todo lo del
  jugador viva en `datos/` (en vez de `%APPDATA%\BlueWake`). Así no toca el sistema y **arranca
  sin pedir nada**: ya viene con 16:9, Better Wind Waker, Smooth Motion 60, HD y el save.
- **Verificado**: arrancado desde el propio pack → `prepared in …\pack-completo\datos\game`,
  `texture-pack=…\datos\Load\Textures\GZLE01 replacements=3733`, `rate=59.9 hitches=0`.
- ⚠️ **Incluye el disco del juego y texturas de terceros: NO se comparte.** Es tu copia personal
  (backup o llevarlo a otro PC).

### ⚠️ Por qué el pack completo no se puede dar a nadie

- El **disco** es material con derechos de autor → nunca se redistribuye.
- El **pack de texturas HD es de terceros** → tampoco.
- La **app sí** (su modelo de release es ese: la app con el código recompilado y el jugador aporta
  su disco; GPL-3.0 y publicada).

`hacer-pack-amigos.sh` **aborta** si detecta un disco o una textura dentro del pack que genera.

---

## Estructura del proyecto

| Ruta | Qué | ¿Se comparte? |
|---|---|---|
| `app/WindWakerRecomp/` + `app/.version` | La app (release oficial) | ✅ |
| `discos/WindWaker-USA.iso` | Disco USA (GZLE01 rev 0) | ❌ |
| `discos/WindWaker-ES.iso` | **El ISO en español** | ❌ |
| `discos/PAL/…(En,Fr,De,Es,It).iso` | Disco PAL (GZLP01), fuente del español | ❌ |
| `discos/extraido/` | Árboles extraídos | ❌ |
| `releases/` | Zips oficiales | ✅ |
| `scripts/`, `tools/`, `docs/` | Utilidades e instrucciones | ✅ |
| `pack-amigos/`, `pack-completo/` | Packs generados | según el pack |
| `logs/` | Registros | — |
| Texturas HD (origen) | `…/AppData/Roaming/BlueWake/Load/Textures/GZLE01` | ❌ |
| Saves / ajustes del juego | `…/AppData/Roaming/BlueWake/` (en el prefijo) | ❌ |

Git local en el PC; `.gitignore` deja fuera discos, app, releases, packs y logs.

---

## Cómo está montado (reproducible)

1. **App**: release oficial Windows x64 v0.2.2 → `app/`. En Linux se ejecuta con **umu-launcher** +
   **Proton** (probado con `proton-cachyos-native`). El lanzador **busca el Proton solo**
   (acepta solo carpetas con `toolmanifest.vdf`) y, si no encuentra ninguno, deja que umu se
   descargue el suyo; se puede forzar con `PROTONPATH=/ruta/a/Proton lanzar-windwaker.sh`.
   - ⚠️ El recomp **no acepta `.rvz` por `--disc`** (su README dice que sí): hay que darle `.iso`/`.gcm`.
2. **Discos**: el `.rvz` de Batocera → `.iso` con `dolphin-tool convert -f iso`.
3. **Español**: `bmgres.arc` del PAL `res/Msg/data3/` injertado en el hueco del USA
   (ver detalle abajo).
4. **Texturas HD**: pack de Dolphin (3.737 DDS) en `<datos>/Load/Textures/GZLE01` + `hd_textures=1`
   en `settings.ini`. **Ojo: el `settings.ini` es Windows con CRLF.**

## El injerto del español

- El disco PAL trae los textos por idioma en `res/Msg/data0…data4`
  (**data0=En, data1=De, data2=Fr, data3=ESPAÑOL, data4=It**), en ASCII claro.
- `bmgres.arc` (diálogo/textos) es el mismo fichero y estructura en ambas versiones; el español
  pesa menos (539.136 B) que el americano (640.672 B) → cabe en su hueco.
- Se localiza por firma y se sobrescribe in-place rellenando con ceros. **`main.dol` y el FST
  intactos** → el recomp lo sigue aceptando como **GZLE01 rev 0**.
- `tools/hacer-iso-es.py` lo automatiza.

**Traducido**: diálogo y textos (8.732 líneas: "Isla del…" ×141, "Espada" ×82, "Escudo" ×20).
**No traducido**: menús y carteles de interfaz (`itemres`, `nameres`, `menures`…), que en el PAL
son multi-idioma y mayores → haría falta reconstruir el ISO (FST nuevo) y elegir idioma.

## Verificado (01/10/2026)

- Intro y textos **en español** ("El pueblo, indefenso ante ese enorme poder, sólo podía rezar…").
- `shown=59.9 game=30.0`, `hitches=0`; AMD RX 6700 XT (D3D12 vía vkd3d-proton).
- HD: `Loaded 3733 texture replacement registrations`, reemplazos 376x104 → 752x208.
- Pack completo arrancado desde sí mismo usando su `datos/` ✅.

## Pendientes

1. Probar a fondo mando y sonido.
2. **Español completo** (menús y objetos): reconstrucción del ISO + elección de idioma.
3. **Port nativo a Linux/ARM** (viable: capa POSIX, SDL3 e Dawn con Vulkan ya presentes).
4. Decidir si el repo local se sube a GitHub (`arcadematicas`).
5. Contar en el issue #3 que funciona por Proton.

---

## 🌍 PUBLICADO: herramienta multi-idioma + respuestas al creador (01/10/2026)

**Repo público**: https://github.com/arcadematicas/wind-waker-recomp-tools

- **`tools/windwaker_pal_text.py`** (568 líneas, Python 3 **solo stdlib**, sin dolphin-tool) —
  injerta el texto de CUALQUIER idioma del PAL en el disco USA:
  ```bash
  python3 tools/windwaker_pal_text.py USA.iso PAL.iso OUT.iso --language es
  python3 tools/windwaker_pal_text.py --list --disc "MI.iso"     # solo lectura
  ```
  Idiomas: `es` (por defecto), `fr`, `it` → caben. `de` → **no cabe** (24.064 B de más) y aborta
  antes de escribir nada, explicando que necesitaría reconstruir el ISO.
  Detecta solo los 5 archivos de diálogo del PAL y su idioma (normaliza acentos), e imprime una
  muestra de texto de cada uno para que se compruebe a ojo.
  **Validado**: la salida en `es` es **byte a byte idéntica** al ISO que ya funcionaba
  (`cmp` → IDENTICOS) y los discos de entrada quedan intactos (sha256 sin cambios).
- **Comentarios publicados en el repo del creador** (usuario `arcadematicas`):
  - Issue **#7** (*Wind waker Europe support*) → https://github.com/elliotttate/Wind-Waker-Recomp/issues/7#issuecomment-5929059380
    Explica la técnica, la tabla de tamaños, qué idiomas caben, que los menús siguen en inglés,
    el caso del alemán, y ofrece la herramienta + un PR.
  - Issue **#3** (*Linux Support*) → https://github.com/elliotttate/Wind-Waker-Recomp/issues/3#issuecomment-5929059857
    Confirma que va por Proton con el comando exacto, avisa de que `--disc` no acepta `.rvz`,
    y documenta el truco de `BLUEWAKE_DATA_DIR` y el detalle de las texturas en `GZLE01`.
- El repo público lleva README (inglés + sección en español), licencia GPL-3.0 y los scripts.
  **No contiene datos del juego.** `.gitignore` fuera discos, app, releases, packs y logs.
- Los commits se reescribieron con la identidad de GitHub (`arcadematicas`).
