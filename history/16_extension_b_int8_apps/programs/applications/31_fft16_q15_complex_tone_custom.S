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
    bge x10, x5, clip_436high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_436end
clip_436high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_436end
    lui x10, 0x8
    addi x10, x10, -1
clip_436end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_437high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_437end
clip_437high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_437end
    lui x11, 0x8
    addi x11, x11, -1
clip_437end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_438high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_438end
clip_438high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_438end
    lui x12, 0x8
    addi x12, x12, -1
clip_438end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_439high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_439end
clip_439high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_439end
    lui x13, 0x8
    addi x13, x13, -1
clip_439end:
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
    bge x10, x5, clip_440high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_440end
clip_440high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_440end
    lui x10, 0x8
    addi x10, x10, -1
clip_440end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_441high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_441end
clip_441high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_441end
    lui x11, 0x8
    addi x11, x11, -1
clip_441end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_442high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_442end
clip_442high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_442end
    lui x12, 0x8
    addi x12, x12, -1
clip_442end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_443high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_443end
clip_443high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_443end
    lui x13, 0x8
    addi x13, x13, -1
clip_443end:
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
    bge x10, x5, clip_444high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_444end
clip_444high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_444end
    lui x10, 0x8
    addi x10, x10, -1
clip_444end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_445high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_445end
clip_445high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_445end
    lui x11, 0x8
    addi x11, x11, -1
clip_445end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_446high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_446end
clip_446high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_446end
    lui x12, 0x8
    addi x12, x12, -1
clip_446end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_447high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_447end
clip_447high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_447end
    lui x13, 0x8
    addi x13, x13, -1
clip_447end:
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
    bge x10, x5, clip_448high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_448end
clip_448high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_448end
    lui x10, 0x8
    addi x10, x10, -1
clip_448end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_449high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_449end
clip_449high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_449end
    lui x11, 0x8
    addi x11, x11, -1
clip_449end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_450high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_450end
clip_450high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_450end
    lui x12, 0x8
    addi x12, x12, -1
clip_450end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_451high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_451end
clip_451high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_451end
    lui x13, 0x8
    addi x13, x13, -1
clip_451end:
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
