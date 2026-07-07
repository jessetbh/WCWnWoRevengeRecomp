# libultra identification (Revenge bring-up)

Evidence log for every `func_XXXX` → libultra RENAME in `tools/gen_symbols.py`,
mirroring World Tour's `disasm/libultra.md` method. Byte fingerprints do NOT
transfer from WT (newer libultra/IDO — see tools/fingerprint*.py, 3/46), so each
identification is re-derived from disassembly evidence and/or boot crash chains.

Mechanism (validated in WT): N64Recomp has built-in name sets
(`N64Recomp/src/symbol_lists.cpp`); naming a function with a libultra name makes
the recompiler skip emitting it and the runtime (librecomp/ultramodern) provides
it. WT's Stage-B correction applies here too: `MEM_W` does NOT trap MMIO, so any
driver doing raw register I/O (SI/PI/VI/AI) must eventually be named/ignored.

## Identified

### func_800268A0 = osInitialize (0x248 bytes, rom 0x274A0) — 2026-07-07
First identification, from the zero-RENAMEs first-boot crash
(`game_main → 800268A0 → 800275F0 → 800281F0`, access READ of a raw SI address).
Disassembly evidence (disasm/asm/1050.s @ 44197):
- **game_main's first call** (`jal func_800268A0` at vram 0x80000460) — WT's
  exact osInitialize evidence pattern (WT: func_800112D0).
- `sw 1 → D_8007DFB8` = `__osFinalrom = TRUE` (canonical first store).
- `func_80026B00`→`func_80026C20` with `| 0x20000000` = __osGetSR/__osSetSR
  enabling CU1 (FPU); `func_80026C10(0x01000800)` = __osSetFpcCsr.
- Busy-wait read loop on **0x1FC007FC** (PIF_RAM last word) via `func_800275F0`
  then write-back `| 8` via `func_80027680` = the PIF terminate-boot sequence
  (`__osSiRawReadIo`/`__osSiRawWriteIo`) — the exact site of the first-boot
  crash (raw SI MMIO through MEM_W indexes out of RDRAM).
- Copies 4×16 bytes from `func_80025F30` (= __osExceptionPreamble) to
  **0x80000000/0x80000080/0x80000100/0x80000180** — the four exception vectors —
  then `func_8001C7E0(0x80000000, 0x190)` / `func_8001C660(...)` =
  osWritebackDCache / osInvalICache over them.
- 64-bit `osClockRate * 3 / 4` computation (D_80038800/04, `func_80028860` =
  64-bit divide helper).
- `osResetType` (0x8000030C) check; on cold reset bzero(`osAppNMIBuffer`
  0x8000031C, 0x40) via `func_80021F60` (= bzero).
- `osTvType` (0x80000300) switch → osViClock = 0x02F5B2D2 (PAL) / 0x02E6025C
  (MPAL) / 0x02E6D354 (NTSC) stored to D_80038808.
- Writes AI_CONTROL/AI_DACRATE/AI_BITRATE (0xA4500008/10/14) init values.

### func_8001C8C0 = osCreateThread (0xD0, rom 0x1D4C0) — 2026-07-07
After naming osInitialize the boot stopped crashing but **hung silently** right
after boot DMA — WT's "each hang names the next function (thread set)" stage: no
host thread ever started. game_main's 2nd call:
`func_8001C8C0(&D_8003BAD0, 1, func_800004B8, arg, D_8003DC80, 8)` — the exact
osCreateThread(t, id, entry, arg, sp, pri) shape. Body evidence (1050.s):
- Fills OSThread context exactly like libultra: `ra = D_80026888`
  (= __osCleanupThread, sits directly before osInitialize at 0x800268A0),
  `sr = 0xFF03`, `rcp = 0x3F`, `fpcsr = 0x01000800`, `pc(0x11C) = entry`,
  64-bit `a0(0x38/3C) = arg`, 64-bit `sp(0xF0/F4) = sp - 0x10`.
- `state(0x10) = 1` (OS_STATE_STOPPED), `flags(0x12) = 0`, id at 0x14.
- Pushes onto `__osActiveQueue` (**D_8003724C**) under
  __osDisableInt/__osRestoreInt (func_80026B10/func_80026B30).

### func_8001CD20 = osStartThread (0x118, rom 0x1D920) — 2026-07-07
game_main's 3rd call, on the thread just created. Body is libultra
osStartThread verbatim:
- switch on `t->state`: 8 (WAITING) → state=2 (RUNNABLE) + enqueue
  `__osRunQueue` (**D_80037248**); 1 (STOPPED) → same if `t->queue` NULL or
  == &__osRunQueue, else re-enqueue via __osPopThread.
- `__osEnqueueThread` = **func_800266B4**, `__osPopThread` = **func_800266FC**.
- If `__osRunningThread` (**D_80037250**) is NULL → `__osDispatchThread`
  (**func_8002670C**, stays STUBBED — no librecomp shim, WT precedent); else
  priority compare + `__osEnqueueAndYield` (**func_800265AC**, also stubbed).
- Whole body wrapped in __osDisableInt/__osRestoreInt.

### func_80026B10 = __osDisableInt (0x20) / func_80026B30 = __osRestoreInt (0x1C) — 2026-07-07
Definitive one-look bodies: B10 `mfc0 $12` → clear IE (& ~1) → `mtc0` → return
old IE bit; B30 `mfc0 $12` → OR a0 → `mtc0`. Same pair WT named
(80012160/80012180). Removed from revenge.toml stubs when named (they were in
the cop0 opcode-scan stub list).

### func_800255B0 = osCreatePiManager (0x1A0, rom 0x261B0) — 2026-07-07
2nd boot crash (after thread set named): game thread `func_800004B8` →
`func_800255B0` → `func_80025750`+0x40, access READ rdram+0x24600014 = raw MMIO
read of **0xA4600014 (PI_BSD_DOM1_LAT_REG)**. Body is osCreatePiManager
verbatim (sig `(pri, cmdQ, cmdBuf, cmdMsgCnt)`):
- guard on `__osPiDevMgr.active` (**D_80037600**); osCreateMesgQueue(cmdQ,...)
  + piEventQueue (D_80063870/D_80063888, 1 msg).
- `osSetEventMesg(8 /*OS_EVENT_PI*/, &piEventQueue, 0x22222222)` — the
  definitive PI magic constant.
- osGetThreadPri(NULL) / raise / restore osSetThreadPri dance.
- Builds __osPiDevMgr {active=1, thread=&piThread D_800626C0, cmdQueue,
  evtQueue, dma=func_80027880, edma=func_80027970}, stack D_80073E98, creates +
  starts DevMgr thread entry **func_80027B40 = __osDevMgrMain**.
- func_80025750 (single caller = here) reads all 8 PI BSD DOM1/DOM2 regs into
  two OSPiHandle param blocks (D_8007DEBD.., D_80070AA5..) — internal PI-init
  helper, no shim; naming the manager removes it from the boot path.

### func_80021AA0 = osCartRomInit (0xD4, rom 0x226A0) — 2026-07-07
Game thread's 2nd call; return value stored as the game's cart handle
(D_8003DD98). Body:
- Guard: if CartRomHandle.baseAddress (**D_8007E1A4**) == 0xB0000000 return
  &CartRomHandle (**D_8007E198**).
- `func_800277E0(0, &word)` = **osPiRawReadIo** (raw PI MMIO; same fn used by
  osInitialize to read header offset 4 for osClockRate) reads the ROM-header
  PI bus-config word; unpacks latency/pageSize/relDuration/pulse bytes into the
  handle; domain=0.
- bzero(handle+8, 0x60) via func_80021F60 (bzero, 2nd sighting).
- Links handle into `__osPiTable` (**D_8003761C**) under int disable/restore.

### Batch (bodies verified individually) — 2026-07-07
- **func_8001C890 = osCreateMesgQueue** (0x24): mq->mtqueue = mq->fullqueue =
  &__osThreadTail (**D_80037240**), validCount=first=0, msgCount=a2, msg=a1 —
  WT's exact evidence (its 80011AE0).
- **func_8001CBF0 = osSetEventMesg** (0x5C): `__osEventStateTab`
  (**D_8007DF30**)[event] = {mq, msg} under __osDisableInt/__osRestoreInt.
- **func_8001CC50 = osSetThreadPri** (0xC8): `if(!t) t=__osRunningThread
  (D_80037250)`; if pri changed and t not running → __osDequeueThread
  (**func_8001CE40**) + __osEnqueueThread; then head-of-runqueue priority
  compare + yield. WT's 80011B10 pattern.
- **func_80026DB0 = osGetThreadPri** (0x18): `if(!a0) a0=__osRunningThread;
  return a0->0x4`. WT's 8001D940 pattern.

### func_800258C0 = osCreateViManager (0x1A0, rom 0x264C0) — 2026-07-07
3rd boot crash: `func_800004B8 → func_80000AF0 → func_800258C0 →
func_800274D0`+0x1A4, access READ rdram+0x24400010 = **0xA4400010
(VI_CURRENT_REG)**. Boot log first shows the runtime shims firing:
`osSetEventMesg event=7 (VI) / event=3 (COUNTER)` into the same mq 0x80064A50,
then `thread id=0 entry=0x80025A60 pri=254` (OS_PRIORITY_VIMGR). Body:
- guard `__osViDevMgr.active` (**D_80037630**); `func_80027040` =
  __osTimerServicesInit (internal, dead once manager is runtime-provided).
- viEventQueue **D_80064A50** / buf D_80064A68 / 5 msgs; retrace + counter
  message blocks typed **0xD / 0xE** (OS_SC-style event msgs) at
  D_80064A80/D_80064A98.
- osSetEventMesg(7, mq, &retraceMsg); osSetEventMesg(3, mq, &counterMsg).
- osGetThreadPri/osSetThreadPri raise dance; creates + starts VI thread
  (**D_80063898**, id 0, entry **func_80025A60 = viMgrMain**, restores pri).
- tail calls **func_800274D0 = __osViInit** (reads/writes raw VI regs incl.
  VI_CURRENT — the crash site; its only caller is this function, so naming the
  manager removes it). Game called from func_80000AF0 (game-side init helper
  creating the main-thread world, itself called by the boot thread).

### func_8001C990 = osRecvMesg / func_8001CAC0 = osSendMesg — 2026-07-07
4th boot crash: main game thread (id=4, entry func_80000E0C, pri 120 — created
after it registered PRENMI/SP/DP event mesgs) → `func_8001C990`+0x152, access
WRITE decoding to a **NULL halfword write at offset 0x10^2** = `sh 8 →
__osRunningThread(D_80037250)->state` — ultramodern never populates the game's
__osRunningThread (WT's documented thread-accessor NULL-deref class).
- **C990 = osRecvMesg** (0x124): `while (mq->validCount==0) { if (flags==
  NOBLOCK) return -1; state=WAITING; __osEnqueueAndYield(&mq->mtqueue); }`,
  `*msg = mq->msg[mq->first]`, `first=(first+1)%msgCount`, validCount--, pops
  fullqueue waiter + osStartThread.
- **CAC0 = osSendMesg** (0x130): queue-FULL check first (`validCount <
  msgCount`) — WT's send/recv discriminator — block loop when full
  (flags==OS_MESG_BLOCK), `msg[(first+validCount)%msgCount] = msg`,
  validCount++, wakes mtqueue waiter via __osPopThread/osStartThread.

### VI set + clock + int mask (5th boot iteration: silent hang) — 2026-07-07
After the mesg pair was named the boot stopped crashing entirely: the game
created its scheduler threads (pri 110/100 entries func_80000EEC/func_80001034)
and game-logic thread (id=6 entry func_80013108, which runs game init then the
overlay dispatch loop via func_8000082C) — then everything recv-blocked for
60s. Diagnosis = WT's documented "vi.mq=0" root cause: init (func_80000AF0 @
0x80000C20) calls `func_80020E70(mq=0x8003DE70, msg=0x29A, count)` and the main
thread recv-blocks on that same queue — but recompiled func_80020E70 wrote the
GAME's __osViNext (D_80038894), which the runtime VI manager never reads, so no
retrace message ever arrives.

Found the whole osVi* family by grepping __osViNext(D_80038894) writers
(cluster 0x80020DF0–0x80021190; __osViCurr = **D_80038890**, set by
__osViInit func_800274D0):
- **80020DF0 = osViGetCurrentFramebuffer**: int-off read `__osViCurr->0x4`.
- **80020E30 = osViGetNextFramebuffer**: same via __osViNext.
- **80020E70 = osViSetEvent**: `__osViNext->{0x10=mq, 0x14=msg}`, `sh a2,0x2`
  (retraceCount) — WT's 80012650 pattern verbatim.
- **80020ED0 = osViSetMode**: `->0x8 = mode`, `state(0x0)=1`, comRegs from
  mode->0x4 into 0xC.
- **80020F20 = osViSetSpecialFeatures**: OS_VI_* bit set/clears on ->0xC,
  `state |= 8`.
- **80021090 = osViSetYScale**: `swc1 $fa0 -> 0x24`, `state |= 4`.
- **800210E0 = osViSwapBuffer**: `->0x4 = framebuffer`, `state |= 0x10` — WT's
  80012860 pattern.
- **80021130 = osViBlack**: `state |= 0x20` / `&= ~0x20` on arg&0xFF.
All shims confirmed present (librecomp/ultramodern *_recomp exports, incl.
osViSetYScale).

Also banked in the same pass (bodies verified):
- **func_80026AF0 = osGetCount** (`mfc0 $v0, $9`) — was stubbed; WT's
  frozen-clock lesson says stubbing it stalls every timed wait. Removed from
  revenge.toml stubs.
- **func_80026DD0 = osGetTime**: int-off; osGetCount − __osBaseCounter
  (**D_80065120**), 64-bit add __osCurrentTime (**D_80070B20/24**) — WT's
  80023800 pattern.
- **func_8001C740 = osSetIntMask** (0xA0, handwritten): COP0 $12 Status
  FF01 bits + MI_INTR_MASK_REG via __osIntTable (**D_8003B650**), global mask
  word **D_80038810** (= __OSGlobalIntMask) — WT's 800126C0. Was stubbed
  (cop0 scan); removed. Used pervasively by the game's swap thread
  (func_80001034) as critical-section guard, so stubbing it was harmless but
  naming keeps semantics.

Related not-yet-named (game scheduler层, watch in later iterations):
- func_80020D4C: spins on __osSpDeviceBusy (func_80027360) then
  __osSpSetStatus(0x125) — this is __osSpDeviceIdle+start pattern (SP task
  kick). func_80020D80: __osSpSetStatus(0x400). Both touch SP MMIO but are
  called by the game's task threads — expect these to surface once graphics
  tasks start (osSpTask* equivalents; WT handled via task-queue plumbing).
- func_80021190: SI-access guarded recv (func_80027744/func_800277B0 =
  __osSiGetAccess/__osSiRelAccess candidates; func_80025810 likely
  __osSiRawStartDma caller = osSiRawStartDma path) — controller read path.
- func_80021230: osGetTime consumer comparing against 0x165A0BB — PIF/PFS
  delay logic (osPfs* or motor).

### PI DMA / audio / controller set (6th iteration: retrace flows, still spins) — 2026-07-07
With the VI set named the retrace registration went live (`[wcw][osViSetEvent]
mq=0x8003DE70 msg=0x29A rc=1`) and the first recv's completed, but
`WCW_HEALTH_LOG` showed the smoking gun: external backlog +60/s with
**del/s=0** — a game thread spinning without ever calling a mesg function,
starving delivery under the cooperative scheduler. WT's devlog documents this
exact stage: *the overlay loader spun retrying osEPiStartDma because the game's
PI devmgr thread no longer drains the cmd queue once osCreatePiManager is
ultramodern's*. Named WT's exact fix set:
- **func_800219B0 = osEPiStartDma** (0x94): `if (!__osPiDevMgr.active
  (D_80037600)) return -1`; `mb->hdr.type = 0xF/0x10` (EDMAREAD/EDMAWRITE) on
  direction; `mb->piHandle(0x14) = a0`; `hdr.pri==1` → osJamMesg else
  osSendMesg into `osPiGetCmdQueue()` (**func_80027950**, reads D_80037608),
  NOBLOCK. Called by the overlay loader func_80000700 before its DMA-done recv.
- **func_80026E60 = osJamMesg** (0x134): queue-full wait then insert at FRONT.
- **func_80022000 = osAiSetFrequency** (0x118): float dacRate = osViClock
  (D_80038808)/freq, min-bitrate clamp, AI_DACRATE/AI_BITRATE raw writes.
- **func_80021230 = osContInit** (0x19C): one-time flag **D_80037530**
  (__osContInitialized), busy-waits osGetTime < **0x165A0BB** (~500ms PIF boot
  delay — WT's exact evidence constant), queue + __osSiRawStartDma + recv
  init-data sequence via func_80021480 (__osContGetInitData).
- **func_80021190 = osContStartReadData** (0x80): __osSiGetAccess
  (**func_80027744**) / __osSiRelAccess (**func_800277B0**); if __osContLastCmd
  (**D_8007BD30**) stale → pack + __osSiRawStartDma(WRITE, __osContPifRam
  **D_8006A260**) + recv; then __osSiRawStartDma(READ), clear lastCmd.
- **func_80025810 = __osSiRawStartDma** (0xA4): SI_STATUS&3 busy check,
  osWritebackDCache 64B on write, osVirtualToPhysical, SI_DRAM_ADDR +
  SI_PIF_ADDR_RD64B/WR64B kick. Naming activates the librecomp si.cpp fork's
  64-byte PIF/joybus emulation (WT's controller solution — shims latch the PIF
  block and run joybus against host input).
- **func_800281F0 = __osSiDeviceBusy** (0x18): `lw SI_STATUS; andi 3; sltu` —
  this was frame 3 of the very first boot crash chain.
- **func_8001CE80 = osVirtualToPhysical** (0x54): KSEG0/KSEG1 & 0x1FFFFFFF,
  TLB fallback via **func_80026B50 = __osProbeTLB** (stays stubbed).
- **func_80021540 = osContSetCh** candidate (clamps to 4 → __osMaxControllers
  D_80070A98, sets lastCmd 0xFE) — NOT named yet; check shim when it surfaces.

### AI set (7th iteration: GAME LOOP RUNS; audio thread crash) — 2026-07-07
The osEPiStartDma batch unstuck everything: overlays load (rom_read#1 at the
overlay descriptor area), PI DMA streams game data (0x200-byte reads from rom
0xCE9F00+), retrace messages consumed every frame, audio thread spawned (id=3,
entry func_80016EDC, pri 80 — plus an earlier pri-70 thread entry 0x80002CC4).
Crash: audio thread → func_80017018 → **func_80020A90**+0x8, access READ
rdram+0x2450000C = **0xA450000C (AI_STATUS_REG)**.
- **func_80020A80 = osAiGetLength** (0x10): `lw AI_LEN_REG (0xA4500004)`.
- **func_80020A90 = osAiGetStatus** (0x10): `lw AI_STATUS_REG (0xA450000C)`.
- **func_80020AA0 = osAiSetNextBuffer** (0x94): libultra's even-samples quirk
  verbatim (static flag **D_80037520**: if set, dramAddr -= 0x2000; set flag
  when (addr+len)&0x1FFF == 0), __osAiDeviceBusy (func_80027340) guard,
  osVirtualToPhysical, `AI_DRAM_ADDR = phys; AI_LEN = len`.
All three shims confirmed in the runtime.

### SP task set (8th iteration: RSP task submission) — 2026-07-07
Audio thread cleared AI init (osAiGetLength shim log fired), registered SI
event queues (event=5 ×2). Task-scheduler thread (entry func_80000EEC) crashed
next: → **func_80020B40**+0x315 → func_80027390 (__osSpSetStatus) WRITE at
rdram+0x24040010 = **0xA4040010 (SP_STATUS_REG)** — RSP task submission.
- **func_80020B40 = osSpTaskLoad** (0x20C): copies OSTask into static
  **D_80062580**, osVirtualToPhysical on each task pointer (ucode/ucode_data/
  dram_stack/output_buff/output_buff_size/yield_data/data at D_80062590..B8),
  DMAs task block to DMEM via __osSpRawStartDma (func_800273D0), __osSpSetPc.
- **func_80020D4C = osSpTaskStartGo** (0x2C): spins __osSpDeviceBusy
  (func_80027360), then __osSpSetStatus(**0x125** = CLR_HALT|CLR_SSTEP|
  SET_INTR_BREAK).
- **func_80020D80 = osSpTaskYield** (0x1C): __osSpSetStatus(**0x400** =
  SET_SIG0, the yield-request signal).
- **func_80020DA0 = osSpTaskYielded** (0x4C): __osSpGetStatus (func_80027380),
  checks SIG0 (0x80)/bit8, updates task->flags OS_TASK_YIELDED.
All four shims confirmed. Related internal SP raw layer (NOT named — dead once
the task set is runtime-provided): func_80027360=__osSpDeviceBusy,
func_80027380=__osSpGetStatus, func_80027390=__osSpSetStatus,
func_800273A0=__osSpSetPc, func_800273D0=__osSpRawStartDma,
func_80027340=__osAiDeviceBusy.

Byproduct candidates banked for later (do NOT name yet — verify each when it
surfaces in a crash chain; some are internal and have no librecomp shim):
- func_80026B00/func_80026C20 ≈ __osGetSR/__osSetSR (internal, no shim — stub if needed)
- func_80026C10 ≈ __osSetFpcCsr (HAS a shim in WT's bounded list)
- func_800275F0/func_80027680 ≈ __osSiRawReadIo/__osSiRawWriteIo
- func_80025F30 ≈ __osExceptionPreamble (handwritten; stub territory)
- func_8001C7E0 ≈ osWritebackDCache, func_8001C660 ≈ osInvalICache
- func_80021F60 ≈ bzero
- func_80028860 ≈ 64-bit div helper (libgcc-ish, internal)
