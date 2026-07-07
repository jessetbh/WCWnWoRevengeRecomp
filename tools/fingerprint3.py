#!/usr/bin/env python3
"""Identification pass 3, three independent signals:
1. PREFIX matching (first 16 masked words, unique hit) — recovers handwritten-asm
   functions that differ only in tails/padding across libultra versions.
2. jal-frequency table for Revenge + WT — the most-called functions in any libultra
   game are stable (osSendMesg/osRecvMesg/cache ops), so rank correspondence is
   evidence even without byte similarity.
3. Unrecompilable-opcode scan — functions containing mfc0/mtc0/eret/tlb/cache ops
   (N64Recomp can't emit these) need stubbing/naming regardless of identity; find
   them directly."""
import re, struct
from collections import Counter

WT_ROM  = r"C:\Users\selki\depot\WcwNwoWorldTour\wcw.z64"
REV_ROM = r"C:\Users\selki\depot\WcwRevengeRecomp\revenge.z64"
WT_TOML = r"C:\Users\selki\depot\WcwNwoWorldTour\WCWSyms\dump.toml"
REV_CODE_START, REV_CODE_END = 0x1000, 0xD8000
REV_MAIN_VRAM = 0x80000400   # entrypoint; assume rom 0x1000 <-> this vram like WT

BRANCH_OPS = {0x01, 0x04, 0x05, 0x06, 0x07, 0x14, 0x15, 0x16, 0x17}

def mask_word(w):
    op = w >> 26
    if op in (2, 3): return w & 0xFC000000
    if op in BRANCH_OPS: return w
    if op == 0x0F:
        imm = w & 0xFFFF
        return w if 0xA000 <= imm <= 0xBFFF else w & 0xFFFF0000
    if op in (0x08, 0x09, 0x0D) and ((w >> 21) & 0x1F) != 29: return w & 0xFFFF0000
    if 0x20 <= op <= 0x3E and ((w >> 21) & 0x1F) == 1: return w & 0xFFFF0000
    return w

def mask_blob(data, start, end):
    out = bytearray()
    for off in range(start, end - 3, 4):
        out += struct.pack(">I", mask_word(struct.unpack_from(">I", data, off)[0]))
    return bytes(out)

wt  = open(WT_ROM, "rb").read()
rev = open(REV_ROM, "rb").read()

sections, funcs, cur = [], [], None
for line in open(WT_TOML):
    m = re.match(r'^rom = (0x[0-9A-Fa-f]+)', line)
    if m: cur = [int(m.group(1), 16), None]
    m = re.match(r'^vram = (0x[0-9A-Fa-f]+)', line)
    if m and cur and cur[1] is None:
        cur[1] = int(m.group(1), 16); sections.append(tuple(cur))
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

# --- 1. prefix matching -----------------------------------------------------
PREFIX_WORDS = 16
hay = mask_blob(rev, REV_CODE_START, REV_CODE_END)
print("=== prefix matches (first %d words, unique) ===" % PREFIX_WORDS)
prefix_found = {}
for name, vram, size in named:
    off = wt_rom_off(vram)
    if off is None or size < PREFIX_WORDS * 4: continue
    needle = mask_blob(wt, off, off + PREFIX_WORDS * 4)
    hits, i = [], hay.find(needle)
    while i != -1 and len(hits) <= 4:
        if i % 4 == 0: hits.append(REV_CODE_START + i)
        i = hay.find(needle, i + 4)
    if len(hits) == 1:
        rom = hits[0]
        prefix_found[name] = rom
        print(f"  {name:>28s}  rom=0x{rom:06X}  vram=0x{REV_MAIN_VRAM + rom - 0x1000:08X}")
print(f"  -> {len(prefix_found)} unique prefix matches")

# --- 2. jal frequency tables -------------------------------------------------
def jal_counts(rom, start, end, vrambase, romstart):
    c = Counter()
    for off in range(start, end - 3, 4):
        w = struct.unpack_from(">I", rom, off)[0]
        if (w >> 26) == 3:
            target = (w & 0x03FFFFFF) << 2 | 0x80000000
            c[target] += 1
    return c

print("\n=== top 15 jal targets: Revenge (assumed vram) vs World Tour (named) ===")
rc = jal_counts(rev, REV_CODE_START, REV_CODE_END, REV_MAIN_VRAM, 0x1000)
wc = jal_counts(wt, 0x1000, 0x2A9B0, 0x80000400, 0x1000)
wt_names = {v: n for n, v, s in funcs}
for (rv, rn), (wv, wn) in zip(rc.most_common(15), wc.most_common(15)):
    print(f"  REV 0x{rv:08X} x{rn:<5d}   WT 0x{wv:08X} x{wn:<5d} {wt_names.get(wv, '?')}")

# --- 3. unrecompilable-opcode scan -------------------------------------------
print("\n=== Revenge words with cop0/cache/eret/tlb (need stubs or runtime names) ===")
special_offs = []
for off in range(REV_CODE_START, REV_CODE_END - 3, 4):
    w = struct.unpack_from(">I", rev, off)[0]
    op = w >> 26
    if op == 0x10:  # COP0: mfc0/mtc0/eret/tlb*
        special_offs.append((off, w))
    elif op == 0x2F:  # cache
        special_offs.append((off, w))
groups = []
for off, w in special_offs:
    if groups and off - groups[-1][1] <= 0x200:
        groups[-1] = (groups[-1][0], off, groups[-1][2] + 1)
    else:
        groups.append((off, off, 1))
for s, e, n in groups:
    print(f"  rom 0x{s:06X}-0x{e:06X} ({n} words)  vram ~0x{REV_MAIN_VRAM + s - 0x1000:08X}")
