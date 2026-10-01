# Wind Waker Recomp en Linux — EN ESPAÑOL (montaje de Alfred, 01/10/2026)

**Estado: FUNCIONANDO Y EN ESPAÑOL.** The Legend of Zelda: The Wind Waker recompilado,
corriendo en CachyOS sobre **Proton**, a 60 fps, con el **texto/diálogo en español**.

---

## Lo esencial

- **Lanzar**: `/home/fransis/wind-waker-recomp/lanzar-windwaker.sh`
  (o el acceso directo del menú KDE *"Wind Waker Recomp (Proton)"*). Usa el **ISO español** por defecto.
- **En inglés** (disco USA original): `WINDWAKER_DISC=/home/fransis/wind-waker-recomp/WindWaker-USA.iso ~/wind-waker-recomp/lanzar-windwaker.sh`
- **Saves / ajustes / logs**: `~/Games/umu/umu-windwaker/drive_c/users/steamuser/AppData/Roaming/BlueWake/`

---

## 1. Qué es el proyecto

- **`elliotttate/Wind-Waker-Recomp`** (fork de `chrissotraidis/bluewake`): recompilación **estática**
  de PowerPC a nativo (`main.dol` + **415 RELs**), runtime derivado de Dolphin ("Aurora") + **Dawn**
  (WebGPU) + **SDL3**.
- **Plataformas oficiales**: Windows x64 (D3D12), macOS AS / iPhone / iPad (Metal).
  **Linux no está soportado** (issue #3) — pero **funciona perfectamente por Proton** (lo verificamos).
- **Exige tu disco USA `GZLE01` revisión 0** y lo verifica (ID de disco + SHA-1 del `main.dol`).
- **La app trae el código recompilado** (`gGZLE01_recomp.dll`); solo necesita el disco.

## 2. Montaje (reproducible)

Directorio: **`/home/fransis/wind-waker-recomp/`**

1. **Release Windows x64 v0.2.2** (174 MB) → `app/WindWakerRecomp/`.
   sha256 del zip `080d267d0c0d5665195de1dbc9024c35080dfaa818cc9a92a2be4b4d93fa610c` ✅
2. **Discos**:
   - USA desde el `.rvz` de Batocera → `dolphin-tool convert -f iso` → `WindWaker-USA.iso` (GZLE01 rev 0).
   - PAL `(Europe) (En,Fr,De,Es,It)` desde el `.7z` → `pal/Legend of Zelda, The - ...(En,Fr,De,Es,It).iso`
     (**GZLP01**, Rev 0).
3. **Ejecución**: **umu-launcher** + **Proton-CachyOS nativo** (fuera de Steam):
   ```bash
   GAMEID=umu-windwaker \
   PROTONPATH=/usr/share/steam/compatibilitytools.d/proton-cachyos-native \
   umu-run ./BlueWake.exe --disc /home/fransis/wind-waker-recomp/WindWaker-ES.iso
   ```
   Dawn inicializa **D3D12** → **vkd3d-proton** → Vulkan. Audio por **DSP HLE** de Dolphin.

   ⚠️ **HALLAZGO**: el recomp **no acepta `.rvz` por `--disc`** aunque su README diga que sí
   (*"needs an uncompressed .iso or .gcm"*). Con `.iso` va perfecto. **Reportable upstream.**

## 3. El español: cómo se ha hecho

### Estructura descubierta

El disco PAL trae los textos **por idioma** en `res/Msg/data0…data4`, cada uno con `acticon.arc` +
`bmgres.arc`. Identificados por su contenido (el texto va en ASCII claro dentro del BMG):

| Carpeta | Idioma | Muestra |
|---|---|---|
| data0 | Inglés | "You can only call Tingle from areas that have maps!" |
| data1 | Alemán | "Tingle kann nur an Orten gerufen werden…" |
| data2 | Francés | "Tingle ne peut être appelé que quand une…" |
| **data3** | **ESPAÑOL** | "…lo es posible hablar con Tingle cuando puedes ver el mapa…" |
| data4 | Italiano | "Puoi chiamare Tingle solo da alcuni luoghi." |

Coincide con el orden del enum de idioma de GameCube (0=En, 1=De, 2=Fr, 3=Es, 4=It).

### El injerto

- El `bmgres.arc` del USA (640.672 B, con `color.bmc` + `zel_00.bmg`) contiene el **diálogo y los textos**.
- El español `data3/bmgres.arc` pesa **539.136 B** → **cabe** en el sitio del USA.
- **Localizado por firma**: `bmgres.arc` del USA está en el offset **0x564A13D0** del ISO
  (RARC de 640.672 B). El parser del FST está en `tools/fst.py` (a medias), y `tools/find_file.py`
  lo localiza buscando su firma (método fiable).
- Se sobrescribe in-place y se rellena con ceros. **`main.dol` y el FST quedan intactos** →
  el recomp lo sigue aceptando como **GZLE01 rev 0** ✅.
- Resultado: `WindWaker-ES.iso` (`dolphin-tool verify` → *Problems Found: No*).

```bash
# reproducible:
python3 tools/patch.py     # copia USA -> ES y aplica el injerto en 0x564A13D0
```

**VERIFICADO**: la leyenda del intro sale en español —
*"El pueblo, indefenso ante ese enorme poder, sólo podía rezar…"* (antes: *"Long ago, there existed
a kingdom…"*).

### Qué está en español y qué no

- ✅ **En español**: todo el **diálogo y los textos** (8.732 líneas). Incluye "Isla del …" (141),
  "Espada" (82), "Escudo" (20).
- ❌ **Sigue en inglés**: **menús/carteles de la interfaz** (`itemres`, `nameres`, `menures`, etc.).
  Esos archivos son **más grandes** en el PAL (multi-idioma), no caben en su sitio y haría falta
  **reconstruir el ISO entero** (FST nuevo). Es el mismo compromiso que tiene el fork francés
  (`THZoria/Wind-Waker-Recomp-PatchFR`), que tampoco publicó su script (`pal_french.py`).

**Siguiente paso posible**: herramienta de reconstrucción de ISO (FST) + averiguar cómo elige el juego
el idioma en los archivos multi-idioma (probablemente el byte de idioma del SRAM/IPL, que el recomp
fija a inglés). Daría menús y nombres de objetos en español.

## 4. Rutas

| Qué | Ruta |
|---|---|
| App (Windows x64) | `/home/fransis/wind-waker-recomp/app/WindWakerRecomp/` |
| **ISO en español (se usa por defecto)** | `/home/fransis/wind-waker-recomp/WindWaker-ES.iso` |
| ISO USA original | `/home/fransis/wind-waker-recomp/WindWaker-USA.iso` |
| ISO PAL (fuente del español) | `/home/fransis/wind-waker-recomp/pal/…(En,Fr,De,Es,It).iso` |
| Árboles extraídos | `iso-probe/` (USA), `pal-probe/`, `pal-data/` (PAL por idioma) |
| Herramientas | `tools/fst.py`, `tools/find_file.py`, `tools/patch.py` |
| Prefijo Proton | `~/Games/umu/umu-windwaker/` |
| Saves/configs/logs | `…/umu-windwaker/drive_c/users/steamuser/AppData/Roaming/BlueWake/` |

## 5. Verificado (01/10/2026)

- Arranca, **intro en español**, título, 60 fps estables
  (`shown=59.9 game=30.0`, `hitches=0`). GPU AMD RX 6700 XT (D3D12 vía vkd3d-proton).
- `module: game_id=GZLE01 abi=3 ranges=417 chunks=748 rels=415`.
- **Pendiente de que Fransis confirme**: sonido y partida con mando (no se pueden oír/probar en remoto).

## 6. Pendientes / ideas

1. **Probar a fondo** (mando, sonido) desde el escritorio.
2. **Español completo** (menús/objetos): reconstrucción del ISO + idioma.
3. **Port nativo a Linux**: viable — el port de Windows solo añadió una capa POSIX
   (`windows/compat/`), SDL3 ya se usa y **Dawn ya tiene backend Vulkan**; faltaría CMake/shell
   Linux y compilar `elliotttate/RecompCore` y `elliotttate/DolRecomp`.
4. **ARM (Odin 3)**: más lejos todavía.
5. Contar en el **issue #3** que funciona por Proton (útil para la comunidad).
6. Posible integración en Batocera `linuxgames`.
