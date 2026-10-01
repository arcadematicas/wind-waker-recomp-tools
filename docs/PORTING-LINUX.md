# Porting the recompilation to Linux (x86-64 and ARM64) — feasibility notes

*Researched 2026-10-01. Nothing here has been implemented; this is the record of what the code
actually says, so the work can start without re-doing the investigation.*

**Short version:** far easier than it looks. The graphics/runtime layer (Aurora) **already builds and
passes CI on Linux**, and the project's own builder is explicitly designed around per-platform
"profiles". What is missing is the small host layer (entry shim + CMake target + build script),
because the shipped ports are Windows and Apple only.

---

## 1. The stack, and what each part is

| Layer | Where | Platform story |
|---|---|---|
| The recompiled game (`gGZLE01_recomp`) | generated from the user's disc by **DolRecomp** | the translator emits **C**, so the output is portable; macOS/iOS already consume arm64 |
| Runtime / GX / audio / PAD / DVD / CARD | **Aurora** (inside RecompCore, `GXRuntime/graphics/aurora`) | **already cross-platform** (see below) |
| Graphics API | **Dawn** (Chromium's WebGPU) over D3D12 / Metal / **Vulkan** | prebuilt binaries for Linux exist for **both** x86-64 and aarch64 |
| Host (game loop, save states, settings, mods, disc import) | `runtime/host/src` (+ thin per-OS shim) | POSIX source; the Windows port added a compat layer, **Linux needs none** |
| Build orchestration | `scripts/builder/build.sh` (Apple) / `scripts/windows/build.py` | **generic pipeline + a per-port "profile"** |

## 2. Evidence that Linux is already a supported target

**Aurora's README** (`GXRuntime/graphics/aurora/README.md`):

> Application layer using SDL3 — *Runs on Windows, Linux, macOS, iOS, tvOS, Android*
> Graphics API support: D3D12, **Vulkan**, Metal
> DVD compatibility layer — Utilizes **nod** to support all GameCube/Wii disc image types,
> **including RVZ**

**Aurora's CI** (`GXRuntime/graphics/aurora/.github/workflows/build.yml`) builds and tests on
`ubuntu-latest`, `macos-latest` and `windows-latest`, installing a full Linux dependency set
(SDL3, X11, Wayland, PipeWire, ALSA, EGL/GLES, udev, dbus…).

**The Dawn provider** (`aurora/cmake/AuroraDawnProvider.cmake`) has an explicit Linux branch:

```cmake
else () # Linux / other
  set(DAWN_ENABLE_VULKAN ON ...)
  set(DAWN_ENABLE_DESKTOP_GL ON ...)
  set(DAWN_ENABLE_OPENGLES ON ...)
```

and, for the prebuilt ("package") route:

```cmake
# Prebuilt Dawn packages available for: windows-{amd64,arm64},
# linux-{x86_64,aarch64}, darwin-{arm64,x86_64}, ios-arm64, android-aarch64
```

`encounter/dawn` release assets confirm it:

```
dawn-linux-x86_64.tar.gz     dawn-linux-aarch64.tar.gz
dawn-windows-amd64.tar.gz    dawn-windows-arm64.tar.gz
dawn-darwin-arm64.tar.gz     dawn-ios-arm64.tar.gz     dawn-android-aarch64.tar.gz
```

Wayland is wired in too (`DAWN_USE_WAYLAND ON` when `CMAKE_SYSTEM_NAME STREQUAL Linux`).

**RecompCore's CMakeLists is Dolphin's**, so the whole system layer is already there: `set(LINUX TRUE)`,
`ENABLE_X11`, `ENABLE_EGL`, `ENABLE_WAYLAND`, `ENABLE_ALSA`, `ENABLE_PULSEAUDIO`, `ENABLE_CUBEB`,
`ENABLE_VULKAN ON`, `ENABLE_SDL`, `ENABLE_EVDEV`, `ENABLE_HWDB`, `LINUX_LOCAL_DEV`. It even keeps
the Android/arm64 paths (`Externals/libadrenotools` for Adreno).

**The builder is generic by design** (`scripts/builder/build.sh` header):

> The pipeline is generic; everything game-specific (disc checks, translator settings, the app
> target, mods) lives in a **profile**, `scripts/builder/profiles/NAME.sh` …
> `docs/BUILDER.md` explains the split and **what a new port's profile provides**.

## 3. How big is the missing piece?

The Windows port is the model to copy, and it is small:

| File | Lines | Purpose |
|---|---|---|
| `windows/src/win_entry.c` | 723 | entry point, default paths, session log, env defaults |
| `windows/src/win_settings.cpp` | 1,175 | the settings/mods menu (Dear ImGui), settings.ini |
| `windows/src/win_disc.c` | 419 | disc import (reuses the Apple `disc_import.c`) |
| `windows/compat/*` | — | POSIX shim for Windows — **not needed on Linux** |
| **total** | **~2,300** | |

The shared host (`runtime/host/src`, ~30 translation units) is listed by
`windows/CMakeLists.txt` and is otherwise platform-neutral: scanning the whole tree, only **eight**
files contain any platform guard, and they are tiny (`main.c` 2+2, `mouse_camera.c` 4+1,
`settings_menu.h` 2+1, `jump_button.c` 3, plus the iOS-only files).

## 4. Plan (x86-64 first)

1. **`linux/CMakeLists.txt`** — mirror `windows/CMakeLists.txt` without the compat layer: the shared
   host sources + `GXRuntime`/Aurora + the DSP donor; link SDL3 and Dawn (Vulkan backend).
2. **`linux/src/linux_entry.c`** — the analogue of `win_entry.c`: default paths beside the
   executable, session log, env defaults. Much shorter than the Windows one (no `windows.h`,
   no path translation).
3. **Settings**: reuse the portable-folder idea the Windows shim already has
   (`BLUEWAKE_DATA_DIR`); a Linux build can use `${XDG_DATA_HOME:-~/.local/share}` by default.
4. **Disc import**: reuse `apple/ios/src/disc_import.c` exactly as the Windows port does.
   (Bonus: Aurora reads `.rvz` through **nod**, so the "no `.rvz` via `--disc`" limitation can be
   dropped on Linux.)
5. **Game module**: translate the user's disc with DolRecomp and compile the generated C for
   `x86-64` (`-march=x86-64-v3` like the Windows build). No new translator work.
6. **Build script / profile**: a `scripts/linux/build.sh` (or a new builder profile) following the
   Mac one, which is already generic.
7. **Bring-up**: window, input (SDL3), audio (SDL3), and Dolphin-DSP audio.

## 5. ARM64 — extra steps

* Dawn prebuilt **exists for `linux-aarch64`**, so no Dawn build from source is required.
* The game module is C: compile it for aarch64 (the macOS/iOS builds already produce arm64 code,
  so the generated source is portable). Cross-compile from the PC or build on the device.
* Aurora's Linux CI is x86-64 only; arm64 Linux is untested there, though Android arm64 paths exist.
* **The real risk is the GPU and performance.** On an AYN Odin 3 (Adreno 830) it would be
  Dawn → Vulkan → **Turnip** (Mesa 26.1+ supports Gen8; the device has 26.2.3 with Turnip
  installed). Plausible but unproven. Dawn's OpenGLES-over-freedreno backend is the fallback.
* Handheld performance is an open question: the game is natively 30 FPS and Dolphin runs Wind Waker
  on Android, so it is not absurd — but a Dawn-based renderer is new territory.

## 6. Estimate

| Target | Work | Risk | Notes |
|---|---|---|---|
| **Linux x86-64** | ~3–6 working days (1–2 focused sessions with agent help) | **low–medium** | the hard layer already builds and is CI-tested on Ubuntu |
| **Linux ARM64** | +1–2 weeks | **medium–high** | driver/compat and performance unknowns |

Test beds: x86-64 on the desktop (Ryzen 7 5800X + RX 6750 XT — the natural target); ARM64 on the
Odin 3.

Biggest unknowns to resolve early:
1. Whether RecompCore's full Dolphin-flavoured CMake is happy to build only the subset the port
   needs (Qt, Discord RP, RetroAchievements, autoupdate can all be switched off).
2. Audio path: the Windows port uses SDL3 audio; confirm Aurora's `aurora_audio.cpp` + SDL3 is
   enough, and whether the Dolphin-DSP donor is needed (there is an `lle_audio` option).
3. First build time (RecompCore is a big tree).

## 7. Strategy

This is a strong **upstream** candidate: the project's own builder documents per-port profiles,
Aurora advertises Linux, Dawn ships Linux binaries for both architectures, and issue **#3
("Linux Support")** is open and unanswered. Doing it as a profile inside a fork — then offering it
back — is the cleanest route, and it keeps the port maintainable as upstream moves.

## 8. Status

**Not started.** Parked on 2026-10-01 at the user's request. Everything needed to begin is in this
file; the first concrete step is section 4, item 1.
