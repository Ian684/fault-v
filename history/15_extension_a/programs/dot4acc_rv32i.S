.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10001
    addi x18, x18, 0
    lui x19, 0x10001
    addi x19, x19, 64
    lui x23, 0x10001
    addi x23, x23, 128
    lui x26, 0x10002
    addi x26, x26, -2048
    addi x20, x0, 16
outer:
    lw x24, 0(x18)
    lw x25, 0(x19)
    lw x22, 0(x23)
    slli x10, x24, 24
    srai x10, x10, 24
    slli x11, x25, 24
    srai x11, x11, 24
    xor x5, x10, x11
    bge x10, x0, mul_28_a
    sub x10, x0, x10
mul_28_a:
    bge x11, x0, mul_28_b
    sub x11, x0, x11
mul_28_b:
    addi x6, x0, 0
mul_28_loop:
    beq x11, x0, mul_28_done
    andi x7, x11, 1
    beq x7, x0, mul_28_skip
    add x6, x6, x10
mul_28_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_28_loop
mul_28_done:
    bge x5, x0, mul_28_positive
    sub x6, x0, x6
mul_28_positive:
    addi x10, x6, 0
    add x22, x22, x10
    slli x10, x24, 16
    srai x10, x10, 24
    slli x11, x25, 16
    srai x11, x11, 24
    xor x5, x10, x11
    bge x10, x0, mul_29_a
    sub x10, x0, x10
mul_29_a:
    bge x11, x0, mul_29_b
    sub x11, x0, x11
mul_29_b:
    addi x6, x0, 0
mul_29_loop:
    beq x11, x0, mul_29_done
    andi x7, x11, 1
    beq x7, x0, mul_29_skip
    add x6, x6, x10
mul_29_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_29_loop
mul_29_done:
    bge x5, x0, mul_29_positive
    sub x6, x0, x6
mul_29_positive:
    addi x10, x6, 0
    add x22, x22, x10
    slli x10, x24, 8
    srai x10, x10, 24
    slli x11, x25, 8
    srai x11, x11, 24
    xor x5, x10, x11
    bge x10, x0, mul_30_a
    sub x10, x0, x10
mul_30_a:
    bge x11, x0, mul_30_b
    sub x11, x0, x11
mul_30_b:
    addi x6, x0, 0
mul_30_loop:
    beq x11, x0, mul_30_done
    andi x7, x11, 1
    beq x7, x0, mul_30_skip
    add x6, x6, x10
mul_30_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_30_loop
mul_30_done:
    bge x5, x0, mul_30_positive
    sub x6, x0, x6
mul_30_positive:
    addi x10, x6, 0
    add x22, x22, x10
    addi x10, x24, 0
    srai x10, x10, 24
    addi x11, x25, 0
    srai x11, x11, 24
    xor x5, x10, x11
    bge x10, x0, mul_31_a
    sub x10, x0, x10
mul_31_a:
    bge x11, x0, mul_31_b
    sub x11, x0, x11
mul_31_b:
    addi x6, x0, 0
mul_31_loop:
    beq x11, x0, mul_31_done
    andi x7, x11, 1
    beq x7, x0, mul_31_skip
    add x6, x6, x10
mul_31_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_31_loop
mul_31_done:
    bge x5, x0, mul_31_positive
    sub x6, x0, x6
mul_31_positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x26)
    addi x18, x18, 4
    addi x19, x19, 4
    addi x23, x23, 4
    addi x26, x26, 4
    addi x20, x20, -1
    bne x20, x0, outer
kernel_end:
    lui x30, 0x20000
    addi x30, x30, 0
    addi x29, x0, 1
    sw x29, 0(x30)
    ebreak
