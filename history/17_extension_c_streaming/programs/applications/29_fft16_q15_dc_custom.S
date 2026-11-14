.section .text
.globl _start
_start:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 1280
    lui x19, 0x10001
    addi x19, x19, 1024
    lh x10, 0(x18)
    lh x11, 2(x18)
    sw x10, 0(x19)
    sw x11, 4(x19)
    lh x10, 32(x18)
    lh x11, 34(x18)
    sw x10, 8(x19)
    sw x11, 12(x19)
    lh x10, 16(x18)
    lh x11, 18(x18)
    sw x10, 16(x19)
    sw x11, 20(x19)
    lh x10, 48(x18)
    lh x11, 50(x18)
    sw x10, 24(x19)
    sw x11, 28(x19)
    lh x10, 8(x18)
    lh x11, 10(x18)
    sw x10, 32(x19)
    sw x11, 36(x19)
    lh x10, 40(x18)
    lh x11, 42(x18)
    sw x10, 40(x19)
    sw x11, 44(x19)
    lh x10, 24(x18)
    lh x11, 26(x18)
    sw x10, 48(x19)
    sw x11, 52(x19)
    lh x10, 56(x18)
    lh x11, 58(x18)
    sw x10, 56(x19)
    sw x11, 60(x19)
    lh x10, 4(x18)
    lh x11, 6(x18)
    sw x10, 64(x19)
    sw x11, 68(x19)
    lh x10, 36(x18)
    lh x11, 38(x18)
    sw x10, 72(x19)
    sw x11, 76(x19)
    lh x10, 20(x18)
    lh x11, 22(x18)
    sw x10, 80(x19)
    sw x11, 84(x19)
    lh x10, 52(x18)
    lh x11, 54(x18)
    sw x10, 88(x19)
    sw x11, 92(x19)
    lh x10, 12(x18)
    lh x11, 14(x18)
    sw x10, 96(x19)
    sw x11, 100(x19)
    lh x10, 44(x18)
    lh x11, 46(x18)
    sw x10, 104(x19)
    sw x11, 108(x19)
    lh x10, 28(x18)
    lh x11, 30(x18)
    sw x10, 112(x19)
    sw x11, 116(x19)
    lh x10, 60(x18)
    lh x11, 62(x18)
    sw x10, 120(x19)
    sw x11, 124(x19)
    lui x18, 0x10001
    addi x18, x18, 1024
    addi x23, x0, 8
fft2_group:
    addi x19, x18, 8
    lui x17, 0x10000
    addi x17, x17, 1408
    addi x20, x0, 1
fft2_butterfly:
    lw x24, 0(x19)
    lw x25, 4(x19)
    lw x26, 0(x18)
    lw x27, 4(x18)
    lh x8, 0(x17)
    lh x9, 2(x17)
    addi x10, x24, 0
    addi x11, x8, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    add x29, x29, x10
    srai x29, x29, 15
    add x10, x26, x28
    add x11, x27, x29
    sub x12, x26, x28
    sub x13, x27, x29
    srai x10, x10, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x10, x5, clip_340high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_340end
clip_340high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_340end
    lui x10, 0x8
    addi x10, x10, -1
clip_340end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_341high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_341end
clip_341high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_341end
    lui x11, 0x8
    addi x11, x11, -1
clip_341end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_342high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_342end
clip_342high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_342end
    lui x12, 0x8
    addi x12, x12, -1
clip_342end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_343high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_343end
clip_343high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_343end
    lui x13, 0x8
    addi x13, x13, -1
clip_343end:
    sw x10, 0(x18)
    sw x11, 4(x18)
    sw x12, 0(x19)
    sw x13, 4(x19)
    addi x18, x18, 8
    addi x19, x19, 8
    addi x17, x17, 32
    addi x20, x20, -1
    bne x20, x0, fft2_butterfly
    addi x18, x18, 8
    addi x23, x23, -1
    bne x23, x0, fft2_group
    lui x18, 0x10001
    addi x18, x18, 1024
    addi x23, x0, 4
fft4_group:
    addi x19, x18, 16
    lui x17, 0x10000
    addi x17, x17, 1408
    addi x20, x0, 2
fft4_butterfly:
    lw x24, 0(x19)
    lw x25, 4(x19)
    lw x26, 0(x18)
    lw x27, 4(x18)
    lh x8, 0(x17)
    lh x9, 2(x17)
    addi x10, x24, 0
    addi x11, x8, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    add x29, x29, x10
    srai x29, x29, 15
    add x10, x26, x28
    add x11, x27, x29
    sub x12, x26, x28
    sub x13, x27, x29
    srai x10, x10, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x10, x5, clip_344high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_344end
clip_344high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_344end
    lui x10, 0x8
    addi x10, x10, -1
clip_344end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_345high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_345end
clip_345high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_345end
    lui x11, 0x8
    addi x11, x11, -1
clip_345end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_346high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_346end
clip_346high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_346end
    lui x12, 0x8
    addi x12, x12, -1
clip_346end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_347high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_347end
clip_347high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_347end
    lui x13, 0x8
    addi x13, x13, -1
clip_347end:
    sw x10, 0(x18)
    sw x11, 4(x18)
    sw x12, 0(x19)
    sw x13, 4(x19)
    addi x18, x18, 8
    addi x19, x19, 8
    addi x17, x17, 16
    addi x20, x20, -1
    bne x20, x0, fft4_butterfly
    addi x18, x18, 16
    addi x23, x23, -1
    bne x23, x0, fft4_group
    lui x18, 0x10001
    addi x18, x18, 1024
    addi x23, x0, 2
fft8_group:
    addi x19, x18, 32
    lui x17, 0x10000
    addi x17, x17, 1408
    addi x20, x0, 4
fft8_butterfly:
    lw x24, 0(x19)
    lw x25, 4(x19)
    lw x26, 0(x18)
    lw x27, 4(x18)
    lh x8, 0(x17)
    lh x9, 2(x17)
    addi x10, x24, 0
    addi x11, x8, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    add x29, x29, x10
    srai x29, x29, 15
    add x10, x26, x28
    add x11, x27, x29
    sub x12, x26, x28
    sub x13, x27, x29
    srai x10, x10, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x10, x5, clip_348high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_348end
clip_348high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_348end
    lui x10, 0x8
    addi x10, x10, -1
clip_348end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_349high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_349end
clip_349high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_349end
    lui x11, 0x8
    addi x11, x11, -1
clip_349end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_350high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_350end
clip_350high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_350end
    lui x12, 0x8
    addi x12, x12, -1
clip_350end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_351high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_351end
clip_351high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_351end
    lui x13, 0x8
    addi x13, x13, -1
clip_351end:
    sw x10, 0(x18)
    sw x11, 4(x18)
    sw x12, 0(x19)
    sw x13, 4(x19)
    addi x18, x18, 8
    addi x19, x19, 8
    addi x17, x17, 8
    addi x20, x20, -1
    bne x20, x0, fft8_butterfly
    addi x18, x18, 32
    addi x23, x23, -1
    bne x23, x0, fft8_group
    lui x18, 0x10001
    addi x18, x18, 1024
    addi x23, x0, 1
fft16_group:
    addi x19, x18, 64
    lui x17, 0x10000
    addi x17, x17, 1408
    addi x20, x0, 8
fft16_butterfly:
    lw x24, 0(x19)
    lw x25, 4(x19)
    lw x26, 0(x18)
    lw x27, 4(x18)
    lh x8, 0(x17)
    lh x9, 2(x17)
    addi x10, x24, 0
    addi x11, x8, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    .insn r 0x0b, 1, 0, x10, x10, x11 # MUL16
    add x29, x29, x10
    srai x29, x29, 15
    add x10, x26, x28
    add x11, x27, x29
    sub x12, x26, x28
    sub x13, x27, x29
    srai x10, x10, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x10, x5, clip_352high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_352end
clip_352high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_352end
    lui x10, 0x8
    addi x10, x10, -1
clip_352end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_353high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_353end
clip_353high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_353end
    lui x11, 0x8
    addi x11, x11, -1
clip_353end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_354high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_354end
clip_354high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_354end
    lui x12, 0x8
    addi x12, x12, -1
clip_354end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_355high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_355end
clip_355high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_355end
    lui x13, 0x8
    addi x13, x13, -1
clip_355end:
    sw x10, 0(x18)
    sw x11, 4(x18)
    sw x12, 0(x19)
    sw x13, 4(x19)
    addi x18, x18, 8
    addi x19, x19, 8
    addi x17, x17, 4
    addi x20, x20, -1
    bne x20, x0, fft16_butterfly
    addi x18, x18, 64
    addi x23, x23, -1
    bne x23, x0, fft16_group
kernel_end:
    lui x30, 0x20000
    addi x30, x30, 0
    addi x10, x0, 1
    sw x10, 0(x30)
    ebreak
