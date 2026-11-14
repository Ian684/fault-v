.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 0
    lui x19, 0x10000
    addi x19, x19, 64
    addi x20, x0, 64
    addi x22, x0, 0
outer:
    lb x10, 0(x18)
    lb x11, 0(x19)
    xor x5, x10, 11
    bge x10, x0, mul_1_a
    sub x10, x0, 10
mul_1_a:
    bge x11, x0, mul_1_b
    sub x11, x0, 11
mul_1_b:
    addi x6, x0, 0
mul_1_loop:
    beq x11, x0, mul_1_done
    andi x7, x11, 1
    beq x7, x0, mul_1_skip
    add x6, x6, 10
mul_1_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_1_loop
mul_1_done:
    bge x5, x0, mul_1_positive
    sub x6, x0, 6
mul_1_positive:
    addi x10, x6, 0
    add x22, x22, 10
    addi x18, x18, 1
    addi x19, x19, 1
    addi x20, x20, -1
    bne x20, x0, outer
    sw x22, 128(x21)
kernel_end:
    addi x0, x0, 0
    lui x21, 0x20000
    addi x21, x21, 0
    addi x10, x0, 1
    sw x10, 0(x21)
    ebreak
