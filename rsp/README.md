# rsp/ — RSP microcode (Revenge)

## Graphics ucode — handled by RT64 (do NOT recompile)
RT64's GBI database matches Revenge's graphics ucode at runtime:
**F3DEX2.fifo 2.06** (text vram `0x8002C970` → ROM `0x2D570`, data vram
`0x8003A870` → ROM `0x3B470`). Newer than WT's F3DEX/F3DLX 1.23 pair, matched
and rendering correctly (attract intro cinematic renders 2026-07-07).

## Audio ucode — RECOMPILED AND EXECUTING (2026-07-07); output silent (see below)
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

## OPEN: audio output is silent (voice path never produces input) — 2026-07-07
`WCW_AUDIO_LOG=1` shows a healthy pipeline (60 batches/s to SDL, stable buffer,
game-set DAC rate 28800) but **peak=0 forever**, including minutes into the
attract intro (which has music on hardware). Root-caused one level up with the
acmd diagnostics in `src/main/main.cpp` (`revenge_audio_traced`, env
`WCW_AUDIO_LOG=1`):
- The game's command lists are real (~0x3D8–0x400 bytes, double-buffered at
  0x80133AD0/0x8013BAD0) but contain ONLY the mixer/reverb set
  (02 CLEARBUFF, 04 LOADBUFF, 06 SAVEBUFF, 0A DMEMMOVE, 0B LOADADPCM(0x20),
  0C MIXER, 0D, 0E POLEF) recirculating DRAM delay-line buffers
  (0x104DB0/0x105080/0x105850/0x105C10/0x106610…).
- **Voice opcodes (01 ADPCM / 05 RESAMPLE / 08 SETBUFF / 09 SETVOL) are never
  submitted** across ~14k tasks, and the mixer's LOADBUFF source buffers are
  **permanently all-zero** (probed 1/s) → the CPU-side voice/music renderer
  never writes its output. The RSP mixer faithfully mixes silence.

Eliminated:
- Ucode bugs (runs clean; mixes what it's given).
- osSetTimer pacing (func_80026FA0 = osSetTimer confirmed, but its only caller
  is inside runtime-provided osContInit — no game callers).
- The audio-command handshake: overlay code sends to mq 0x800467C0 and BLOCKS
  on an ack (0x800467E0) — the intro advances, so the handshake completes.
  (NB: thread entry 0x80002CC4 pri 70 is a screen/fade manager — it calls
  osViSetYScale/osViBlack — not the music engine.)

Leads for the next session:
1. Thread entry **0x80016EDC (pri 80)** is the audio-system thread (did the
   osAiGetLength call; crashed on AI regs pre-shims via func_80017018). Its
   loop needs disassembly: find the voice-render call and what gates it
   (bank-loaded flag? sample-table pointer?).
2. **Event 5 (SI) is registered twice** (`mq=0x80060428 msg=0x1` then
   `mq=0x800482F0 msg=0x0` — second overwrites first in __osEventStateTab).
   If the audio system owns the first registration and something steals it,
   its DMA-completion/timing messages never arrive. Identify both registrants.
3. Bump the `rom_read` log cap (pi.cpp, currently 30) to check whether the
   music/sample streaming reads (0x200-byte chunks, rom ~0xE35000/0xCE9F00)
   continue past boot or stall after the first buffer fill.
