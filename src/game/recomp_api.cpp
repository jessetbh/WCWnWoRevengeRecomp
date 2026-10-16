#include <algorithm>
#include <cstdio>

#include "recomp.h"
#include "librecomp/helpers.hpp"
#include "ultramodern/ultramodern.hpp"
#include "ultramodern/config.hpp"
#include "recompui/recompui.h"

// Game-side runtime API callable from MIPS patches (adapted from BMHero's
// src/game/recomp_api.cpp). Every function here needs a matching address entry in
// patches/syms.ld and is exposed to patches via the generated manual_patch_symbols
// table — only implement (and list in syms.ld) what patches actually use.

extern "C" void recomp_puts(uint8_t* rdram, recomp_context* ctx) {
    PTR(char) cur_str = _arg<0, PTR(char)>(rdram, ctx);
    u32 length = _arg<1, u32>(rdram, ctx);

    for (u32 i = 0; i < length; i++) {
        fputc(MEM_B(i, (gpr)cur_str), stdout);
    }
    // Redirected stdout is fully buffered; without a flush, output sits in the CRT
    // buffer and is lost if the process is killed (this is a debugging API — flush).
    fflush(stdout);
}

extern "C" void recomp_exit(uint8_t* rdram, recomp_context* ctx) {
    ultramodern::quit();
}

// Aspect ratio the game should build its 3D projection with (widescreen patch,
// patches/widescreen.c). Same semantics as BMHero's: Original → the game's own ratio
// unchanged; Expand → the window's ratio, never below the original (RT64's Expand
// aspect mode then gives full-width perspective projections the wide viewport).
extern "C" void recomp_get_target_aspect_ratio(uint8_t* rdram, recomp_context* ctx) {
    float original = _arg<0, float>(rdram, ctx);
    const ultramodern::renderer::GraphicsConfig& config = ultramodern::renderer::get_graphics_config();

    if (config.ar_option == ultramodern::renderer::AspectRatio::Expand) {
        int width = 0, height = 0;
        recompui::get_window_size(width, height);
        if (width > 0 && height > 0) {
            _return(ctx, std::max(static_cast<float>(width) / height, original));
            return;
        }
    }
    _return(ctx, original);
}

// [wcw fix] Widescreen cull (aki-roadmap#47 / #5), called from the hand-edited func_80002110
// (tools/readd_hand_edits.py). The game drops an object when its center is past
// |x| / (depth + 150) > 1.5 in view space, about 3.8x the 4:3 screen edge. In Expand the screen
// is wider, so large set pieces whose center is past that line but which reach into the extra
// width vanished at the edges. The horizontal limit is scaled by how much wider than 4:3 the
// screen is, keeping the game's own margin; 1 at Original, so 4:3 is unchanged.
extern "C" double wcw_widescreen_cull_scale() {
    const ultramodern::renderer::GraphicsConfig& config = ultramodern::renderer::get_graphics_config();
    if (config.ar_option != ultramodern::renderer::AspectRatio::Expand) {
        return 1.0;
    }

    int width = 0, height = 0;
    recompui::get_window_size(width, height);
    if (width <= 0 || height <= 0) {
        return 1.0;
    }

    return std::max(1.0, (static_cast<double>(width) / height) / (4.0 / 3.0));
}
