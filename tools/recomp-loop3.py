#!/usr/bin/env python3
"""Recompile triage loop v3. Reads N64Recomp's per-function diagnostics for the
FAILING function only (warnings about other functions are non-fatal):

  A. "Unhandled branch in <fail> at A to T" / external j-targets, all FORWARD:
     IDO shared-tail split -> extend <fail>'s size to absorb targets.
  B. Any escape target BACKWARD (before function start): <fail> is a continuation
     fragment -> merge into the containing earlier function (extend its size and
     skip <fail> as a symbol if nothing jal's it; else stub + flag for review).
  C. No escape info at all -> stub (cop0-style unrecompilable), flag for review.
"""
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
        if m: funcs[m.group(1)] = (int(m.group(2), 16), int(m.group(3), 16))
    return funcs

def containing(funcs, addr):
    for n, (v, s) in funcs.items():
        if v <= addr < v + s:
            return n
    return None

def fn_body(name):
    for f in glob.glob("disasm/asm/*.s"):
        txt = open(f, encoding="utf-8").read()
        m = re.search(rf"^glabel {name}\n(.*?)(?:^endlabel|\Z)", txt, re.S | re.M)
        if m: return m.group(1)
    return ""

def jal_referenced(name):
    for f in glob.glob("disasm/asm/*.s"):
        if re.search(rf"\bjal\s+{name}\b", open(f, encoding="utf-8").read()):
            return True
    return False

def set_size(symfile_lines, name, vram, size):
    out = [l for l in symfile_lines if f"func_{vram:08X}" not in l and name not in l]
    out.append(f"{name} = 0x{vram:08X}; // type:func size:0x{size:X}")
    return out

def add_stub(name):
    cands = open("syms/stub_candidates.txt").read()
    if f'"{name}"' in cands: return False
    with open("syms/stub_candidates.txt", "a", newline="\n") as f:
        f.write(f'    "{name}",\n')
    stubs = open("syms/stub_candidates.txt").read()
    toml = open("revenge.toml").read()
    toml = re.sub(r"stubs = \[\n.*?\]", "stubs = [\n" + stubs + "]", toml, flags=re.S)
    open("revenge.toml", "w", newline="\n").write(toml)
    return True

def resplit():
    subprocess.run([PY, "-m", "splat", "split", "revenge.yaml"], cwd="disasm", capture_output=True)
    subprocess.run([sys.executable, "tools/gen_symbols.py"], capture_output=True)
    # prune stub entries whose functions no longer exist (swallowed by a merge)
    funcs = load_funcs()
    kept = []
    for line in open("syms/stub_candidates.txt"):
        m = re.search(r'"(\S+)"', line)
        if m and m.group(1) not in funcs:
            continue
        kept.append(line)
    open("syms/stub_candidates.txt", "w", newline="\n").writelines(kept)
    stubs = "".join(kept)
    toml = open("revenge.toml").read()
    toml = re.sub(r"stubs = \[\n.*?\]", "stubs = [\n" + stubs + "]", toml, flags=re.S)
    open("revenge.toml", "w", newline="\n").write(toml)

def sym_lines():
    if os.path.exists("disasm/symbol_addrs.txt"):
        return [l.rstrip("\n") for l in open("disasm/symbol_addrs.txt") if l.strip()]
    return []

for it in range(1, 61):
    code, out = run_recomp()
    if code == 0:
        print(f"=== CLEAN RECOMPILE after {it} iteration(s) ===")
        print(f"RecompiledFuncs: {len(glob.glob('RecompiledFuncs/*.c'))} files")
        sys.exit(0)
    m = re.search(r"Error recompiling (\S+)", out)
    if not m:
        print("=== unrecognized failure ==="); print(out[-1500:]); sys.exit(1)
    fail = m.group(1)
    funcs = load_funcs()
    if fail not in funcs:
        print(f"=== {fail} not in dump.toml ==="); sys.exit(1)
    fvram, fsize = funcs[fail]

    escapes = [int(t, 16) for t in
               re.findall(rf"Unhandled branch in {fail} at 0x[0-9A-Fa-f]+ to (0x[0-9A-Fa-f]+)", out)]
    escapes += [int(t, 16) for t in
                re.findall(rf"Function {fail} is branching outside of the function \(to (0x[0-9A-Fa-f]+)\)", out)]
    body = fn_body(fail)
    for jm in re.finditer(r'\bj\s+func_([0-9A-Fa-f]{8})', body):
        escapes.append(int(jm.group(1), 16))
    escapes = sorted({t for t in escapes if not (fvram <= t < fvram + fsize)})

    lines = sym_lines()
    # data-as-code guard: escapes outside the loaded segment mean this "function"
    # is data words that decode as jumps — stub it, it is never really executed
    if escapes and any(not (0x80000400 <= t < 0x80100400) for t in escapes):
        add_stub(fail)
        print(f"iter {it}: STUB {fail} (j-target outside loaded segment = data-as-code)")
        continue
    if escapes and min(escapes) >= fvram:
        span_end = fvram + fsize
        for t in escapes:
            end = t + 0x40
            c = containing(funcs, t)
            if c: end = funcs[c][0] + funcs[c][1]
            span_end = max(span_end, end)
        lines = set_size(lines, fail, fvram, span_end - fvram)
        print(f"iter {it}: FORWARD-EXTEND {fail} 0x{fsize:X} -> 0x{span_end - fvram:X}")
    elif escapes:
        back = min(escapes)
        c = containing(funcs, back)
        if c and not jal_referenced(fail):
            cv, cs = funcs[c]
            newsize = (fvram + fsize) - cv
            lines = set_size(lines, c, cv, newsize)
            # suppress <fail> as a function start
            skips = set()
            if os.path.exists("syms/skip_functions.txt"):
                skips = {l.strip() for l in open("syms/skip_functions.txt")}
            skips.add(fail)
            open("syms/skip_functions.txt", "w", newline="\n").write("\n".join(sorted(skips)) + "\n")
            print(f"iter {it}: BACKWARD-MERGE {fail} into {c} (size 0x{newsize:X})")
        else:
            add_stub(fail)
            print(f"iter {it}: STUB {fail} (backward escape but jal-referenced or no container) — REVIEW")
            continue
    else:
        add_stub(fail)
        print(f"iter {it}: STUB {fail} (no escape info) — REVIEW")
        continue
    open("disasm/symbol_addrs.txt", "w", newline="\n").write("\n".join(lines) + "\n")
    resplit()
print("=== iteration cap reached ===")
sys.exit(1)
