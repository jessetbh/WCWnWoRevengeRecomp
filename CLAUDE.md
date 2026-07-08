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

**Status (2026-07-07): GAME RUNS — 30fps, RDP frames render through RT64.**
The Phase-3 bring-up loop is DONE for boot: 11 iterations named **38 libultra
functions** (evidence per function in `disasm/libultra.md`), overlays swap,
gfx ucode = F3DEX2.fifo 2.06, telemetry `vis/s=30 ext=0 dpc+30/s`, no crashes.
The loop tooling, if more identifications are needed:

1. RENAME the identified function in `tools\gen_symbols.py` (verify a runtime
   shim exists first — `grep <name>_recomp lib/N64ModernRuntime/{librecomp,
   ultramodern}/src/*.cpp`; if it was stubbed in revenge.toml, remove it there).
2. `python tools\gen_symbols.py` → `.\N64Recomp.exe revenge.toml` →
   `cmake --build build-msvc --target RevengeRecompiled` → run with
   `WCW_AUTOBOOT=revenge.z64` from `build-msvc\` → symbolize crashes with
   `python tools\symbolize.py --log <err.log>` (parses the backtrace against
   build-msvc\RevengeRecompiled.map) → identify → repeat. For silent hangs use
   `WCW_HEALTH_LOG=1 WCW_VI_LOG=1` (1/s telemetry: vis/s = real frame rate,
   ext = undelivered-message backlog; ext growing with del/s=0 means a game
   thread is spinning without yielding).

**Audio phase (2026-07-07): DONE — music + SFX render at full scale.**
`rsp/revenge_audio.toml` → `rsp/revenge_audio.cpp`, wired for M_AUDTASK.
NOT WT's aspMain — newer ucode, own dispatch table (see rsp/README.md for the
12-bit-PC jump-table gotcha). The silence was `func_80018C24` (libultra AL
synth event post — ALL alSynStartVoice/SetVol/SetPitch/StopVoice calls route
through it) sitting in revenge.toml's stub list from an IDO shared-tail
mis-split; fixed by a symbol_addrs.txt size-extension to 0xA0 + un-stub
(root cause + full AL structure map in rsp/README.md). Diagnostics:
`WCW_AUDIO_LOG=1` enables the acmd dump/opcode histogram/[voice] pipeline
probe in src/main/main.cpp and the [audio] peak line.
Next: input verify, SaveType verify, stubs review — **treat every remaining
stub as suspect game code, not settled OS asm; the audio bug proves a stub
can boot clean and still kill a subsystem.**

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
