#!/usr/bin/env python3
"""Classify code vs data across the Revenge main segment at 256-byte granularity
using rabbitizer instruction validity, then emit splat subsegment boundaries."""
import struct, sys
sys.path.insert(0, r"C:\Users\selki\depot\WcwRevengeRecomp\disasm\.venv\Lib\site-packages")
import rabbitizer

rev = open(r"C:\Users\selki\depot\WcwRevengeRecomp\revenge.z64", "rb").read()
START, END = 0x1050, 0xD8000
WIN = 0x100

BRANCH_OPS = {0x01, 0x04, 0x05, 0x06, 0x07, 0x14, 0x15, 0x16, 0x17}

def win_score(off):
    """Fraction of words that decode as valid, plausible MIPS. Data that decodes as
    instructions is caught by target sanity: j/jal must land in the loaded segment,
    branches must stay local (real IDO branches are short; float/vertex data words
    produce wild displacements)."""
    bad = 0
    n = WIN // 4
    for i in range(n):
        w = struct.unpack_from(">I", rev, off + i*4)[0]
        if w == 0:
            continue  # nops are fine either way
        insn = rabbitizer.Instruction(w)
        if not insn.isValid():
            bad += 1
            continue
        op = w >> 26
        if op in (2, 3):  # j/jal
            target = ((w & 0x03FFFFFF) << 2) | 0x80000000
            if not (0x80000400 <= target < 0x800D8000):
                bad += 1
        elif op in BRANCH_OPS or (op == 1):  # branches: displacement must be local
            disp = w & 0xFFFF
            if disp >= 0x8000:
                disp -= 0x10000
            if abs(disp) > 0x2000:            # +/-32KB instr = 8K words; IDO stays far under
                bad += 1
        elif op == 0x11:                      # COP1: rs field must be a real fmt/branch
            rs = (w >> 21) & 0x1F
            if rs not in (0, 2, 4, 6, 8, 0x10, 0x11, 0x14, 0x15):
                bad += 1
    return 1.0 - bad / n

wins = []
off = START & ~0xFF
while off < END:
    wins.append((off, win_score(off)))
    off += WIN

# data = runs of windows scoring < 0.90, at least 2 windows long
segs = []          # (start, is_code)
cur_kind = True
run_start = START
pending = []
kinds = []
for off, sc in wins:
    kinds.append((off, sc >= 0.95))

# smooth: single-window flips get absorbed
sm = []
for i, (off, k) in enumerate(kinds):
    prevk = kinds[i-1][1] if i > 0 else k
    nextk = kinds[i+1][1] if i+1 < len(kinds) else k
    sm.append((off, prevk if (k != prevk and k != nextk) else k))

bounds = []
cur = sm[0][1]
for off, k in sm[1:]:
    if k != cur:
        bounds.append((off, k))
        cur = k

print(f"# {len(bounds)+1} runs; subsegments for revenge.yaml:")
print(f"      - [0x1050, asm]")
for off, becomes_code in bounds:
    print(f"      - [0x{off:X}, {'asm' if becomes_code else 'data'}]")
print(f"      - [0xD8000, data]")
