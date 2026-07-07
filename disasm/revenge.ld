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
        build/asm/2D600.o(.text);
        build/asm/2E100.o(.text);
        build/asm/2E900.o(.text);
        build/asm/2F500.o(.text);
        build/asm/30B00.o(.text);
        build/asm/31500.o(.text);
        build/asm/36B00.o(.text);
        build/asm/3C700.o(.text);
        build/asm/77F00.o(.text);
        build/asm/7F100.o(.text);
        build/asm/7FF00.o(.text);
        build/asm/82A00.o(.text);
        build/asm/91A00.o(.text);
        build/asm/CBC00.o(.text);
        build/asm/CC100.o(.text);
        build/asm/CD800.o(.text);
        build/asm/CE200.o(.text);
        build/asm/CE700.o(.text);
        build/asm/CEC00.o(.text);
        build/asm/CF400.o(.text);
        build/asm/CFB00.o(.text);
        build/asm/D0800.o(.text);
        build/asm/D2500.o(.text);
        build/asm/D2A00.o(.text);
        build/asm/D2C00.o(.text);
        build/asm/D3500.o(.text);
        build/asm/D6500.o(.text);
        build/asm/D7A00.o(.text);
        . = ALIGN(., 16);
        main_TEXT_END = .;
        main_TEXT_SIZE = ABSOLUTE(main_TEXT_END - main_TEXT_START);
        main_DATA_START = .;
        build/asm/asm/data/2C800.data.o(.data);
        build/asm/asm/data/2D800.data.o(.data);
        build/asm/asm/data/2E600.data.o(.data);
        build/asm/asm/data/2EB00.data.o(.data);
        build/asm/asm/data/2F900.data.o(.data);
        build/asm/asm/data/30E00.data.o(.data);
        build/asm/asm/data/31900.data.o(.data);
        build/asm/asm/data/36D00.data.o(.data);
        build/asm/asm/data/72200.data.o(.data);
        build/asm/asm/data/78100.data.o(.data);
        build/asm/asm/data/7F300.data.o(.data);
        build/asm/asm/data/80100.data.o(.data);
        build/asm/asm/data/91800.data.o(.data);
        build/asm/asm/data/CB400.data.o(.data);
        build/asm/asm/data/CBF00.data.o(.data);
        build/asm/asm/data/CD600.data.o(.data);
        build/asm/asm/data/CE100.data.o(.data);
        build/asm/asm/data/CE500.data.o(.data);
        build/asm/asm/data/CE900.data.o(.data);
        build/asm/asm/data/CF200.data.o(.data);
        build/asm/asm/data/CF900.data.o(.data);
        build/asm/asm/data/D0500.data.o(.data);
        build/asm/asm/data/D2400.data.o(.data);
        build/asm/asm/data/D2900.data.o(.data);
        build/asm/asm/data/D2B00.data.o(.data);
        build/asm/asm/data/D3200.data.o(.data);
        build/asm/asm/data/D5F00.data.o(.data);
        build/asm/asm/data/D6700.data.o(.data);
        build/asm/1050.o(.data);
        build/asm/2D600.o(.data);
        build/asm/2E100.o(.data);
        build/asm/2E900.o(.data);
        build/asm/2F500.o(.data);
        build/asm/30B00.o(.data);
        build/asm/31500.o(.data);
        build/asm/36B00.o(.data);
        build/asm/3C700.o(.data);
        build/asm/77F00.o(.data);
        build/asm/7F100.o(.data);
        build/asm/7FF00.o(.data);
        build/asm/82A00.o(.data);
        build/asm/91A00.o(.data);
        build/asm/CBC00.o(.data);
        build/asm/CC100.o(.data);
        build/asm/CD800.o(.data);
        build/asm/CE200.o(.data);
        build/asm/CE700.o(.data);
        build/asm/CEC00.o(.data);
        build/asm/CF400.o(.data);
        build/asm/CFB00.o(.data);
        build/asm/D0800.o(.data);
        build/asm/D2500.o(.data);
        build/asm/D2A00.o(.data);
        build/asm/D2C00.o(.data);
        build/asm/D3500.o(.data);
        build/asm/D6500.o(.data);
        build/asm/D7A00.o(.data);
        build/asm/asm/data/D8000.data.o(.data);
        . = ALIGN(., 16);
        main_DATA_END = .;
        main_DATA_SIZE = ABSOLUTE(main_DATA_END - main_DATA_START);
        main_RODATA_START = .;
        build/asm/1050.o(.rodata);
        build/asm/2D600.o(.rodata);
        build/asm/2E100.o(.rodata);
        build/asm/2E900.o(.rodata);
        build/asm/2F500.o(.rodata);
        build/asm/30B00.o(.rodata);
        build/asm/31500.o(.rodata);
        build/asm/36B00.o(.rodata);
        build/asm/3C700.o(.rodata);
        build/asm/77F00.o(.rodata);
        build/asm/7F100.o(.rodata);
        build/asm/7FF00.o(.rodata);
        build/asm/82A00.o(.rodata);
        build/asm/91A00.o(.rodata);
        build/asm/CBC00.o(.rodata);
        build/asm/CC100.o(.rodata);
        build/asm/CD800.o(.rodata);
        build/asm/CE200.o(.rodata);
        build/asm/CE700.o(.rodata);
        build/asm/CEC00.o(.rodata);
        build/asm/CF400.o(.rodata);
        build/asm/CFB00.o(.rodata);
        build/asm/D0800.o(.rodata);
        build/asm/D2500.o(.rodata);
        build/asm/D2A00.o(.rodata);
        build/asm/D2C00.o(.rodata);
        build/asm/D3500.o(.rodata);
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
        build/asm/2D600.o(.bss);
        build/asm/2E100.o(.bss);
        build/asm/2E900.o(.bss);
        build/asm/2F500.o(.bss);
        build/asm/30B00.o(.bss);
        build/asm/31500.o(.bss);
        build/asm/36B00.o(.bss);
        build/asm/3C700.o(.bss);
        build/asm/77F00.o(.bss);
        build/asm/7F100.o(.bss);
        build/asm/7FF00.o(.bss);
        build/asm/82A00.o(.bss);
        build/asm/91A00.o(.bss);
        build/asm/CBC00.o(.bss);
        build/asm/CC100.o(.bss);
        build/asm/CD800.o(.bss);
        build/asm/CE200.o(.bss);
        build/asm/CE700.o(.bss);
        build/asm/CEC00.o(.bss);
        build/asm/CF400.o(.bss);
        build/asm/CFB00.o(.bss);
        build/asm/D0800.o(.bss);
        build/asm/D2500.o(.bss);
        build/asm/D2A00.o(.bss);
        build/asm/D2C00.o(.bss);
        build/asm/D3500.o(.bss);
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
