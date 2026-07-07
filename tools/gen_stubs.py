#!/usr/bin/env python3
"""Regenerate syms/stub_candidates.txt (functions containing cop0/cache opcodes —
unrecompilable, runtime-provided) and rebuild revenge.toml's stubs block.
recomp-loop2.py appends further stubs discovered at recompile time."""
import re, struct, os
os.chdir(r"C:\Users\selki\depot\WcwRevengeRecomp")
rev = open("revenge.z64", "rb").read()
funcs = []
for line in open("syms/dump.toml"):
    m = re.search(r'\{ name = "([^"]+)", vram = (0x[0-9A-Fa-f]+), size = (0x[0-9A-Fa-f]+)', line)
    if m: funcs.append((m.group(1), int(m.group(2), 16), int(m.group(3), 16)))
special = []
for name, vram, size in funcs:
    rom = vram - 0x80000400 + 0x1000
    for off in range(rom, rom + size - 3, 4):
        w = struct.unpack_from(">I", rev, off)[0]
        if (w >> 26) in (0x10, 0x2F):
            special.append(name); break
with open("syms/stub_candidates.txt", "w", newline="\n") as f:
    for name in special:
        f.write(f'    "{name}",\n')
stubs = open("syms/stub_candidates.txt").read()
toml = open("revenge.toml").read()
toml = re.sub(r"stubs = \[\n.*?\]", "stubs = [\n" + stubs + "]", toml, flags=re.S)
open("revenge.toml", "w", newline="\n").write(toml)
print(f"{len(special)} stub candidates; revenge.toml updated")
