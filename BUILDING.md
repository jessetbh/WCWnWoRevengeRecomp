# Building Guide

**Building is NOT required to play** — download a release zip instead (see the
README). This guide is for contributors building from source on Windows (the beta
is Windows-only; CI in `.github/workflows/validate.yml` runs these exact steps).

The pipeline has two halves:

1. **Recompile** — run `N64Recomp` on your ROM to generate `RecompiledFuncs/`
   (~16 MB of C), and `RSPRecomp` to generate the audio-microcode CPU translation.
2. **Port build** — compile the generated C plus the runtime stack
   (ultramodern + librecomp + RecompFrontend + RT64) with **clang-cl** into
   `RevengeRecompiled.exe`.

Unlike the sister project (World Tour), there is no `patches/` pipeline yet, so no
MIPS-capable clang or GNU make is needed — the toolchain list is shorter.

## 1. Prerequisites

- **Git**
- **VS Build Tools 2022** with clang-cl, CMake, and Ninja (needs UAC):

  ```powershell
  winget install --id Microsoft.VisualStudio.2022.BuildTools --override "--passive --wait --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Llvm.Clang --add Microsoft.VisualStudio.Component.VC.Llvm.ClangToolset --add Microsoft.VisualStudio.Component.VC.CMake.Project --includeRecommended"
  ```

  RT64 is D3D12/Vulkan and needs clang-cl + the Windows SDK; MinGW cannot
  substitute for the port build.
- *(Optional — regenerating symbols only)* Python 3 with a splat venv, see §7.

## 2. Clone

```powershell
git clone --recursive https://github.com/jessetbh/WCWnWoRevengeRecomp.git
cd WCWnWoRevengeRecomp
```

`--recursive` matters: `lib/` contains the runtime-stack forks (with required
`[wcw fix]` changes shared with the sister project). Symbol metadata is tracked
directly in this repo under `syms/`.

**Windows path-length warning**: the nested submodule tree produces long internal
git paths, and cloning into a deep directory (OneDrive Documents, etc.) can fail
with `Filename too long`. Either clone into a short path (e.g. `C:\src\`) or enable
long-path support first:

```powershell
git config --global core.longpaths true
```

## 3. Provide the ROM

Place the **WCW/nWo Revenge (USA)** ROM as `revenge.z64` in the repo root —
SHA1 `E1711A2511394B9357B5F1AC8CA5CC17BD674836`, big-endian. It is used only by
the recompiler steps below; at runtime the launcher asks for (and remembers) a
ROM on first start. The code is not compressed, so there is no decompression step.

## 4. Build N64Recomp + RSPRecomp, then recompile

Build the recompiler CLI from upstream at the pinned commit
(`ffb39cdad1da5de07eaaa48bd1db4a89a7986771` — the commit `RecompiledFuncs/` was
last generated with; any toolchain works, VS is fine):

```powershell
git clone --recurse-submodules https://github.com/N64Recomp/N64Recomp.git N64RecompSource
git -C N64RecompSource checkout ffb39cdad1da5de07eaaa48bd1db4a89a7986771
git -C N64RecompSource submodule update --init --recursive
cmake -S N64RecompSource -B N64RecompSource/build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build N64RecompSource/build --target N64RecompCLI RSPRecomp
copy N64RecompSource\build\N64Recomp.exe .
copy N64RecompSource\build\RSPRecomp.exe .
```

(Not to be confused with the `jessetbh/N64Recomp` fork pinned inside
`lib/N64ModernRuntime` — that one only supplies the `recomp.h` header the port
compiles against.)

Then recompile the game and the audio microcode (from the repo root):

```powershell
.\N64Recomp.exe revenge.toml               # -> RecompiledFuncs/
.\RSPRecomp.exe rsp\revenge_audio.toml     # -> rsp/revenge_audio.cpp
```

## 5. Build the port

Configure and build with clang-cl (`tools/env-msvc.ps1` puts the VS tools on
PATH for the current shell):

```powershell
. .\tools\env-msvc.ps1
cmake -S . -B build-msvc -G Ninja -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_BUILD_TYPE=Release
cmake --build build-msvc --target RevengeRecompiled
```

The exe lands at `build-msvc\RevengeRecompiled.exe`, with `assets/`,
`recompcontrollerdb.txt`, and the SDL2/DXC DLLs copied next to it — that folder is
a complete, runnable install.

Build types: `Release` is the shipping configuration (windowed app; stdio goes to
`%LOCALAPPDATA%\RevengeRecompiled\RevengeRecompiled.log`, or launch with
`--show-console`); `Debug` keeps the console.

## 6. Run

Double-click `RevengeRecompiled.exe`. First run: **Load ROM** → pick your ROM →
it is validated and stored → **Start Game**. Saves and config live in
`%LOCALAPPDATA%\RevengeRecompiled\` (create an empty `portable.txt` next to the
exe for a portable install).

Dev conveniences:

- `WCW_AUTOBOOT=<path|1>` — skip the launcher and boot straight into the game
  (`1` uses the stored ROM).
- Crash backtraces print RVAs that resolve against `build-msvc\
  RevengeRecompiled.map` (always emitted): `python tools\symbolize.py --log <log>`.
- Env-gated diagnostics: `WCW_AUDIO_LOG=1` (audio pipeline + acmd histogram),
  `WCW_HEALTH_LOG=1` (1/s frame-rate + message-queue health), `WCW_VI_LOG=1`.

## 7. Regenerating symbols (contributors)

`syms/dump.toml` is generated; the regeneration tooling is the splat project in
`disasm/` + `tools/gen_symbols.py` (the libultra `RENAME` map and the
`EXTRA_FUNCS` multi-entry injection live there; evidence log in
`disasm/libultra.md`). Requires Python and a splat venv, plus the ROM copied to
`disasm\revenge.z64`:

```powershell
python -m venv disasm\.venv
disasm\.venv\Scripts\pip install splat64 spimdisasm rabbitizer n64img crunch64 pygfxd
cd disasm; ..\disasm\.venv\Scripts\python.exe -m splat split revenge.yaml; cd ..
python tools\gen_symbols.py                                      # -> syms/dump.toml
```

Function-boundary fixes (IDO shared-tail splits) go in `disasm/symbol_addrs.txt`
as `type:func size:` hints — use `rom:` attributes for overlay functions, since
both overlays share vram `0x80090000`. `tools/recomp-loop3.py` automates the
common treatments.

## 8. Changing anything under `lib/`

`lib/` submodules are jessetbh forks carrying the `[wcw fix]` set on `wcw`
branches, shared with the sister project
([World Tour](https://github.com/jessetbh/WCWvsNWOWorldTourRecomp)). After ANY
edit under `lib/`: commit on that repo's `wcw` branch, push to the fork, and bump
the submodule pin here. The diff-vs-upstream record (`lib-patches/`) is maintained
in the World Tour repo.
