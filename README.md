# WCW/nWo Revenge: Recompiled (bootstrap)

Native PC port of **WCW/nWo Revenge (N64, USA)** via static recompilation —
sister project to [WCW vs. nWo World Tour: Recompiled](https://github.com/jessetbh/WCWvsNWOWorldTourRecomp),
reusing its runtime stack (the jessetbh forks with the `[wcw fix]` set), tooling,
and hard-won knowledge. Same AKI engine family, one year newer.

**Status: bootstrap (2026-07-07).** Disassembly + first recompile in progress.
No game assets are distributed; supply your own ROM (US release, SHA1
`E1711A2511394B9357B5F1AC8CA5CC17BD674836`, big-endian, entrypoint `0x80000400`).

## What's known so far (see tools/*.py for the evidence)

- **Same entrypoint as World Tour (0x80000400)**, same IDO compiler, same
  rom↔vram mapping for the main segment (rom 0x1000 ↔ vram 0x80000400).
- **NO overlay system** — the single biggest structural simplification vs World
  Tour. One contiguous ~860 KB main segment (code to ~rom 0xD8000, interleaved
  with per-TU data pockets; libultra at the top end ~0x800D2xxx). WT's two
  swap-at-same-vram overlays don't exist here (16 MB cart, no need).
- **Newer libultra/IDO than WT**: byte-level fingerprint transfer mostly fails
  (3/46 direct matches, all handwritten-asm leaf functions). Identification must
  redo WT's evidence-driven method, accelerated by rank/structure anchors
  (jal-frequency table correlates well; osRecvMesg is almost certainly the #1
  most-called function at 0x800D427C — unconfirmed).
- **Audio microcode is NOT byte-identical to WT's aspMain** (newer revision).
  Locate it the way WT did: boot far enough to log the OSTask fields from
  `get_rsp_microcode` (see WT's rsp/README.md "Method").
- 3,159 functions across 27 asm subsegments (splat; code/data interleave mapped
  by tools/classify.py using rabbitizer instruction validity at 256-byte
  granularity).
- 25 functions contain cop0/cache/eret/tlb opcodes (tools scan) — stubbed for
  the first recompile exactly as WT's bring-up did, to be RENAMEd as identified.
- **PARKED REGION rom 0x88000-0xB0000 (~160 KB, vram ~0x80087400-0x800AF400)**:
  declared data for the bootstrap. It passes instruction-level validity checks
  but is full of conditional branches spanning tens of KB across spimdisasm's
  function splits — N64Recomp's one-entry function model can't express it
  piecemeal. Hypothesis: AKI's hand-written match-engine core with multiple
  entry points and free cross-branching (jal targets from outside force splits
  mid-flow). If correct, the game may boot to menus without it but will crash
  entering a match. Conquering it (likely: treat as one unit / find the real
  entry set / N64Recomp single-function-with-alt-entries modeling) is the next
  major analysis project after boot bring-up.
- Idle-thread spin located at 0x80000560-0x80000568 in func_800004B8
  (`jal func_8001C580; j back` — WT's exact cooperative-scheduler deadlock
  pattern). Queued: `[[patches.instruction]]` in revenge.toml rewriting the j at
  0x80000568 to 0x1000FFFF (`b .`) so N64Recomp emits pause_self, mirroring
  wcw.toml's documented fix.

## Layout

Mirrors World Tour: `disasm/` (splat project + own venv), `tools/`
(gen_symbols.py, recon/fingerprint/classify scripts), `syms/` (generated symbol
TOMLs — local dir for now, split into a Syms repo before any public release),
`revenge.toml` (N64Recomp config), `lib/` (submodules of the same jessetbh
forks). `N64Recomp.exe`/`RSPRecomp.exe` + MinGW DLLs copied from the WT build
(upstream commit `ffb39cd`).

## Next steps

1. Clean first recompile (tools/recomp-loop.ps1 iterates missing function
   boundaries from N64Recomp tail-call errors).
2. Port shell: adapt WT's CMakeLists + src/main (game id `revenge.us`, hash
   check, SaveType — Revenge may use cart SRAM rather than Controller Pak;
   verify at bring-up).
3. libultra identification for the runtime-provided set (threads/mesg/VI):
   WT's disasm/libultra.md documents per-function evidence patterns; the
   jal-rank + MMIO-block anchors in tools/fingerprint3.py narrow candidates.
4. Boot bring-up: expect WT's invariant list to apply (idle-thread busy-poll
   needing a self-branch patch, PresentationMode Console, Framerate Original,
   G_FORCEMTX-only rendering → RT64 zero-VP guard already in the rt64 fork).
