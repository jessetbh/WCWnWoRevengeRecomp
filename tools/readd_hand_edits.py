#!/usr/bin/env python3
"""Re-apply RecompiledFuncs hand-edits after a regen (WCW/nWo Revenge).

Every N64Recomp regen wipes edits made directly in RecompiledFuncs/*.c; register them
here (idempotent, safe to re-run) and run this AFTER the regen pipeline. Anchors are exact
generated lines; a missing anchor fails loudly (regen output changed shape).
"""

# [revenge][rt] Ray tracing experiment (exp/raytracing; src/game/raytracing.cpp): hand RT64
# the real camera. RT64 only uses it while ray tracing is active (menu option or WCW_RT).
def rt_hand_edits():
    import os as _os
    funcs = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'RecompiledFuncs')
    def _load(fn):
        with open(_os.path.join(funcs, fn), 'rb') as f:
            return f.read().decode('utf-8', errors='replace').splitlines(keepends=True)
    def _save(fn, lines):
        with open(_os.path.join(funcs, fn), 'wb') as f:
            f.write(''.join(lines).encode('utf-8'))
    def _body(lines, name):
        sig = 'RECOMP_FUNC void %s(' % name
        start = next((i for i, l in enumerate(lines) if l.startswith(sig)), None)
        if start is None:
            return None, None
        end = next((i for i in range(start, len(lines)) if lines[i].rstrip('\r\n') == ';}'), None)
        return start, end
    def _insert_after_all(fn, func, anchor, text, expect):
        lines = _load(fn)
        if any('[revenge][rt]' in l for l in lines[slice(*_body(lines, func))] if l):
            return '%s already present' % func
        lo, hi = _body(lines, func)
        if lo is None or hi is None:
            raise SystemExit('rt: cannot locate %s in %s' % (func, fn))
        hits = [i for i in range(lo, hi) if lines[i].rstrip('\r\n') == anchor]
        if len(hits) != expect:
            raise SystemExit('rt: anchor %r matched %d times in %s (expected %d)' % (anchor, len(hits), func, expect))
        for i in reversed(hits):
            lines[i + 1:i + 1] = text
        _save(fn, lines)
        return '%s (%d site(s))' % (func, len(hits))
    done = []
    done.append(_insert_after_all('funcs_0.c', 'func_800014AC', '    ctx->r4 = ADD32(ctx->r6, 0);', [
        '    { /* [revenge][rt] camera latch: a1 = P, a2 = V */\n',
        '      extern void wcw_rt_latch_camera(uint8_t* rdram, uint32_t proj_vaddr, uint32_t view_vaddr);\n',
        '      wcw_rt_latch_camera(rdram, (uint32_t)ctx->r5, (uint32_t)ctx->r6); }\n'], 1))
    done.append(_insert_after_all('funcs_1.c', 'func_80002CC4', '    func_80002664(rdram, ctx);', [
        '    { /* [revenge][rt] after the frame DL head is returned in v0 */\n',
        '      extern uint32_t wcw_rt_emit_camera(uint8_t* rdram, uint32_t gfx);\n',
        '      ctx->r2 = (int64_t)(int32_t)wcw_rt_emit_camera(rdram, (uint32_t)ctx->r2); }\n'], 1))
    return 'rt camera hand-off: ' + '; '.join(done)


if __name__ == '__main__':
    print('readd_hand_edits: ' + rt_hand_edits())
