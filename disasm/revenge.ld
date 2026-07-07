SECTIONS
{
    __romPos = 0;
    header_ROM_START = __romPos;
    header_VRAM = ADDR(.header);
    .header : AT(header_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        header_DATA_START = .;
        build/asm/header.o(.data);
        header_DATA_END = .;
        header_DATA_SIZE = ABSOLUTE(header_DATA_END - header_DATA_START);
    }
    __romPos += SIZEOF(.header);
    header_ROM_END = __romPos;
    header_VRAM_END = .;

    ipl3_ROM_START = __romPos;
    ipl3_VRAM = ADDR(.ipl3);
    .ipl3 : AT(ipl3_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        ipl3_DATA_START = .;
        build/assets/ipl3.o(.data);
        ipl3_DATA_END = .;
        ipl3_DATA_SIZE = ABSOLUTE(ipl3_DATA_END - ipl3_DATA_START);
    }
    __romPos += SIZEOF(.ipl3);
    ipl3_ROM_END = __romPos;
    ipl3_VRAM_END = .;

    entry_ROM_START = __romPos;
    entry_VRAM = ADDR(.entry);
    .entry 0x80000400 : AT(entry_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        entry_TEXT_START = .;
        build/asm/1000.o(.text);
        . = ALIGN(., 16);
        entry_TEXT_END = .;
        entry_TEXT_SIZE = ABSOLUTE(entry_TEXT_END - entry_TEXT_START);
        entry_DATA_START = .;
        build/asm/1000.o(.data);
        . = ALIGN(., 16);
        entry_DATA_END = .;
        entry_DATA_SIZE = ABSOLUTE(entry_DATA_END - entry_DATA_START);
        entry_RODATA_START = .;
        build/asm/1000.o(.rodata);
        . = ALIGN(., 16);
        entry_RODATA_END = .;
        entry_RODATA_SIZE = ABSOLUTE(entry_RODATA_END - entry_RODATA_START);
    }
    entry_bss_VRAM = ADDR(.entry_bss);
    .entry_bss (NOLOAD) : SUBALIGN(16)
    {
        FILL(0x00000000);
        entry_BSS_START = .;
        build/asm/1000.o(.bss);
        . = ALIGN(., 16);
        entry_BSS_END = .;
        entry_BSS_SIZE = ABSOLUTE(entry_BSS_END - entry_BSS_START);
    }
    __romPos += SIZEOF(.entry);
    __romPos = ALIGN(__romPos, 16);
    . = ALIGN(., 16);
    entry_ROM_END = __romPos;
    entry_VRAM_END = .;

    main_ROM_START = __romPos;
    main_VRAM = ADDR(.main);
    .main entry_VRAM_END : AT(main_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        main_TEXT_START = .;
        build/asm/1050.o(.text);
        build/asm/2D500.o(.text);
        build/asm/2E100.o(.text);
        build/asm/2E900.o(.text);
        build/asm/2F500.o(.text);
        build/asm/30B00.o(.text);
        build/asm/31500.o(.text);
        build/asm/32600.o(.text);
        build/asm/33000.o(.text);
        build/asm/33F00.o(.text);
        build/asm/35400.o(.text);
        build/asm/35C00.o(.text);
        build/asm/36B00.o(.text);
        build/asm/39800.o(.text);
        build/asm/3B800.o(.text);
        build/asm/3C700.o(.text);
        build/asm/76800.o(.text);
        build/asm/76D00.o(.text);
        build/asm/77200.o(.text);
        build/asm/7EC00.o(.text);
        build/asm/7F000.o(.text);
        build/asm/7FE00.o(.text);
        build/asm/81100.o(.text);
        build/asm/82A00.o(.text);
        build/asm/D6500.o(.text);
        build/asm/D7A00.o(.text);
        . = ALIGN(., 16);
        main_TEXT_END = .;
        main_TEXT_SIZE = ABSOLUTE(main_TEXT_END - main_TEXT_START);
        main_DATA_START = .;
        build/asm/asm/data/2CC00.data.o(.data);
        build/asm/asm/data/2D800.data.o(.data);
        build/asm/asm/data/2E600.data.o(.data);
        build/asm/asm/data/2EB00.data.o(.data);
        build/asm/asm/data/2FA00.data.o(.data);
        build/asm/asm/data/30E00.data.o(.data);
        build/asm/asm/data/31900.data.o(.data);
        build/asm/asm/data/32C00.data.o(.data);
        build/asm/asm/data/33C00.data.o(.data);
        build/asm/asm/data/34E00.data.o(.data);
        build/asm/asm/data/35800.data.o(.data);
        build/asm/asm/data/36800.data.o(.data);
        build/asm/asm/data/36D00.data.o(.data);
        build/asm/asm/data/39A00.data.o(.data);
        build/asm/asm/data/3BA00.data.o(.data);
        build/asm/asm/data/72400.data.o(.data);
        build/asm/asm/data/76A00.data.o(.data);
        build/asm/asm/data/76F00.data.o(.data);
        build/asm/asm/data/78100.data.o(.data);
        build/asm/asm/data/7EE00.data.o(.data);
        build/asm/asm/data/7F300.data.o(.data);
        build/asm/asm/data/80100.data.o(.data);
        build/asm/asm/data/81400.data.o(.data);
        build/asm/asm/data/D5F00.data.o(.data);
        build/asm/asm/data/D6800.data.o(.data);
        build/asm/1050.o(.data);
        build/asm/2D500.o(.data);
        build/asm/2E100.o(.data);
        build/asm/2E900.o(.data);
        build/asm/2F500.o(.data);
        build/asm/30B00.o(.data);
        build/asm/31500.o(.data);
        build/asm/32600.o(.data);
        build/asm/33000.o(.data);
        build/asm/33F00.o(.data);
        build/asm/35400.o(.data);
        build/asm/35C00.o(.data);
        build/asm/36B00.o(.data);
        build/asm/39800.o(.data);
        build/asm/3B800.o(.data);
        build/asm/3C700.o(.data);
        build/asm/76800.o(.data);
        build/asm/76D00.o(.data);
        build/asm/77200.o(.data);
        build/asm/7EC00.o(.data);
        build/asm/7F000.o(.data);
        build/asm/7FE00.o(.data);
        build/asm/81100.o(.data);
        build/asm/82A00.o(.data);
        build/asm/D6500.o(.data);
        build/asm/D7A00.o(.data);
        build/asm/asm/data/D8000.data.o(.data);
        . = ALIGN(., 16);
        main_DATA_END = .;
        main_DATA_SIZE = ABSOLUTE(main_DATA_END - main_DATA_START);
        main_RODATA_START = .;
        build/asm/1050.o(.rodata);
        build/asm/2D500.o(.rodata);
        build/asm/2E100.o(.rodata);
        build/asm/2E900.o(.rodata);
        build/asm/2F500.o(.rodata);
        build/asm/30B00.o(.rodata);
        build/asm/31500.o(.rodata);
        build/asm/32600.o(.rodata);
        build/asm/33000.o(.rodata);
        build/asm/33F00.o(.rodata);
        build/asm/35400.o(.rodata);
        build/asm/35C00.o(.rodata);
        build/asm/36B00.o(.rodata);
        build/asm/39800.o(.rodata);
        build/asm/3B800.o(.rodata);
        build/asm/3C700.o(.rodata);
        build/asm/76800.o(.rodata);
        build/asm/76D00.o(.rodata);
        build/asm/77200.o(.rodata);
        build/asm/7EC00.o(.rodata);
        build/asm/7F000.o(.rodata);
        build/asm/7FE00.o(.rodata);
        build/asm/81100.o(.rodata);
        build/asm/82A00.o(.rodata);
        build/asm/D6500.o(.rodata);
        build/asm/D7A00.o(.rodata);
        . = ALIGN(., 16);
        main_RODATA_END = .;
        main_RODATA_SIZE = ABSOLUTE(main_RODATA_END - main_RODATA_START);
    }
    main_bss_VRAM = ADDR(.main_bss);
    .main_bss (NOLOAD) : SUBALIGN(16)
    {
        FILL(0x00000000);
        main_BSS_START = .;
        build/asm/1050.o(.bss);
        build/asm/2D500.o(.bss);
        build/asm/2E100.o(.bss);
        build/asm/2E900.o(.bss);
        build/asm/2F500.o(.bss);
        build/asm/30B00.o(.bss);
        build/asm/31500.o(.bss);
        build/asm/32600.o(.bss);
        build/asm/33000.o(.bss);
        build/asm/33F00.o(.bss);
        build/asm/35400.o(.bss);
        build/asm/35C00.o(.bss);
        build/asm/36B00.o(.bss);
        build/asm/39800.o(.bss);
        build/asm/3B800.o(.bss);
        build/asm/3C700.o(.bss);
        build/asm/76800.o(.bss);
        build/asm/76D00.o(.bss);
        build/asm/77200.o(.bss);
        build/asm/7EC00.o(.bss);
        build/asm/7F000.o(.bss);
        build/asm/7FE00.o(.bss);
        build/asm/81100.o(.bss);
        build/asm/82A00.o(.bss);
        build/asm/D6500.o(.bss);
        build/asm/D7A00.o(.bss);
        . = ALIGN(., 16);
        main_BSS_END = .;
        main_BSS_SIZE = ABSOLUTE(main_BSS_END - main_BSS_START);
    }
    __romPos += SIZEOF(.main);
    __romPos = ALIGN(__romPos, 16);
    . = ALIGN(., 16);
    main_ROM_END = __romPos;
    main_VRAM_END = .;

    assets_ROM_START = __romPos;
    assets_VRAM = ADDR(.assets);
    .assets : AT(assets_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        assets_DATA_START = .;
        build/assets/assets.o(.data);
        assets_DATA_END = .;
        assets_DATA_SIZE = ABSOLUTE(assets_DATA_END - assets_DATA_START);
    }
    __romPos += SIZEOF(.assets);
    assets_ROM_END = __romPos;
    assets_VRAM_END = .;

    /DISCARD/ :
    {
        *(*);
    }
}
