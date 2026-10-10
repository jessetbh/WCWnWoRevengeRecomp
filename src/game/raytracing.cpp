#include <cstdint>
#include <cstdlib>

// Ray tracing experiment (exp/raytracing): hand RT64 the real camera.
//
// Like every AKI engine, WCW/nWo Revenge composes each MVP on the CPU (object matrix x V x P,
// latched by func_800014AC into D_80048288 via func_80001C28) and submits it via forced matrices, so
// RT64 never sees a projection and its "world" transforms are clip-space MVPs. Ray tracing
// needs true world space, so two hand-edits in RecompiledFuncs (tools/readd_hand_edits.py)
// call in here (same scheme as Vpw2Recomp's src/game/raytracing.cpp):
//  - wcw_rt_latch_camera: at the top of func_800014AC(cam, P, V), the camera latch every camera
//    setup goes through, copies the P and V float matrices.
//  - wcw_rt_emit_camera: right after func_80002664 returns the frame's display-list head
//    (in func_80002CC4), writes
//      gEXEnable                (RT64 hook on F3DEX2 G_SPNOOP 0xE0; RT64 resets it per DL)
//      gEXSetViewMatrixFloat / gEXSetProjMatrixFloat (inline copies of V and P)
//      gSPBranchList            (past the inline matrices, which share the DL's lifetime)
//    and returns the advanced head. RT64 ([wcw rt], rt64_rsp.cpp) loads this camera into
//    the projection stack only while ray tracing is active (Graphics menu option or WCW_RT)
//    and ignores it otherwise, so rendering is unchanged with the option off.

namespace {
    constexpr uint32_t RT64_HOOK_OPCODE = 0xE0;
    constexpr uint32_t RT64_HOOK_MAGIC = 0x525464;
    constexpr uint32_t RT64_HOOK_OP_ENABLE = 0x1;
    constexpr uint32_t RT64_EXTENDED_OPCODE = 0x64;
    constexpr uint32_t G_EX_SETPROJMATRIXFLOAT_V1 = 0x00002D;
    constexpr uint32_t G_EX_SETVIEWMATRIXFLOAT_V1 = 0x00002E;
    constexpr uint32_t GBI_G_DL = 0xDE;
    constexpr uint32_t G_DL_NOPUSH = 0x01;

    bool camera_valid = false;
    uint32_t camera_view[16];
    uint32_t camera_proj[16];

    // RDRAM words are stored native-endian (N64Recomp's MEM_W layout); vaddr is KSEG0.
    uint32_t& rdram_word(uint8_t* rdram, uint32_t vaddr) {
        return *reinterpret_cast<uint32_t*>(rdram + (vaddr - 0x80000000u));
    }
}

extern "C" void wcw_rt_latch_camera(uint8_t* rdram, uint32_t proj_vaddr, uint32_t view_vaddr) {
    for (uint32_t i = 0; i < 16; i++) {
        camera_proj[i] = rdram_word(rdram, proj_vaddr + i * 4);
        camera_view[i] = rdram_word(rdram, view_vaddr + i * 4);
    }

    camera_valid = true;
}

extern "C" uint32_t wcw_rt_emit_camera(uint8_t* rdram, uint32_t gfx) {
    if (!camera_valid) {
        return gfx;
    }

    const uint32_t view = gfx + 4 * 8;
    const uint32_t proj = view + 64;
    const uint32_t after = proj + 64;
    for (uint32_t i = 0; i < 16; i++) {
        rdram_word(rdram, view + i * 4) = camera_view[i];
        rdram_word(rdram, proj + i * 4) = camera_proj[i];
    }

    rdram_word(rdram, gfx + 0x00) = (RT64_HOOK_OPCODE << 24) | RT64_HOOK_MAGIC;
    rdram_word(rdram, gfx + 0x04) = (RT64_HOOK_OP_ENABLE << 28) | RT64_EXTENDED_OPCODE;
    rdram_word(rdram, gfx + 0x08) = (RT64_EXTENDED_OPCODE << 24) | G_EX_SETVIEWMATRIXFLOAT_V1;
    rdram_word(rdram, gfx + 0x0C) = view;
    rdram_word(rdram, gfx + 0x10) = (RT64_EXTENDED_OPCODE << 24) | G_EX_SETPROJMATRIXFLOAT_V1;
    rdram_word(rdram, gfx + 0x14) = proj;
    rdram_word(rdram, gfx + 0x18) = (GBI_G_DL << 24) | (G_DL_NOPUSH << 16);
    rdram_word(rdram, gfx + 0x1C) = after;
    return after;
}
