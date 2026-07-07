#!/usr/bin/env python3
"""Generate N64Recomp symbol TOML (syms/dump.toml) from splat output — Revenge.

Same approach as World Tour's generator (symbol-TOML mode; spimdisasm emits
`nonmatching <name>, <size>` + per-instruction `/* ROM VRAM WORD */` comments),
but Revenge has NO overlays — one contiguous main segment split across many
asm subsegment files by the code/data interleave. One [[section]] per asm file.

RENAME transfers libultra knowledge as it gets identified (start empty-ish;
see World Tour's tools/gen_symbols.py + disasm/libultra.md for the method)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASM = ROOT / "disasm" / "asm"
OUT = ROOT / "syms" / "dump.toml"

RENAME = {
    # host-collision rename, same as WT:
    "main": "game_main",

    # --- libultra: naming a function makes N64Recomp auto-ignore it (built-in set in
    #     N64Recomp/src/symbol_lists.cpp) so the runtime provides it. Evidence per
    #     function in disasm/libultra.md (WT's method).
    # game_main's first call (jal at 0x80000460). Sets __osFinalrom=1, SR |= CU1,
    # FCR31=0x01000800, PIF terminate-boot SI loop at 0x1FC007FC (the first-boot crash:
    # raw SI read via func_800275F0), copies exception-vector preamble (func_80025F30)
    # to 0x80000000/80/100/180, osClockRate*3/4, reads osResetType/osTvType/
    # osAppNMIBuffer, sets osViClock (NTSC 0x02E6D354/PAL/MPAL), AI DACRATE/BITRATE init.
    "func_800268A0": "osInitialize",
    # Threads (game_main's 2nd/3rd calls, WT's exact pattern; silent-hang boot proved
    # no host thread ever started). C8C0: fills OSThread ctx (SR=0xFF03, fpcsr=
    # 0x01000800, sp-0x10, ra=__osCleanupThread), state=1, pushes __osActiveQueue
    # (D_8003724C). CD20: state switch 8/1 → RUNNABLE, enqueues __osRunQueue
    # (D_80037248), dispatches if __osRunningThread (D_80037250) NULL.
    "func_8001C8C0": "osCreateThread",
    "func_8001CD20": "osStartThread",
    # Interrupts (mfc0/mtc0 $12 Status: B10 masks IE & returns old bit; B30 ORs it
    # back). Runtime shims exist (WT named its equivalents 80012160/80012180).
    # Removed from revenge.toml stubs when named.
    "func_80026B10": "__osDisableInt",
    "func_80026B30": "__osRestoreInt",
    # PI manager + cart init (2nd boot crash: game thread func_800004B8 →
    # 800255B0 → 80025750 raw PI-domain-reg read at 0xA4600014). 255B0 is
    # osCreatePiManager verbatim: __osPiDevMgr @ D_80037600, OS_EVENT_PI mesg
    # 0x22222222, pri juggle, __osDevMgrMain (func_80027B40) thread. Naming it
    # removes its single-caller raw-MMIO helper func_80025750 from the path.
    "func_800255B0": "osCreatePiManager",
    # 21AA0: guards CartRomHandle(D_8007E198).baseAddress==0xB0000000, reads ROM
    # header bus-config via func_800277E0 (osPiRawReadIo), unpacks latency/
    # pageSize/relDuration/pulse, links __osPiTable (D_8003761C).
    "func_80021AA0": "osCartRomInit",
    # Mesg/event/pri set (bodies verified, WT's exact evidence patterns):
    "func_8001C890": "osCreateMesgQueue",   # mtqueue/fullqueue = &__osThreadTail (D_80037240)
    "func_8001CBF0": "osSetEventMesg",      # __osEventStateTab (D_8007DF30)[e] = {mq,msg}
    "func_8001CC50": "osSetThreadPri",      # !t → __osRunningThread; dequeue/enqueue/yield
    "func_80026DB0": "osGetThreadPri",      # !t → __osRunningThread; return t->0x4
    # VI manager (3rd boot crash: raw VI_CURRENT read at 0xA4400010 in
    # func_800274D0 = __osViInit, single-called from 258C0's tail). 258C0 is
    # osCreateViManager verbatim: __osViDevMgr @ D_80037630, viEventQueue
    # D_80064A50 (5 msgs), retrace/counter mesgs typed 0xD/0xE, osSetEventMesg
    # events 7 (VI) + 3 (COUNTER), pri-254 thread entry func_80025A60 (viMgrMain).
    "func_800258C0": "osCreateViManager",
    # Message passing (4th boot crash: main game thread func_80000E0C →
    # 8001C990 NULL halfword write at __osRunningThread->state — ultramodern
    # doesn't populate the game's D_80037250; WT's thread-accessor class).
    # C990 blocks on validCount==0 (recv); CAC0 does the queue-full check
    # early (send) — WT's exact send/recv discriminator.
    "func_8001C990": "osRecvMesg",
    "func_8001CAC0": "osSendMesg",
    # VI set (5th boot iteration: no crash, all threads recv-blocked — the
    # retrace never arrived because the game's osViSetEvent wrote the game-side
    # __osViNext (D_80038894), invisible to the runtime VI manager. WT's exact
    # "vi.mq=0" root cause). Setters found by grepping __osViNext writers;
    # field offsets match WT's evidence one-for-one (msgq 0x10 / msg 0x14 /
    # retraceCount 0x2 / framep 0x4 / modep 0x8 / features 0xC / state 0x0).
    "func_80020DF0": "osViGetCurrentFramebuffer",  # __osViCurr(D_80038890)->framep
    "func_80020E30": "osViGetNextFramebuffer",     # __osViNext->framep
    "func_80020E70": "osViSetEvent",               # mq/msg/retraceCount into __osViNext
    "func_80020ED0": "osViSetMode",                # modep=a0, state=1
    "func_80020F20": "osViSetSpecialFeatures",     # feature bit set/clear, state|=8
    "func_80021090": "osViSetYScale",              # swc1 fa0 -> 0x24, state|=4
    "func_800210E0": "osViSwapBuffer",             # framep=a0, state|=0x10
    "func_80021130": "osViBlack",                  # state|=0x20 / &=~0x20
    # Clock (WT's frozen-clock lesson: osGetCount was stubbed there and timed
    # waits stalled; name BOTH so the runtime clock is self-consistent).
    "func_80026AF0": "osGetCount",   # mfc0 $9; removed from revenge.toml stubs
    "func_80026DD0": "osGetTime",    # count - __osBaseCounter(D_80065120) + __osCurrentTime(D_80070B20/24)
    # Interrupt mask (COP0 $12 + MI_INTR_MASK via __osIntTable D_8003B650);
    # used pervasively by the game's swap thread. Removed from stubs.
    "func_8001C740": "osSetIntMask",
    # 6th boot iteration (silent spin, ext-backlog +60/s with del/s=0): WT's
    # documented "overlay loader spins retrying osEPiStartDma because the game's
    # PI devmgr thread no longer drains the cmd queue once osCreatePiManager is
    # ultramodern's". Same fix set that took WT from boots→runs-game-code.
    "func_800219B0": "osEPiStartDma",   # __osPiDevMgr.active guard, EDMAREAD/WRITE 0xF/0x10, jam/send to osPiGetCmdQueue
    "func_80026E60": "osJamMesg",       # queue-full loop + insert at FRONT (first-1 mod count)
    "func_80022000": "osAiSetFrequency",# dacRate = osViClock(D_80038808)/freq, AI_DACRATE/BITRATE writes
    "func_80021230": "osContInit",      # one-time flag D_80037530, osGetTime vs 0x165A0BB PIF delay
    "func_80021190": "osContStartReadData", # __osSiGetAccess, __osContLastCmd D_8007BD30, pack/write/recv/read
    "func_80025810": "__osSiRawStartDma",   # SI_STATUS&3 busy, WB-DCache 64, SI PIF RD64B/WR64B — activates si.cpp PIF emu
    "func_800281F0": "__osSiDeviceBusy",    # lw SI_STATUS(0xA4800018) & 3 — frame 3 of the first-boot crash chain
    "func_8001CE80": "osVirtualToPhysical", # KSEG0/1 & 0x1FFFFFFF + __osProbeTLB(func_80026B50) fallback
    # AI set (7th boot iteration: game loop RUNS — overlays load, PI DMA
    # streams, retrace pumps; audio thread pri 80 entry func_80016EDC crashed
    # reading AI_STATUS 0xA450000C in func_80020A90).
    "func_80020A80": "osAiGetLength",     # lw AI_LEN (0xA4500004)
    "func_80020A90": "osAiGetStatus",     # lw AI_STATUS (0xA450000C)
    "func_80020AA0": "osAiSetNextBuffer", # even-samples 0x2000 adjust (D_80037520), __osAiDeviceBusy, AI_DRAM_ADDR+AI_LEN
    # SP task set (8th boot iteration: task thread func_80000EEC crashed
    # writing SP_STATUS 0xA4040010 in __osSpSetStatus via 80020B40 — the RSP
    # task submission path; WT: "osSpTaskLoad/StartGo → gfx tasks → RT64").
    "func_80020B40": "osSpTaskLoad",      # task copy to D_80062580, V2P on all task ptrs, DMEM DMA
    "func_80020D4C": "osSpTaskStartGo",   # __osSpDeviceBusy spin, __osSpSetStatus(0x125)
    "func_80020D80": "osSpTaskYield",     # __osSpSetStatus(0x400) = SET_SIG0
    "func_80020DA0": "osSpTaskYielded",   # status bit 0x80 -> OS_TASK_YIELDED flags
}

# Functions suppressed as symbols (continuation fragments merged into an earlier
# function by tools/recomp-loop3.py's backward-merge treatment).
SKIP = set()
_skip_file = Path(__file__).resolve().parent.parent / "syms" / "skip_functions.txt"
if _skip_file.exists():
    SKIP = {l.strip() for l in open(_skip_file) if l.strip()}

FUNC_RE = re.compile(r"^nonmatching (\S+), (0x[0-9A-Fa-f]+)")
GLABEL_RE = re.compile(r"^glabel (\S+)")
INSN_RE = re.compile(r"^\s*/\* ([0-9A-Fa-f]+) ([0-9A-Fa-f]{8}) ([0-9A-Fa-f]{8}) \*/")

def parse_file(path):
    """Return (rom_start, vram_start, rom_end, [(name, vram, size)])."""
    funcs = []
    pending_size = None
    pending_name = None
    first = None
    last = None
    for line in open(path, encoding="utf-8"):
        m = FUNC_RE.match(line)
        if m:
            pending_name, pending_size = m.group(1), int(m.group(2), 16)
            continue
        m = GLABEL_RE.match(line)
        if m and pending_name == m.group(1):
            funcs.append([pending_name, None, pending_size])
            continue
        m = INSN_RE.match(line)
        if m:
            rom, vram = int(m.group(1), 16), int(m.group(2), 16)
            if first is None:
                first = (rom, vram)
            last = (rom, vram)
            if funcs and funcs[-1][1] is None:
                funcs[-1][1] = vram
    if first is None:
        return None
    return first[0], first[1], last[0] + 4, [(n, v, s) for n, v, s in funcs if v is not None]

def main():
    sections = []
    for path in sorted(ASM.glob("*.s")):
        parsed = parse_file(path)
        if not parsed:
            continue
        rom, vram, rom_end, funcs = parsed
        if path.name == "1000.s":
            name = "entry"
            funcs = [("entrypoint", vram, 0x38)] if not funcs else funcs
        elif path.name == "3C770.s":
            name = "ovl_a"
        elif path.name == "834A0.s":
            name = "ovl_b"
        else:
            name = f"main_{rom:X}"
        sections.append((name, rom, vram, rom_end - rom, funcs))

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="\n") as f:
        f.write("# Autogenerated from splat disassembly by tools/gen_symbols.py\n")
        total = 0
        seen = {}
        for name, rom, vram, size, funcs in sections:
            f.write(f"\n[[section]]\nname = \"{name}\"\n")
            f.write(f"rom = 0x{rom:08X}\nvram = 0x{vram:08X}\nsize = 0x{size:X}\n\n")
            f.write("functions = [\n")
            for fn, fv, fs in funcs:
                if fn in SKIP:
                    continue
                fn = RENAME.get(fn, fn)
                # disambiguate names colliding across same-vram overlays (WT scheme)
                if fn in seen and seen[fn] != (name, fv):
                    fn = f"{fn}_{name}"
                seen[fn] = (name, fv)
                f.write(f"    {{ name = \"{fn}\", vram = 0x{fv:08X}, size = 0x{fs:X} }},\n")
                total += 1
            f.write("]\n")
    print(f"wrote {OUT}: {len(sections)} sections, {total} functions")

if __name__ == "__main__":
    main()
