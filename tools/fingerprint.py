#!/usr/bin/env python3
"""Fingerprint World Tour's identified (named) functions inside the Revenge ROM.

Method: take each named function's MIPS words from the WT ROM, mask relocation-
dependent fields (jal/j targets, lui immediates, address-forming addiu/ori
immediates, $at-relative load/store offsets), apply the SAME per-word masking to
the whole Revenge code region, then find the masked needle in the masked haystack.
Branch offsets, register allocation, and struct/stack offsets are kept, so a match
is the same compiled function modulo link addresses. Unique matches bootstrap
Revenge's RENAME map without redoing the libultra identification."""
import re, struct, sys

WT_ROM  = r"C:\Users\selki\depot\WcwNwoWorldTour\wcw.z64"
REV_ROM = r"C:\Users\selki\depot\WcwRevengeRecomp\revenge.z64"
WT_TOML = r"C:\Users\selki\depot\WcwNwoWorldTour\WCWSyms\dump.toml"

REV_CODE_START, REV_CODE_END = 0x1000, 0xD8000   # from tools/recon.py

def mask_word(w):
    op = w >> 26
    rs = (w >> 21) & 0x1F
    if op in (2, 3):                    # j / jal: target is link-address-dependent
        return w & 0xFC000000
    if op == 0x0F:                      # lui: HI16 reloc
        return w & 0xFFFF0000
    if op in (0x08, 0x09, 0x0D):        # addi/addiu/ori: LO16 reloc unless stack math
        if rs != 29:
            return w & 0xFFFF0000
        return w
    if 0x20 <= op <= 0x3E:              # loads/stores: LO16 reloc when $at-based
        if rs == 1:
            return w & 0xFFFF0000
        return w
    return w

def mask_blob(data, start, end):
    out = bytearray()
    for off in range(start, end - 3, 4):
        w = struct.unpack_from(">I", data, off)[0]
        out += struct.pack(">I", mask_word(w))
    return bytes(out)

wt  = open(WT_ROM, "rb").read()
rev = open(REV_ROM, "rb").read()

# Parse sections + functions from dump.toml
sections = []   # (rom, vram, size)
funcs = []      # (name, vram, size)
cur = None
for line in open(WT_TOML):
    m = re.match(r'^rom = (0x[0-9A-Fa-f]+)', line)
    if m: cur = [int(m.group(1), 16), None]
    m = re.match(r'^vram = (0x[0-9A-Fa-f]+)', line)
    if m and cur and cur[1] is None:
        cur[1] = int(m.group(1), 16); sections.append(tuple(cur))
    m = re.search(r'\{ name = "([^"]+)", vram = (0x[0-9A-Fa-f]+), size = (0x[0-9A-Fa-f]+)', line)
    if m:
        funcs.append((m.group(1), int(m.group(2), 16), int(m.group(3), 16)))

def wt_rom_off(vram):
    best = None
    for rom, svram in sections:
        if svram <= vram and (best is None or svram > best[1]):
            best = (rom, svram)
    return best[0] + (vram - best[1]) if best else None

named = [(n, v, s) for (n, v, s) in funcs
         if not n.startswith("func_") and v < 0x80090000 and s >= 0x20]

hay = mask_blob(rev, REV_CODE_START, REV_CODE_END)

print(f"named main-segment functions to fingerprint: {len(named)}")
unique, multi, none = [], [], []
for name, vram, size in named:
    off = wt_rom_off(vram)
    if off is None:
        none.append(name); continue
    needle = mask_blob(wt, off, off + size)
    hits = []
    i = hay.find(needle)
    while i != -1:
        if i % 4 == 0:
            hits.append(REV_CODE_START + i)
        i = hay.find(needle, i + 4)
        if len(hits) > 8: break
    if len(hits) == 1:
        rev_rom = hits[0]
        rev_vram = 0x80000400 + (rev_rom - 0x1000)   # assume same main-segment mapping
        unique.append((name, rev_rom, rev_vram, size))
    elif hits:
        multi.append((name, len(hits)))
    else:
        none.append(name)

print(f"unique matches: {len(unique)}   ambiguous: {len(multi)}   not found: {len(none)}")
print("\n--- unique (name, revenge_rom, revenge_vram_assuming_wt_mapping, size) ---")
for name, rom, vram, size in sorted(unique, key=lambda x: x[1]):
    print(f"  {name:>28s}  rom=0x{rom:06X}  vram=0x{vram:08X}  size=0x{size:X}")
if multi:
    print("\n--- ambiguous ---")
    for name, n in multi: print(f"  {name}: {n} hits")
if none:
    print("\n--- not found ---")
    for name in none: print(f"  {name}")

# Audio ucode: raw byte search for WT's aspMain text (rom 0x2A850, len 0xE20)
asp = wt[0x2A850:0x2A850+0xE20]
i = rev.find(asp)
print(f"\naspMain audio ucode text in Revenge: {'rom=0x%X' % i if i != -1 else 'NOT FOUND byte-identical'}")
