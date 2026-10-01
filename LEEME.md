# Wind Waker Recomp en Linux — EN ESPAÑOL (proyecto de Alfred, 01/10/2026)

**Estado: FUNCIONANDO.** Recompilación nativa de *The Wind Waker* (GameCube) corriendo en
CachyOS sobre **Proton**, a 60 fps, con **texto/diálogo en español** y **pack de texturas HD**.

---

## Uso rápido

```bash
~/wind-waker-recomp/scripts/lanzar-windwaker.sh          # ISO español + HD (por defecto)
~/wind-waker-recomp/scripts/actualizar.sh --check        # ¿hay versión nueva de la app?
~/wind-waker-recomp/scripts/actualizar.sh                # instala la última release
~/wind-waker-recomp/scripts/hacer-iso-es.sh              # rehace el ISO español
~/wind-waker-recomp/scripts/hacer-pack-amigos.sh         # crea el zip para compartir
```
También hay acceso directo en el menú KDE: **"Wind Waker Recomp (Proton)"**.
Para el disco USA original: `WINDWAKER_DISC=…/discos/WindWaker-USA.iso scripts/lanzar-windwaker.sh`

---

## Estructura del proyecto

| Ruta | Qué | ¿Se comparte? |
|---|---|---|
| `app/WindWakerRecomp/` | La app (release oficial Windows x64) | ✅ (es pública, GPL-3.0) |
| `app/.version` | Versión instalada | ✅ |
| `discos/WindWaker-USA.iso` | Disco USA (GZLE01 rev 0) | ❌ **nunca** |
| `discos/WindWaker-ES.iso` | **El ISO en español** (el que juegas) | ❌ nunca |
| `discos/PAL/…(En,Fr,De,Es,It).iso` | Disco PAL (GZLP01), fuente del español | ❌ nunca |
| `discos/extraido/` | Árboles extraídos (usa / pal / pal-idiomas) | ❌ nunca |
| `releases/` | Zips oficiales descargados | ✅ |
| `scripts/` | lanzar / actualizar / hacer-iso-es / hacer-pack-amigos | ✅ |
| `tools/` | `hacer-iso-es.py`, `find_file.py`, `fst.py`, `patch.py` | ✅ |
| `docs/LEEME-AMIGOS.txt` | Instrucciones para quien recibe el pack | ✅ |
| `logs/` | Registros | — |
| **Pack de texturas HD** | `~/Games/umu/umu-windwaker/…/BlueWake/Load/Textures/GZLE01` | ❌ terceros |
| **Saves / ajustes / logs del juego** | `…/AppData/Roaming/BlueWake/` (en el prefijo) | ❌ |

Git local inicializado (commit `48faabb`); `.gitignore` excluye discos, app, releases y logs.

---

## Compartir con amigos

**`scripts/hacer-pack-amigos.sh`** genera **`WindWaker-Recomp-pack-v0.2.2.zip` = 166 MB**.
Contiene: la app oficial (sin modificar) + scripts + `LEEME-AMIGOS.txt`.
Se comparte eso y **nada más**; el script aborta si detecta un disco o una textura dentro.

**Por qué no se puede (ni se debe) compartir el juego:**

- El disco del juego no se redistribuye: es material con derechos de autor.
  Cada amigo pone **su propio** GZLE01 (USA) revisión 0.
- El **pack de texturas HD es de terceros** → tampoco se redistribuye.
- La **app sí**: su modelo de release es exactamente ese (el código recompilado dentro de la
  app y el jugador aporta el disco). Además es GPL-3.0 y está publicada en GitHub.

**De los 4,7 GB del proyecto, solo hacen falta 166 MB para compartir.** El resto son discos
(4,1 GB) y el pack de texturas (1,2 GB aparte, en el prefijo).

Si algún amigo quiere el **español**, necesita además su propio disco PAL (En,Fr,De,Es,It) y
ejecutar `scripts/hacer-iso-es.sh` — el pack lleva el script y las instrucciones.

---

## Cómo está montado (reproducible)

1. **App**: release oficial Windows x64 v0.2.2 → `app/`. (Requisito: jugar en Windows, o en
   Linux con **umu-launcher** + **Proton** — lo probado.)
   - ⚠️ El recomp **no acepta `.rvz` por `--disc`** (su README dice que sí): hay que darle `.iso`/`.gcm`.
2. **Discos**: el `.rvz` de Batocera → `.iso` con `dolphin-tool convert -f iso`.
3. **Español**: ver abajo.
4. **Texturas HD**: pack de Dolphin copiado a `<datos>/Load/Textures/GZLE01` y `hd_textures=1`
   en `settings.ini`. (3.733 texturas registradas; verificado en el log.)

## El injerto del español

- El disco PAL trae los textos por idioma en `res/Msg/data0…data4`
  (**data0=En, data1=De, data2=Fr, data3=ESPAÑOL, data4=It**), con el texto en ASCII claro.
- `bmgres.arc` (diálogo y textos) es el mismo fichero y estructura en ambas versiones; el
  español pesa menos (539.136 B) que el americano (640.672 B) → cabe en su hueco.
- Se localiza por firma dentro del ISO y se sobrescribe in-place, rellenando con ceros.
  **`main.dol` y el FST intactos** → el recomp lo sigue aceptando como **GZLE01 rev 0**.
- `tools/hacer-iso-es.py` hace todo el proceso (extrae, localiza, injerta y verifica).

**Traducido**: diálogo y textos (8.732 líneas: "Isla del…" ×141, "Espada" ×82, "Escudo" ×20).
**No traducido**: menús y carteles de la interfaz (`itemres`, `nameres`, `menures`…), que en el
PAL son multi-idioma y mayores → haría falta reconstruir el ISO (FST nuevo) y decidir el idioma.

## Verificado (01/10/2026)

- Intro y textos **en español** ("El pueblo, indefenso ante ese enorme poder, sólo podía rezar…").
- `shown=59.9 game=30.0`, `hitches=0`; GPU AMD RX 6700 XT (D3D12 vía vkd3d-proton).
- HD: `Loaded 3733 texture replacement registrations`, reemplazos 376x104 → 752x208, etc.

## Pendientes

1. Probar a fondo mando y sonido (no se puede desde remoto).
2. **Español completo** (menús y objetos): reconstrucción del ISO + elección de idioma.
3. **Port nativo a Linux/ARM**: el port de Windows solo añadió una capa POSIX, SDL3 ya se usa y
   Dawn ya tiene backend Vulkan → es viable pero es un proyecto.
4. Decidir si el repo local se sube a GitHub (`arcadematicas`).
5. Contar en el issue #3 que funciona por Proton.
