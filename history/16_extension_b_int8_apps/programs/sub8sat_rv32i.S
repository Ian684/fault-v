.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10001
    addi x18, x18, 768
    lui x19, 0x10001
    addi x19, x19, 832
    lui x23, 0x10001
    addi x23, x23, 896
    lui x26, 0x10002
    addi x26, x26, -1856
    addi x20, x0, 16
outer:
    lw x24, 0(x18)
    lw x25, 0(x19)
    addi x30, x0, 0
    slli x10, x24, 24
    srai x10, x10, 24
    slli x11, x25, 24
    srai x11, x11, 24
    sub x10, x10, x11
    addi x5, x0, -128
    bge x10, x5, clip_5_high
    addi x10, x0, -128
    jal x0, clip_5_end
clip_5_high:
    addi x5, x0, 127
    bge x5, x10, clip_5_end
    addi x10, x0, 127
clip_5_end:
    andi x10, x10, 255
    or x30, x30, x10
    slli x10, x24, 16
    srai x10, x10, 24
    slli x11, x25, 16
    srai x11, x11, 24
    sub x10, x10, x11
    addi x5, x0, -128
    bge x10, x5, clip_6_high
    addi x10, x0, -128
    jal x0, clip_6_end
clip_6_high:
    addi x5, x0, 127
    bge x5, x10, clip_6_end
    addi x10, x0, 127
clip_6_end:
    andi x10, x10, 255
    slli x10, x10, 8
    or x30, x30, x10
    slli x10, x24, 8
    srai x10, x10, 24
    slli x11, x25, 8
    srai x11, x11, 24
    sub x10, x10, x11
    addi x5, x0, -128
    bge x10, x5, clip_7_high
    addi x10, x0, -128
    jal x0, clip_7_end
clip_7_high:
    addi x5, x0, 127
    bge x5, x10, clip_7_end
    addi x10, x0, 127
clip_7_end:
    andi x10, x10, 255
    slli x10, x10, 16
    or x30, x30, x10
    addi x10, x24, 0
    srai x10, x10, 24
    addi x11, x25, 0
    srai x11, x11, 24
    sub x10, x10, x11
    addi x5, x0, -128
    bge x10, x5, clip_8_high
    addi x10, x0, -128
    jal x0, clip_8_end
clip_8_high:
    addi x5, x0, 127
    bge x5, x10, clip_8_end
    addi x10, x0, 127
clip_8_end:
    andi x10, x10, 255
    slli x10, x10, 24
    or x30, x30, x10
    addi x22, x30, 0
    sw x22, 0(x26)
    addi x18, x18, 4
    addi x19, x19, 4
    addi x26, x26, 4
    addi x20, x20, -1
    bne x20, x0, outer
kernel_end:
    lui x30, 0x20000
    addi x30, x30, 0
    addi x29, x0, 1
    sw x29, 0(x30)
    ebreak
