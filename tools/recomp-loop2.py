#!/usr/bin/env python3
"""Smarter recompile loop. N64Recomp fails on functions whose IDO shared-epilogue
tails were carved off as separate functions (j past own end). Treatment: extend
the failing function's size (splat symbol_addrs size: attribute) to absorb the
tail blocks, drop any conflicting function-start entries inside the new range,
re-split, regenerate, retry."""
import re, subprocess, glob, sys, os

ROOT = r"C:\Users\selki\depot\WcwRevengeRecomp"
os.chdir(ROOT)
PY = os.path.join("disasm", ".venv", "Scripts", "python.exe")

def run_recomp():
    p = subprocess.run(["./N64Recomp.exe", "revenge.toml"], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr

def load_funcs():
    funcs = {}
    for line in open("syms/dump.toml"):
        m = re.search(r'\{ name = "(\S+)", vram = (0x[0-9A-Fa-f]+), size = (0x[0-9A-Fa-f]+)', line)
        if m:
            funcs[m.group(1)] = (int(m.group(2), 16), int(m.group(3), 16))
    return funcs

def find_j_targets(name):
    """All `j <target>` vrams inside function `name` in the splat asm."""
    targets = []
    for f in glob.glob("disasm/asm/*.s"):
        txt = open(f, encoding="utf-8").read()
        m = re.search(rf"^glabel {name}\n(.*?)(?:^endlabel|\Z)", txt, re.S | re.M)
        if not m:
            continue
        for jm in re.finditer(r'\bj\s+(?:func_|\.L)?([0-9A-Fa-f]{8})', m.group(1)):
            targets.append(int(jm.group(1), 16))
        break
    return targets

def resplit():
    subprocess.run([PY, "-m", "splat", "split", "revenge.yaml"], cwd="disasm",
                   capture_output=True)
    subprocess.run([sys.executable, "tools/gen_symbols.py"], capture_output=True)

for it in range(1, 41):
    code, out = run_recomp()
    if code == 0:
        print(f"=== CLEAN RECOMPILE after {it} iteration(s) ===")
        n = len(glob.glob("RecompiledFuncs/*.c"))
        print(f"RecompiledFuncs: {n} files")
        sys.exit(0)
    m = re.search(r"Error recompiling (\S+)", out)
    if not m:
        print("=== unrecognized failure ==="); print(out[-2000:]); sys.exit(1)
    fail = m.group(1)
    funcs = load_funcs()
    if fail not in funcs:
        print(f"=== failing fn {fail} not in dump.toml ==="); sys.exit(1)
    fvram, fsize = funcs[fail]
    ext_targets = [t for t in find_j_targets(fail) if not (fvram <= t < fvram + fsize)]
    if not ext_targets:
        print(f"=== {fail}: no external j-targets; different failure class ===")
        print(out[-1500:]); sys.exit(1)
    span_end = fvram + fsize
    for t in ext_targets:
        # absorb the target's whole function if known, else a small window
        end = t + 0x40
        for n2, (v2, s2) in funcs.items():
            if v2 <= t < v2 + s2:
                end = v2 + s2
                break
        span_end = max(span_end, end)
    new_size = span_end - fvram
    # rewrite symbol_addrs.txt: drop function-start overrides inside (fvram, span_end),
    # add/replace the size override for the failing function
    lines = []
    if os.path.exists("disasm/symbol_addrs.txt"):
        for line in open("disasm/symbol_addrs.txt"):
            am = re.search(r'= (0x[0-9A-Fa-f]+);', line)
            if am and fvram < int(am.group(1), 16) < span_end:
                continue
            if f"func_{fvram:08X}" in line or fail in line:
                continue
            lines.append(line.rstrip("\n"))
    lines.append(f"{fail} = 0x{fvram:08X}; // type:func size:0x{new_size:X}")
    open("disasm/symbol_addrs.txt", "w").write("\n".join(lines) + "\n")
    print(f"iter {it}: {fail} size 0x{fsize:X} -> 0x{new_size:X} "
          f"(absorbing {len(ext_targets)} tail target(s))")
    resplit()
print("=== iteration cap reached ===")
sys.exit(1)
