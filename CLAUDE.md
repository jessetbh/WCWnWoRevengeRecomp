# CLAUDE.md — WCW/nWo Revenge: Recompiled

Contributor/agent instructions. **This is the sister project of WCW vs. nWo World
Tour: Recompiled at `C:\Users\selki\depot\WcwNwoWorldTour`** — same AKI engine
family, same runtime stack, and nearly every technique used here was proven there
first. **Consult the World Tour project constantly**:

- `..\WcwNwoWorldTour\CLAUDE.md` — its invariants (most apply here verbatim).
- `..\WcwNwoWorldTour\docs\devlog.md` — every root-caused bug from raw ROM to a
  shipped public beta; if something here looks mysterious, WT probably hit it.
- `..\WcwNwoWorldTour\disasm\libultra.md` — the per-function identification
  evidence method this project's bring-up repeats.
- `..\WcwNwoWorldTour\BUILDING.md` — toolchain story (identical here).
- WT shipped v0.1.0 publicly: https://github.com/jessetbh/WCWvsNWOWorldTourRecomp

## What this project is

Native PC port of **WCW/nWo Revenge (N64, USA)** via N64Recomp static
recompilation on the same jessetbh fork stack (N64ModernRuntime/RecompFrontend/
rt64, `wcw` branches — the `[wcw fix]` set is REQUIRED and shared; any edit under
`lib/` follows WT's fork workflow: commit on `wcw` branch, push, bump pin, rerun
WT's `lib-patches\export.ps1`).

**Status (2026-07-07): builds and executes.** Clean recompile (1,684 funcs),
`build-msvc\RevengeRecompiled.exe` links, runtime initializes, boot DMA correct,
recompiled code runs, crashes in recompiled `osInitialize` — the expected
zero-RENAMEs first boot. README.md has the full findings; the bring-up loop is:

1. RENAME the next-identified libultra function in `tools\gen_symbols.py`
   (**first one banked: `func_800268A0` = osInitialize**, from the symbolized
   crash chain `game_main → 800268A0 → 800275F0 → 800281F0`).
2. `python tools\gen_symbols.py` → `.\N64Recomp.exe revenge.toml` →
   `cmake --build build-msvc --target RevengeRecompiled` → run with
   `WCW_AUTOBOOT=revenge.z64` from `build-msvc\` → symbolize the next crash
   against `build-msvc\RevengeRecompiled.map` (nearest map symbol ≤ RVA,
   preferred base 0x140000000) → identify → repeat. Log evidence per function
   the way WT's `disasm/libultra.md` does.

## Hard-won facts (do not re-derive)

- **Two overlays, BOTH at vram 0x80090000** (WT's exact architecture), rom
  0x3C770/0x834A0, 9-word descriptors at rom 0x37A30/0x37A54. An early "no
  overlays" misread cost half a day — trust the descriptors.
- Fixed segment rom 0x1000 ↔ vram 0x80000400 (same as WT).
- **Newer libultra than WT: byte fingerprints do NOT transfer** (tools/
  fingerprint*.py, 3/46). Identify by evidence, not bytes. jal-rank anchors:
  candidates in tools/fingerprint3.py output.
- Audio ucode ≠ WT's aspMain bytes. Locate via the OSTask log already wired in
  `src/main/main.cpp` `get_rsp_microcode` (prints type/ucode/ucode_data/size).
- Idle-thread spin at 0x80000568: instruction patch already in revenge.toml
  (self-branch → pause_self), mirroring wcw.toml's documented fix.
- ~40 stubs in revenge.toml (`syms/stub_candidates.txt`; extra discoveries in
  `syms/bootstrap_stubs.log`) — cop0/cache OS layer + a few cross-branching asm
  functions. Review once booting.
- WT boot invariants expected to apply: PresentationMode **Console**, Framerate
  **Original**, G_FORCEMTX-only rendering (rt64 fork's zero-VP guard handles it),
  raw-SI input path (librecomp si.cpp fork).
- Save type: currently SaveType::Sram copied from WT (Controller Pak emulation);
  VERIFY what Revenge actually uses during bring-up (may be cart SRAM — simpler).

## Build

Same two-toolchain story as WT (see its BUILDING.md). Quick loop:

```powershell
python tools\gen_symbols.py                # syms/dump.toml (RENAME map lives here)
.\N64Recomp.exe revenge.toml               # -> RecompiledFuncs/ (needs revenge.z64 at root)
. .\tools\env-msvc.ps1
cmake --build build-msvc --target RevengeRecompiled
```

`N64Recomp.exe`/`RSPRecomp.exe` + MinGW DLLs at repo root are copies of WT's
(upstream N64Recomp @ ffb39cd). disasm re-split: `disasm\.venv\Scripts\python.exe
-m splat split revenge.yaml` (run inside `disasm\`).

## Conventions

- Everything mirrors WT: `wcw` C++ namespace kept for glue (shared frontend
  couplings expect it), gitignore covers ROMs/generated dirs, **never commit ROM
  data or extracted assets**, PowerShell for shell commands.
- Names "RevengeRecompiled" / display "WCW/nWo Revenge" are PLACEHOLDERS —
  owner picks the public name before any release (WT precedent: full title).
- No GitHub repo yet (local git only). Before any publication: separate Syms
  repo, secrets/CI per WT's beta-release-plan playbook.
