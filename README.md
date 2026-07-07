# WCW/nWo Revenge: Recompiled (bootstrap)

Native PC port of **WCW/nWo Revenge (N64, USA)** via static recompilation —
sister project to [WCW vs. nWo World Tour: Recompiled](https://github.com/jessetbh/WCWvsNWOWorldTourRecomp),
reusing its runtime stack (the jessetbh forks with the `[wcw fix]` set), tooling,
and hard-won knowledge. Same AKI engine family, one year newer.

**Status: bootstrap (2026-07-07) — builds and executes.** Clean recompile
(1,684 functions), full port links (`build-msvc/RevengeRecompiled.exe`), runtime
stack initializes (window/D3D12/RT64), boot DMA loads the game image, and
recompiled game code executes before crashing in the recompiled `osInitialize`
— the expected zero-RENAMEs first-boot crash. First identification banked from
the symbolized backtrace: **func_800268A0 = osInitialize** (game_main's first
call, WT's exact evidence pattern). Next: RENAME it in tools/gen_symbols.py,
rebuild, iterate the boot — World Tour's documented Phase-3 bring-up loop.
No game assets are distributed; supply your own ROM (US release, SHA1
`E1711A2511394B9357B5F1AC8CA5CC17BD674836`, big-endian, entrypoint `0x80000400`).

## What's known so far (see tools/*.py for the evidence)

- **Same entrypoint as World Tour (0x80000400)**, same IDO-family compiler, same
  fixed-segment mapping (rom 0x1000 <-> vram 0x80000400).
- **Same overlay architecture as World Tour**: two CPU overlays, BOTH loading at
  vram 0x80090000 (swap-at-same-address), 9-word descriptors at rom
  0x37A30/0x37A54 — just stored right after the fixed image (rom 0x3C770 /
  0x834A0) instead of at the end of ROM. An earlier "no overlays" misread
  interpreted overlay code at contiguous vram and produced hundreds of phantom
  recompile errors (cross-function branch chaos) before the descriptor tables
  settled it. With correct mapping the overlays disassemble cleanly (373 + 657
  functions).
- **Newer libultra/IDO than WT**: byte-level fingerprint transfer fails (3/46,
  handwritten-asm leaves only). Identification redoes WT's evidence-driven
  method; first result: **func_800268A0 = osInitialize** (game_main's first
  call, confirmed by the first-boot crash chain).
- **Audio microcode is NOT byte-identical to WT's aspMain** (newer revision).
  Locate via the runtime OSTask log in get_rsp_microcode (already wired; prints
  on any boot that reaches an audio task).
- 1,720 functions across main + 2 overlays; ~40 stubs (cop0/cache OS layer +
  a few cross-branching asm functions, logged in syms/bootstrap_stubs.log).
- Idle-thread spin at 0x80000560-0x568 in func_800004B8 — WT's exact
  cooperative-scheduler deadlock pattern; the self-branch instruction patch is
  already in revenge.toml (mirrors wcw.toml's documented fix).
- Code/data interleave in the fixed segment mapped by tools/classify.py
  (rabbitizer validity + branch-locality + jump-target sanity at 256-byte
  granularity); overlay section bounds come from the descriptors (byte-exact).

## Layout

Mirrors World Tour: `disasm/` (splat project + own venv), `tools/`
(gen_symbols.py, recon/fingerprint/classify scripts), `syms/` (generated symbol
TOMLs — local dir for now, split into a Syms repo before any public release),
`revenge.toml` (N64Recomp config), `lib/` (submodules of the same jessetbh
forks). `N64Recomp.exe`/`RSPRecomp.exe` + MinGW DLLs copied from the WT build
(upstream commit `ffb39cd`).

## Next steps (WT's Phase-3 bring-up loop)

1. RENAME func_800268A0 = osInitialize in tools/gen_symbols.py, regen, recompile,
   rebuild, boot — repeat: each crash/hang names the next libultra function
   (thread/mesg/VI set), evidence-logged like WT's disasm/libultra.md.
2. Once the VI/retrace loop runs: locate the audio ucode from the OSTask log,
   RSPRecomp it (rsp/, WT's wcw_audio.toml as template).
3. Verify SaveType (Revenge may use cart SRAM rather than Controller Pak — check
   the game's save driver against WT's raw-SI pattern).
4. Review syms/bootstrap_stubs.log stubs once booting (which are game code that
   needs proper treatment vs OS asm the runtime replaces).
