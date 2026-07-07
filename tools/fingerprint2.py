#!/usr/bin/env python3
"""Looser structural fingerprinting, level-based:
L1: mask link-address fields only (previous attempt — near-total miss: newer
    libultra/IDO in Revenge changes codegen slightly).
L2: keep opcode+rs+rt+rd skeleton, keep branch displacements and hardware-segment
    lui values (0xA0xx-0xBFxx — MMIO anchors), mask all other immediates.
L3: opcode skeleton only (op field; for SPECIAL also funct), branches keep offsets.
A function 'matches' at the loosest level that yields exactly one hit."""
import re, struct

WT_ROM  = r"C:\Users\selki\depot\WcwNwoWorldTour\wcw.z64"
REV_ROM = r"C:\Users\selki\depot\WcwRevengeRecomp\revenge.z64"
WT_TOML = r"C:\Users\selki\depot\WcwNwoWorldTour\WCWSyms\dump.toml"
REV_CODE_START, REV_CODE_END = 0x1000, 0xD8000

BRANCH_OPS = {0x01, 0x04, 0x05, 0x06, 0x07, 0x14, 0x15, 0x16, 0x17}

def mask_word(w, level):
    op = w >> 26
    if op in (2, 3):
        return w & 0xFC000000
    if op in BRANCH_OPS:
        return w                                   # keep branch structure at all levels
    if op == 0:                                    # SPECIAL
        return w if level < 3 else (w & 0xFC00003F)
    if op == 0x0F:                                 # lui
        imm = w & 0xFFFF
        if 0xA000 <= imm <= 0xBFFF:                # MMIO/uncached segment: keep (anchor!)
            return w
        return w & 0xFFFF0000
    if level >= 2:
        return w & 0xFFFF0000 if op != 0x0F else w
    return w

def mask_blob(data, start, end, level):
    out = bytearray()
    for off in range(start, end - 3, 4):
        w = struct.unpack_from(">I", data, off)[0]
        out += struct.pack(">I", mask_word(w, level))
    return bytes(out)

wt  = open(WT_ROM, "rb").read()
rev = open(REV_ROM, "rb").read()

sections, funcs, cur = [], [], None
for line in open(WT_TOML):
    m = re.match(r'^rom = (0x[0-9A-Fa-f]+)', line)
    if m: cur = [int(m.group(1), 16), None]
    m = re.match(r'^vram = (0x[0-9A-Fa-f]+)', line)
    if m and cur and cur[1] is None:
        cur[1] = int(m.group(1), 16); sections.append(tuple(cur));
    m = re.search(r'\{ name = "([^"]+)", vram = (0x[0-9A-Fa-f]+), size = (0x[0-9A-Fa-f]+)', line)
    if m: funcs.append((m.group(1), int(m.group(2), 16), int(m.group(3), 16)))

def wt_rom_off(vram):
    best = None
    for rom, svram in sections:
        if svram <= vram and (best is None or svram > best[1]):
            best = (rom, svram)
    return best[0] + (vram - best[1]) if best else None

named = [(n, v, s) for (n, v, s) in funcs
         if not n.startswith("func_") and v < 0x80090000 and s >= 0x20]

hays = {lvl: mask_blob(rev, REV_CODE_START, REV_CODE_END, lvl) for lvl in (1, 2, 3)}

results = {}
for name, vram, size in named:
    off = wt_rom_off(vram)
    if off is None: continue
    for lvl in (1, 2, 3):
        needle = mask_blob(wt, off, off + size, lvl)
        hits, i = [], hays[lvl].find(needle)
        while i != -1 and len(hits) <= 8:
            if i % 4 == 0: hits.append(REV_CODE_START + i)
            i = hays[lvl].find(needle, i + 4)
        if len(hits) == 1:
            results[name] = (lvl, hits[0], size); break
        if len(hits) > 1 and lvl == 3:
            results[name] = (-len(hits), None, size)

print(f"{'function':>28s}  result")
found = 0
for name, vram, size in named:
    r = results.get(name)
    if r and r[1] is not None:
        lvl, rom, _ = r
        found += 1
        print(f"{name:>28s}  L{lvl} rom=0x{rom:06X} vram=0x{0x80000400 + rom - 0x1000:08X}")
    elif r:
        print(f"{name:>28s}  ambiguous ({-r[0]}+ hits at L3)")
    else:
        print(f"{name:>28s}  NOT FOUND")
print(f"\nfound: {found}/{len(named)}")
