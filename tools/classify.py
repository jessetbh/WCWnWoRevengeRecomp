#!/usr/bin/env python3
"""Classify code vs data across the Revenge main segment at 256-byte granularity
using rabbitizer instruction validity, then emit splat subsegment boundaries."""
import struct, sys
sys.path.insert(0, r"C:\Users\selki\depot\WcwRevengeRecomp\disasm\.venv\Lib\site-packages")
import rabbitizer

rev = open(r"C:\Users\selki\depot\WcwRevengeRecomp\revenge.z64", "rb").read()
START, END = 0x1050, 0xD8000
WIN = 0x100

def win_score(off):
    """Fraction of words that decode as valid, plausible MIPS."""
    bad = 0
    n = WIN // 4
    for i in range(n):
        w = struct.unpack_from(">I", rev, off + i*4)[0]
        if w == 0:
            continue  # nops are fine either way
        insn = rabbitizer.Instruction(w)
        if not insn.isValid():
            bad += 1
        elif insn.isJumptableJump() or insn.isBranch() or insn.isJumpWithAddress():
            # branches/jumps with insane targets are data
            pass
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
    kinds.append((off, sc >= 0.90))

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
