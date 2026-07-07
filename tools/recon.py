#!/usr/bin/env python3
"""Initial ROM recon for WCW/nWo Revenge, using the methods proven on World Tour
(docs/devlog.md there): jr-$ra density to find code regions, plus a direct
similarity comparison against the World Tour ROM to measure shared code.
"""
import sys, struct

REV = r"C:\Users\selki\depot\WcwRevengeRecomp\revenge.z64"
WT  = r"C:\Users\selki\depot\WcwNwoWorldTour\wcw.z64"

rev = open(REV, "rb").read()
wt  = open(WT, "rb").read()

def jr_density(rom, window=0x4000):
    """Count jr $ra (0x03E00008) per window; code windows score high."""
    out = []
    for base in range(0, len(rom), window):
        chunk = rom[base:base+window]
        n = 0
        for i in range(0, len(chunk) - 3, 4):
            if chunk[i:i+4] == b"\x03\xe0\x00\x08":
                n += 1
        out.append((base, n))
    return out

def regions(rom, thresh=8):
    dens = jr_density(rom)
    regs, start = [], None
    for base, n in dens:
        if n >= thresh and start is None:
            start = base
        elif n < thresh and start is not None:
            regs.append((start, base)); start = None
    if start is not None:
        regs.append((start, len(rom)))
    return regs

print("=== Revenge code regions (jr $ra density >= 8/16KB) ===")
for s, e in regions(rev):
    print(f"  0x{s:06X} - 0x{e:06X}  ({(e-s)//1024} KB)")

print("=== World Tour code regions (same method, sanity check) ===")
for s, e in regions(wt):
    print(f"  0x{s:06X} - 0x{e:06X}  ({(e-s)//1024} KB)")

# Boot-code similarity: compare 16-byte blocks at identical offsets in the first 64KB
print("=== identical 16-byte blocks at same offset, first 64KB from 0x1000 ===")
same = 0
total = 0
for off in range(0x1000, 0x11000, 16):
    total += 1
    if rev[off:off+16] == wt[off:off+16]:
        same += 1
print(f"  {same}/{total} blocks identical ({100*same//total}%)")

# Opcode-level similarity in the first 256KB of code (mask immediates: keep top 6+5+5 bits)
def opcode_sig(rom, start, count):
    sig = []
    for i in range(count):
        w = struct.unpack_from(">I", rom, start + i*4)[0]
        sig.append(w & 0xFFE00000)  # opcode + rs field only
    return sig

a = opcode_sig(rev, 0x1000, 0x40000//4)
b = opcode_sig(wt,  0x1000, 0x40000//4)
same = sum(1 for x, y in zip(a, b) if x == y)
print(f"=== opcode-field match in first 256KB of code: {100*same//len(a)}% ===")
