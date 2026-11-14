.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 768
    lui x19, 0x10000
    addi x19, x19, 896
    addi x20, x0, 16
    lh x8, 832(x21)
    lh x9, 834(x21)
    lh x12, 836(x21)
    lh x13, 838(x21)
    lh x14, 840(x21)
    lh x15, 842(x21)
    lh x16, 844(x21)
    lh x17, 846(x21)
outer:
    addi x22, x0, 0
    lh x10, 0(x18)
    addi x11, x8, 0
    xor x5, x10, 11
    bge x10, x0, mul_18_a
    sub x10, x0, 10
mul_18_a:
    bge x11, x0, mul_18_b
    sub x11, x0, 11
mul_18_b:
    addi x6, x0, 0
mul_18_loop:
    beq x11, x0, mul_18_done
    andi x7, x11, 1
    beq x7, x0, mul_18_skip
    add x6, x6, 10
mul_18_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_18_loop
mul_18_done:
    bge x5, x0, mul_18_positive
    sub x6, x0, 6
mul_18_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lh x10, 2(x18)
    addi x11, x9, 0
    xor x5, x10, 11
    bge x10, x0, mul_19_a
    sub x10, x0, 10
mul_19_a:
    bge x11, x0, mul_19_b
    sub x11, x0, 11
mul_19_b:
    addi x6, x0, 0
mul_19_loop:
    beq x11, x0, mul_19_done
    andi x7, x11, 1
    beq x7, x0, mul_19_skip
    add x6, x6, 10
mul_19_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_19_loop
mul_19_done:
    bge x5, x0, mul_19_positive
    sub x6, x0, 6
mul_19_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lh x10, 4(x18)
    addi x11, x12, 0
    xor x5, x10, 11
    bge x10, x0, mul_20_a
    sub x10, x0, 10
mul_20_a:
    bge x11, x0, mul_20_b
    sub x11, x0, 11
mul_20_b:
    addi x6, x0, 0
mul_20_loop:
    beq x11, x0, mul_20_done
    andi x7, x11, 1
    beq x7, x0, mul_20_skip
    add x6, x6, 10
mul_20_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_20_loop
mul_20_done:
    bge x5, x0, mul_20_positive
    sub x6, x0, 6
mul_20_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lh x10, 6(x18)
    addi x11, x13, 0
    xor x5, x10, 11
    bge x10, x0, mul_21_a
    sub x10, x0, 10
mul_21_a:
    bge x11, x0, mul_21_b
    sub x11, x0, 11
mul_21_b:
    addi x6, x0, 0
mul_21_loop:
    beq x11, x0, mul_21_done
    andi x7, x11, 1
    beq x7, x0, mul_21_skip
    add x6, x6, 10
mul_21_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_21_loop
mul_21_done:
    bge x5, x0, mul_21_positive
    sub x6, x0, 6
mul_21_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lh x10, 8(x18)
    addi x11, x14, 0
    xor x5, x10, 11
    bge x10, x0, mul_22_a
    sub x10, x0, 10
mul_22_a:
    bge x11, x0, mul_22_b
    sub x11, x0, 11
mul_22_b:
    addi x6, x0, 0
mul_22_loop:
    beq x11, x0, mul_22_done
    andi x7, x11, 1
    beq x7, x0, mul_22_skip
    add x6, x6, 10
mul_22_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_22_loop
mul_22_done:
    bge x5, x0, mul_22_positive
    sub x6, x0, 6
mul_22_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lh x10, 10(x18)
    addi x11, x15, 0
    xor x5, x10, 11
    bge x10, x0, mul_23_a
    sub x10, x0, 10
mul_23_a:
    bge x11, x0, mul_23_b
    sub x11, x0, 11
mul_23_b:
    addi x6, x0, 0
mul_23_loop:
    beq x11, x0, mul_23_done
    andi x7, x11, 1
    beq x7, x0, mul_23_skip
    add x6, x6, 10
mul_23_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_23_loop
mul_23_done:
    bge x5, x0, mul_23_positive
    sub x6, x0, 6
mul_23_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lh x10, 12(x18)
    addi x11, x16, 0
    xor x5, x10, 11
    bge x10, x0, mul_24_a
    sub x10, x0, 10
mul_24_a:
    bge x11, x0, mul_24_b
    sub x11, x0, 11
mul_24_b:
    addi x6, x0, 0
mul_24_loop:
    beq x11, x0, mul_24_done
    andi x7, x11, 1
    beq x7, x0, mul_24_skip
    add x6, x6, 10
mul_24_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_24_loop
mul_24_done:
    bge x5, x0, mul_24_positive
    sub x6, x0, 6
mul_24_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lh x10, 14(x18)
    addi x11, x17, 0
    xor x5, x10, 11
    bge x10, x0, mul_25_a
    sub x10, x0, 10
mul_25_a:
    bge x11, x0, mul_25_b
    sub x11, x0, 11
mul_25_b:
    addi x6, x0, 0
mul_25_loop:
    beq x11, x0, mul_25_done
    andi x7, x11, 1
    beq x7, x0, mul_25_skip
    add x6, x6, 10
mul_25_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_25_loop
mul_25_done:
    bge x5, x0, mul_25_positive
    sub x6, x0, 6
mul_25_positive:
    addi x10, x6, 0
    add x22, x22, 10
    sw x22, 0(x19)
    addi x18, x18, 2
    addi x19, x19, 4
    addi x20, x20, -1
    bne x20, x0, outer
kernel_end:
    addi x0, x0, 0
    lui x21, 0x20000
    addi x21, x21, 0
    addi x10, x0, 1
    sw x10, 0(x21)
    ebreak
