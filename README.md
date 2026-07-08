# WCW/nWo Revenge: Recompiled (bootstrap)

Native PC port of **WCW/nWo Revenge (N64, USA)** via static recompilation —
sister project to [WCW vs. nWo World Tour: Recompiled](https://github.com/jessetbh/WCWvsNWOWorldTourRecomp),
reusing its runtime stack (the jessetbh forks with the `[wcw fix]` set), tooling,
and hard-won knowledge. Same AKI engine family, one year newer.

**Status: GAME RUNS (2026-07-07) — steady 30fps, RDP frames render through
RT64.** One day of WT's Phase-3 bring-up loop (11 boot iterations, each
crash/hang symbolized against the .map and identified by evidence) took the
port from the zero-RENAMEs first-boot crash to a running game: **38 libultra
functions named** (threads/mesg/events/VI/PI/SI/AI/SP-task/clock sets — full
per-function evidence in `disasm/libultra.md`), overlays swap in correctly,
graphics ucode identified as **F3DEX2.fifo 2.06** (RT64-handled), health
telemetry shows `vis/s=30, ext=0, dpc+30/s` with zero crashes. **Audio WORKS
(same day):** the RSP audio ucode is recompiled (rsp/revenge_audio.toml) and
the game's music/SFX render at full scale after fixing a mis-stubbed AL synth
function (rsp/README.md has the story).
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

## Next steps (post-boot)

1. ~~**Audio voice path**~~ **DONE 2026-07-07 — AUDIO WORKS** (music + SFX at
   full scale). The silence was a mis-stubbed game function: `func_80018C24`,
   the libultra AL synth event-post that every alSynStartVoice/SetVol/SetPitch/
   StopVoice flows through, was in revenge.toml's bootstrap stub list (IDO
   shared-tail split had made it look unrecompilable). One-line
   symbol_addrs.txt size-extension + un-stub fixed it; full root-cause
   narrative and the AL structure map in rsp/README.md. Lesson for the
   remaining stubs review (step 4): a stub that "boots fine" can still be
   load-bearing game code.
2. ~~**Verify visuals/input in-game**~~ **DONE 2026-07-07 — INPUT WORKS.**
   Keyboard Start breaks the attract loop to the title screen and the menus
   navigate/confirm correctly (screenshot-verified through Mode Select →
   Exhibition → Single/Tag Match). Root cause of the initial dead input: the
   bring-up had RENAMEd func_80021190 = osContStartReadData, which made the
   runtime shim swallow read requests while the game's own (un-renamed)
   osContGetReadData parsed a PIF RAM nobody filled. WT's invariant holds
   exactly: rename ONLY osContInit + __osSiRawStartDma/__osSiDeviceBusy and
   let the game's controller layer run against si.cpp's PIF emulation.
3. ~~Verify SaveType~~ **DONE 2026-07-07 — cart SRAM confirmed, saves persist.**
   func_80000A40 is Revenge's osSramInit (PI handle 0xA8000000, device type 3,
   linked into __osPiTable) — unlike WT, Revenge saves to cart SRAM, which
   librecomp's SaveType::Sram routes natively (phys >= 0x08000000 →
   saves/wcw.nwo.revenge.us.bin). Verified live: the save carries AKI's
   repeated "19 97 10 21" magic with real data (5,630 nonzero bytes), play
   sessions produce incremental 3-byte updates (read-modify-write), and a
   no-input boot validates the magic and preserves the file byte-for-byte.
4. ~~Review remaining revenge.toml stubs~~ **DONE 2026-07-07.** All 13
   non-privileged bootstrap stubs (syms/bootstrap_stubs.log) triaged: 10 were
   real game code and are now recompiled live (8 IDO shared-tail splits fixed
   via symbol_addrs.txt size hints — incl. a 0x1488-byte ovl_b cluster — one
   segment-boundary fix at rom 0x2C840 for func_8002BBCC's tail, one
   multi-entry cluster via the EXTRA_FUNCS injection in gen_symbols.py);
   3 re-stubbed with documented reasons (__osDispatchThread + two swc2 OS
   thunks). The 18 privileged cop0/cache/tlb stubs are genuine OS asm the
   runtime replaces. Verified: 120s run, 30fps, ext=0, audio full-scale, no
   crashes.
5. Cosmetic: window title still says "WCW vs. nWo World Tour: Recompiled"
   (shared shell string) — rename when the public name is picked.
6. **Pending fork bookkeeping** (owner action; see CLAUDE.md fork workflow):
   lib/N64ModernRuntime has local commit `dc4592a` on its `wcw` branch
   ("[wcw fix] Overlay swap mapping: table-driven rom lookup +
   registered-address filter" — pi.cpp + overlays.cpp; no-op for WT's layout).
   This repo's pin already points at it. Still to do:
   (a) `git push` from `lib\N64ModernRuntime` to the jessetbh fork;
   (b) in the WT checkout, advance its lib\N64ModernRuntime submodule to
   include `dc4592a` (keep both ports on the same fork commit);
   (c) run `..\WcwNwoWorldTour\lib-patches\export.ps1` and commit the
   refreshed N64ModernRuntime.patch in WT.
