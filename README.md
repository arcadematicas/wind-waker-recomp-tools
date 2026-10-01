# Wind Waker Recomp Tools

Community tools around the [Wind Waker Recomp / BlueWake](https://github.com/elliotttate/Wind-Waker-Recomp)
static recompilation of *The Legend of Zelda: The Wind Waker* (GameCube).

Two things live here:

1. **`windwaker_pal_text.py`** — play the recompilation with the **French, Spanish or Italian
   text** of the European disc, on top of your own USA disc.
2. **Linux notes and scripts** — the recompilation is shipped for Windows and macOS only, but it
   runs fine on Linux through Proton; and a few extras around it.

> **No game data is included or distributed by this repository.** You need your own legally
> obtained discs. The tools only rearrange data that is already on your own discs.

---

## 1. `tools/windwaker_pal_text.py` — PAL text on a USA disc

### The problem

The recompilation accepts exactly one disc: **The Wind Waker, USA (`GZLE01`), revision 0**. It
checks the disc ID and the SHA-1 of `main.dol` and refuses anything else, so you cannot simply hand
it the European disc (`GZLP01`) - which is the only GameCube release that contains **French,
German, Spanish and Italian** (the USA release is English only).

### The trick

All of the game's dialogue and text lives in one archive, `res/Msg/bmgres.arc`: a GameCube **RARC**
containing `color.bmc` and `zel_00.bmg` (a BMG message bank, plain ASCII text inside).

* The **USA** disc has exactly one copy of it.
* The **PAL** disc ships **five** copies, one per language, under `res/Msg/data0..data4`:

  | folder | language | RARC size |
  |---|---|---|
  | data0 | English | 640,736 |
  | data1 | German | 664,736 |
  | data2 | French | 586,880 |
  | data3 | **Spanish** | 539,136 |
  | data4 | Italian | 538,912 |

  (the USA one is 640,672 bytes)

If the language you want is **smaller than or equal to** the US archive, it fits in the gap left by
the US one. The tool overwrites it **in place** and zero-fills the rest. `main.dol` and the file
system table (FST) are never touched, so the disc keeps the USA game code and revision and the
recompilation keeps accepting it.

### What works and what does not

| | |
|---|---|
| ✅ French, Spanish, Italian | fit in place, supported **today** |
| ❌ German | 24,064 bytes **too big** for the US gap: it needs a full ISO rebuild (moving files and rewriting the FST). Not implemented yet |
| ✅ Dialogue, narration, most in-game text | translated |
| ❌ Menus and item / island name plates | stay in English: those live in other archives that are *bigger* on the PAL disc (they hold all five languages at once) |

### Requirements

* Python 3 (standard library only - **no external tools, no Dolphin install**)
* Your own **USA** disc (`GZLE01` rev 0) and your own **PAL** disc (`GZLP01`,
  *Europe (En,Fr,De,Es,It)*), as `.iso` or `.gcm` (a `.rvz` must be converted first: the
  recompilation itself only reads `.iso`/`.gcm`)

### Usage

See what is inside a disc (read-only, writes nothing):

```bash
python3 tools/windwaker_pal_text.py --list --disc "The Legend of Zelda - The Wind Waker (USA).iso"
python3 tools/windwaker_pal_text.py --list --disc "The Legend of Zelda - The Wind Waker (Europe) (En,Fr,De,Es,It).iso"
```

It prints every dialogue archive it finds, its size, a text sample and the language it detected, so
you can see with your own eyes which is which.

Build the patched disc:

```bash
python3 tools/windwaker_pal_text.py \
    "The Legend of Zelda - The Wind Waker (USA).iso" \
    "The Legend of Zelda - The Wind Waker (Europe) (En,Fr,De,Es,It).iso" \
    "WindWaker-ES.iso" \
    --language es
```

`--language` takes `en`, `de`, `fr`, `es` (default) or `it`; `--index N` picks a PAL archive by its
position instead of by detection. Your input discs are opened read-only and never modified.

Then launch the recompilation and choose the patched `.iso` when it asks for your disc.

### How it is verified

The German case fails *before* anything is written, with a clear message. For the supported
languages the output was checked to be **byte-for-byte identical** to an ISO produced by an older,
independent method, and both discs' SHA-256 were confirmed unchanged afterwards.

---

## 2. Linux

The recompilation is a Windows program. On Linux it runs well through **umu-launcher + Proton**
(tested on CachyOS with `proton-cachyos-native`, AMD RX 6700 XT, a steady 60 FPS with Smooth
Motion); Dawn initialises Direct3D 12 and vkd3d-proton translates it to Vulkan.

```bash
GAMEID=umu-windwaker \
PROTONPATH=/usr/share/steam/compatibilitytools.d/proton-cachyos-native \
umu-run ./BlueWake.exe --disc /path/to/WindWaker-ES.iso
```

`scripts/lanzar-windwaker.sh` wraps that up.

Two things worth knowing:

* **The `--disc` option does not accept `.rvz`**, even though the project README says it does
  ("an .rvz is unpacked once…"). It reports *"This file is not a GameCube disc image. BlueWake needs
  an uncompressed .iso or .gcm dump of your disc."* Convert first, e.g.
  `dolphin-tool convert -i game.rvz -o game.iso -f iso`.
* **The app supports a portable data folder**: set **`BLUEWAKE_DATA_DIR`** and the settings, saves,
  memory card and texture packs live there instead of `%APPDATA%\BlueWake`, which makes a
  self-contained folder that runs anywhere.

Other scripts:

| Script | What it does |
|---|---|
| `scripts/lanzar-windwaker.sh` | Launches through Proton, picking the patched disc by default |
| `scripts/hacer-iso-es.sh` | Convenience wrapper around `windwaker_pal_text.py` |
| `scripts/actualizar.sh` | Downloads the latest recompilation release, verifies its SHA-256, keeps a backup |

---

## Legal

* This repository contains **no game data**: no disc images, no extracted files, no textures.
  You must supply your own legally obtained discs.
* Do not redistribute patched disc images. The patched ISO contains the game's copyrighted data.
* The recompilation itself is GPL-3.0 and publishes its own app releases (which do contain the
  recompiled code); its model is that the player supplies their own disc. See its
  [AGENTS.md](https://github.com/elliotttate/Wind-Waker-Recomp/blob/main/AGENTS.md).

## Credits

* [elliotttate/Wind-Waker-Recomp](https://github.com/elliotttate/Wind-Waker-Recomp) and
  [chrissotraidis/bluewake](https://github.com/chrissotraidis/bluewake) — the recompilation.
* The French fork [`THZoria/Wind-Waker-Recomp-PatchFR`](https://github.com/THZoria/Wind-Waker-Recomp-PatchFR)
  described the same idea first; it never published its script, so this tool was written from scratch.

---

## En español

Esta herramienta te permite jugar la recompilación de Wind Waker **con los textos en español**
(además de francés e italiano): coge el texto del disco europeo `GZLP01` y lo injerta en tu disco
americano `GZLE01`, dejando `main.dol` intacto para que la recompilación lo siga aceptando.

```bash
python3 tools/windwaker_pal_text.py "MI-USA.iso" "MI-PAL.iso" "WindWaker-ES.iso" --language es
```

- Se traduce **el diálogo y los textos**; los menús y los nombres de objetos siguen en inglés.
- El **alemán** no cabe (su archivo es mayor) y necesitaría reconstruir el ISO entero.
- **No se distribuye ningún dato del juego**: usa tus propios discos.
