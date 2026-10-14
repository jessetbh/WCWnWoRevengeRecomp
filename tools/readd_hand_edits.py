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
    # The latch sits in the matrix multiply func_800014AC calls, not in func_800014AC itself:
    # mods hook func_800014AC (AkiMods' camera) and a hooked function is recompiled from the
    # ROM without hand-edits. Older generated files had it in func_800014AC: strip that site.
    lines = _load('funcs_0.c')
    old = next((i for i, l in enumerate(lines) if '[revenge][rt] camera latch: a1 = P, a2 = V' in l), None)
    if old is not None:
        del lines[old:old + 3]
        _save('funcs_0.c', lines)
        done.append('removed old latch in func_800014AC')
    done.append(_insert_after_all('funcs_0.c', 'func_80001C28', '    int c1cs = 0;', [
        '    { /* [revenge][rt] camera latch: a0 = V, a1 = P, a2 = product (the camera matrix when called from the camera builder) */\n',
        '      extern void wcw_rt_latch_camera_multiply(uint8_t* rdram, uint32_t view_vaddr, uint32_t proj_vaddr, uint32_t dest_vaddr);\n',
        '      wcw_rt_latch_camera_multiply(rdram, (uint32_t)ctx->r4, (uint32_t)ctx->r5, (uint32_t)ctx->r6); }\n'], 1))
    done.append(_insert_after_all('funcs_1.c', 'func_80002CC4', '    func_80002664(rdram, ctx);', [
        '    { /* [revenge][rt] after the frame DL head is returned in v0 */\n',
        '      extern uint32_t wcw_rt_emit_camera(uint8_t* rdram, uint32_t gfx);\n',
        '      ctx->r2 = (int64_t)(int32_t)wcw_rt_emit_camera(rdram, (uint32_t)ctx->r2); }\n'], 1))
    return 'rt camera hand-off: ' + '; '.join(done)


# [wcw fix] Widescreen cull (aki-roadmap#47 / #5). func_80002110 builds the visible-object lists of the
# layer passes and drops an object when |x| / (depth + 150) > 1.5 or |y| / (depth + 150) > 1.5
# (view space; the AKI engine's per-object cull, the same as No Mercy's func_800024F8). That is about
# 3.8x the 4:3 screen edge, but with Aspect Ratio = Expand RT64 shows a wider view, and large set pieces
# whose center is past the line while their geometry reaches into the extra width were culled at the
# screen edges (edge pop-in). Scale only the horizontal limit by the screen's widening
# (wcw_widescreen_cull_scale, src/game/recomp_api.cpp: 1 at Original). The projection is untouched
# (RT64's Expand widens it). Never hook func_80002110 from a mod: a hooked function is recompiled from the
# ROM without this edit.
WCW_CULL_FUNC = 'func_80002110'
WCW_CULL_X_LOAD = '    ctx->f12.u32l = MEM_W(ctx->r16, 0X18);'
WCW_CULL_COMPARE = '    c1cs = ctx->f22.d < ctx->f0.d;'
WCW_CULL_EDIT = [
    '    /* [wcw fix] widescreen cull: the horizontal limit follows the screen width (aki-roadmap#47). */\n',
    '    c1cs = (ctx->f22.d * wcw_widescreen_cull_scale()) < ctx->f0.d;\n',
]
WCW_CULL_DECLS = [
    '/* [wcw fix] widescreen cull scale, implemented in src/game/recomp_api.cpp. */\n',
    'extern double wcw_widescreen_cull_scale(void);\n',
]

def widescreen_cull_edit():
    """Replace the cull's horizontal compare (the first after the x load) in place. Fails loudly if the
    generated code changed shape."""
    import glob, os as _os, sys as _sys
    funcs = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'RecompiledFuncs')
    sig = 'RECOMP_FUNC void %s(' % WCW_CULL_FUNC
    for path in sorted(glob.glob(_os.path.join(funcs, 'funcs_*.c'))):
        with open(path, 'rb') as f:
            lines = f.read().decode('utf-8', errors='replace').splitlines(keepends=True)
        start = next((i for i, l in enumerate(lines) if l.startswith(sig)), None)
        if start is None:
            continue
        if any('wcw_widescreen_cull_scale' in l for l in lines):
            return 'widescreen cull (already present)'
        end = next(i for i in range(start, len(lines)) if lines[i].rstrip('\r\n') == ';}')
        loads = [i for i in range(start, end) if lines[i].rstrip('\r\n') == WCW_CULL_X_LOAD]
        compares = [i for i in range(loads[0], end) if lines[i].rstrip('\r\n') == WCW_CULL_COMPARE] if len(loads) == 1 else []
        if len(loads) != 1 or len(compares) != 2:
            _sys.exit('widescreen cull: %s changed shape (%d x loads, %d compares); re-derive the edit'
                      % (WCW_CULL_FUNC, len(loads), len(compares)))
        lines[compares[0]:compares[0] + 1] = WCW_CULL_EDIT
        last_include = max((i for i, l in enumerate(lines) if l.startswith('#include')), default=-1)
        lines[last_include + 1:last_include + 1] = WCW_CULL_DECLS
        with open(path, 'wb') as f:
            f.write(''.join(lines).encode('utf-8'))
        return 'widescreen cull -> %s %s' % (_os.path.basename(path), WCW_CULL_FUNC)
    _sys.exit('widescreen cull: %s not found in RecompiledFuncs' % WCW_CULL_FUNC)


if __name__ == '__main__':
    print('readd_hand_edits: ' + rt_hand_edits())
    print('readd_hand_edits: ' + widescreen_cull_edit())
