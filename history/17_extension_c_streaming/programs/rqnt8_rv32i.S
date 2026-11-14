.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10001
    addi x18, x18, 1024
    lui x19, 0x10001
    addi x19, x19, 1088
    lui x23, 0x10001
    addi x23, x23, 1152
    lui x26, 0x10002
    addi x26, x26, -1792
    addi x20, x0, 16
outer:
    lw x24, 0(x18)
    lw x25, 0(x19)
    addi x10, x24, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_33_a
    sub x10, x0, x10
mul_33_a:
    bge x11, x0, mul_33_b
    sub x11, x0, x11
mul_33_b:
    addi x6, x0, 0
mul_33_loop:
    beq x11, x0, mul_33_done
    andi x7, x11, 1
    beq x7, x0, mul_33_skip
    add x6, x6, x10
mul_33_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_33_loop
mul_33_done:
    bge x5, x0, mul_33_positive
    sub x6, x0, x6
mul_33_positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_9_abs
    sub x10, x0, x10
round_9_abs:
    beq x12, x0, round_9_shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_9_shift:
    srl x10, x10, x12
    bge x14, x0, round_9_positive
    sub x10, x0, x10
round_9_positive:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_10_high
    addi x10, x0, -128
    jal x0, clip_10_end
clip_10_high:
    addi x5, x0, 127
    bge x5, x10, clip_10_end
    addi x10, x0, 127
clip_10_end:
    addi x22, x10, 0
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
