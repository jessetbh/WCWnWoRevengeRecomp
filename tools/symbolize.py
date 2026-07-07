#!/usr/bin/env python3
"""Symbolize crash-backtrace RVAs against build-msvc/RevengeRecompiled.map.

Usage:
    python tools/symbolize.py 0x7DF80 0x7DC74 ...       # module-relative RVAs
    python tools/symbolize.py --log boot3.err.log        # parse `+0xNNN` frames

MSVC map: symbol lines are `SSSS:OFFSET  name  ADDRESS  [f] [i] obj`; ADDRESS is
based at the preferred load address 0x140000000. Crash frames print
`RevengeRecompiled.exe +0xRVA` (module-relative), so match on
0x140000000 + RVA, nearest symbol <= address (the WT loop's documented method).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "build-msvc" / "RevengeRecompiled.map"
BASE = 0x140000000

SYM_RE = re.compile(
    r"^\s*[0-9a-f]{4}:[0-9a-f]{8}\s+(\S+)\s+([0-9a-f]{16})\s", re.IGNORECASE)
FRAME_RE = re.compile(r"RevengeRecompiled\.exe\s+\+0x([0-9A-Fa-f]+)")


def load_map():
    syms = []
    for line in open(MAP, encoding="utf-8", errors="replace"):
        m = SYM_RE.match(line)
        if m:
            addr = int(m.group(2), 16)
            if addr:
                syms.append((addr, m.group(1)))
    syms.sort()
    return syms


def lookup(syms, addr):
    import bisect
    i = bisect.bisect_right(syms, (addr, "\xff")) - 1
    if i < 0:
        return None, None
    return syms[i][1], addr - syms[i][0]


def main():
    args = sys.argv[1:]
    rvas = []
    if args and args[0] == "--log":
        text = open(args[1], encoding="utf-8", errors="replace").read()
        rvas = [int(x, 16) for x in FRAME_RE.findall(text)]
    else:
        rvas = [int(a, 16) for a in args]
    if not rvas:
        sys.exit("no RVAs given")
    syms = load_map()
    for rva in rvas:
        name, off = lookup(syms, BASE + rva)
        print(f"+0x{rva:<8X} -> {name}+0x{off:X}")


if __name__ == "__main__":
    main()
