# rsp/ — RSP microcode (Revenge)

**Audio status: WORKING (2026-07-07)** — ucode recompiled and executing, and
the game-side voice path fixed (stubbed `func_80018C24`, see RESOLVED below).

## Graphics ucode — handled by RT64 (do NOT recompile)
RT64's GBI database matches Revenge's graphics ucode at runtime:
**F3DEX2.fifo 2.06** (text vram `0x8002C970` → ROM `0x2D570`, data vram
`0x8003A870` → ROM `0x3B470`). Newer than WT's F3DEX/F3DLX 1.23 pair, matched
and rendering correctly (attract intro cinematic renders 2026-07-07).

## Audio ucode — RECOMPILED AND EXECUTING (2026-07-07)
`revenge_audio.toml` (text ROM `0x2C910`, size `0xC54`, text_address
`0x04001080`) → `RSPRecomp` → `rsp/revenge_audio.cpp` (`revenge_audio_ucode`),
compiled into `RevengeRecompiled` and returned by `get_rsp_microcode` for
`M_AUDTASK`. Located via the OSTask log (`ucode=0x8002BD10 ucode_data=0x8003A5C0
ucode_size=0x1000` — the 0x1000 is the rounded DMA size, WT's lesson; the real
text is bounded by the F3DEX2 text at ROM 0x2D570).

Key differences from WT:
- **NOT WT/BMHero's aspMain** (diverges at byte 0; text 0xC54 vs 0xE20) — a
  newer audio microcode revision. Jump-table targets were extracted from THIS
  ucode's own data section (first 16 halfwords at ROM `0x3B1C0` = the ABI
  command dispatch table; see the toml comments).
- One dispatch entry is stored as `0x02B0` (12-bit RSP PC; = recompiler label
  `0x12B0`). Omitting it crashed the boot with `UnhandledJumpTarget 0x02B0`
  (audio opcode 14 = POLEF-slot). RSPRecomp's generated switch normalizes with
  `(jump_target | 0x1000) & 0x1FFF`, so listing `0x12B0` in the toml suffices.

Verified executing: `[wcw][sp] task totals` counts ~43 audio tasks/s alongside
gfx tasks, no unhandled ops over multi-minute runs.

## RESOLVED 2026-07-07: silent audio = stubbed AL event-post function
`WCW_AUDIO_LOG=1` showed a healthy pipeline (60 batches/s, DAC 28800) but
peak=0 forever: command lists carried ONLY the mixer/reverb set (02/04/06/0A/
0B/0C/0D/0E recirculating delay lines); voice opcodes (01 ADPCM / 05 RESAMPLE /
09 SETVOL) never appeared and the mixer's input DRAM stayed all-zero.

**Root cause: `func_80018C24` — the libultra AL synthesizer's event-post
function, through which EVERY voice operation flows (alSynStartVoice 0xE /
StopVoice 0xF / SetPitch 0xB / SetVol 0xC posts onto the pvoice event list at
+0x7C, and the pri-4/9 transitions that set the pvoice render gate at +0x84) —
was in revenge.toml's bootstrap stub list, recompiled as an empty body.** The
game-side engine was fully alive (probed: music track started, ~20 voices
active, all 24 pvoices allocated) but every alSyn* call silently no-oped, so
the render gate never opened and `_pullSubFrame` emitted reverb only.

Why it was stubbed: IDO shared-tail split — the function ends in
`j func_80018CAC` (splat split the tail off as a phantom function), and the
bootstrap loop stubbed it instead of merging. Fix (one line + regen):
`disasm/symbol_addrs.txt` gets `func_80018C24 = 0x80018C24; // type:func
size:0xA0` (absorbs the 0x18-byte tail; nothing jal's func_80018CAC), re-split,
`gen_symbols.py`, remove the stub from revenge.toml, re-recompile. Verified:
peak hits full scale (32767) with the intro music, voice opcodes stream in the
acmd histogram, 90s run clean.

The AL structure map that got there (all in 1050.s, offsets verified at
runtime via the `[voice]` probe in src/main/main.cpp):
- alGlobals ptr `D_80036F54` → struct at 0x8006E3E0. +0x0 client list head,
  +0x4/0xC/0x14 pvoice free/alloc/lame lists, +0x1C frame sample clock,
  +0x2C event free pool, +0x30 bus chain (render callbacks), +0x38 numPVoices
  (24), +0x40 outputRate (28800).
- `func_80017510`=alInit, `func_80017554`=alClose, `func_80017590`=
  alSynAddPlayer, `func_800175E0`=alSynAllocVoice, `func_80017700`=pvoice grab,
  `func_80017DB0`=alAudioFrame, `func_80017860/980/A30/AC0`=alSynSetVol/
  SetPitch/StartVoice/StopVoice, `func_80017F18`=event alloc, `func_80018C24`=
  event post (THE fix), `func_80018CC4`=pvoice render (gate +0x84==1).
- Game layer: client `D_800604A0`, handler `func_80014500` (walks 24 voices
  of 0x158 bytes at `D_800604D0`; ALVoices 0x1C apart at `D_800604CC`);
  play-music facade `func_8000E55C(track)` (song table `D_80030D0C`, current
  track `D_80036748`), `func_8001381C` = alloc-voices+start, event queue
  w/r = `D_80060508/504`.

NB the two unexplored leads from the hunt (double event-5 registration;
rom_read streaming continuity) were NOT the cause — audio works with both
untouched. The double SI registration may still be worth a look during the
input-verification pass.
