.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10001
    addi x18, x18, -2048
    lui x19, 0x10000
    addi x19, x19, 384
    addi x20, x0, 16
    lb x8, 320(x21)
    lb x9, 321(x21)
    lb x12, 322(x21)
    lb x13, 323(x21)
    lb x14, 324(x21)
    lb x15, 325(x21)
    lb x16, 326(x21)
    lb x17, 327(x21)
outer:
    addi x22, x0, 0
    lw x24, 0(x18)
    lw x25, 4(x18)
    slli x10, x24, 24
    srai x10, x10, 24
    addi x11, x8, 0
    xor x5, x10, 11
    bge x10, x0, mul_10_a
    sub x10, x0, 10
mul_10_a:
    bge x11, x0, mul_10_b
    sub x11, x0, 11
mul_10_b:
    addi x6, x0, 0
mul_10_loop:
    beq x11, x0, mul_10_done
    andi x7, x11, 1
    beq x7, x0, mul_10_skip
    add x6, x6, 10
mul_10_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_10_loop
mul_10_done:
    bge x5, x0, mul_10_positive
    sub x6, x0, 6
mul_10_positive:
    addi x10, x6, 0
    add x22, x22, 10
    slli x10, x24, 16
    srai x10, x10, 24
    addi x11, x9, 0
    xor x5, x10, 11
    bge x10, x0, mul_11_a
    sub x10, x0, 10
mul_11_a:
    bge x11, x0, mul_11_b
    sub x11, x0, 11
mul_11_b:
    addi x6, x0, 0
mul_11_loop:
    beq x11, x0, mul_11_done
    andi x7, x11, 1
    beq x7, x0, mul_11_skip
    add x6, x6, 10
mul_11_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_11_loop
mul_11_done:
    bge x5, x0, mul_11_positive
    sub x6, x0, 6
mul_11_positive:
    addi x10, x6, 0
    add x22, x22, 10
    slli x10, x24, 8
    srai x10, x10, 24
    addi x11, x12, 0
    xor x5, x10, 11
    bge x10, x0, mul_12_a
    sub x10, x0, 10
mul_12_a:
    bge x11, x0, mul_12_b
    sub x11, x0, 11
mul_12_b:
    addi x6, x0, 0
mul_12_loop:
    beq x11, x0, mul_12_done
    andi x7, x11, 1
    beq x7, x0, mul_12_skip
    add x6, x6, 10
mul_12_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_12_loop
mul_12_done:
    bge x5, x0, mul_12_positive
    sub x6, x0, 6
mul_12_positive:
    addi x10, x6, 0
    add x22, x22, 10
    addi x10, x24, 0
    srai x10, x10, 24
    addi x11, x13, 0
    xor x5, x10, 11
    bge x10, x0, mul_13_a
    sub x10, x0, 10
mul_13_a:
    bge x11, x0, mul_13_b
    sub x11, x0, 11
mul_13_b:
    addi x6, x0, 0
mul_13_loop:
    beq x11, x0, mul_13_done
    andi x7, x11, 1
    beq x7, x0, mul_13_skip
    add x6, x6, 10
mul_13_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_13_loop
mul_13_done:
    bge x5, x0, mul_13_positive
    sub x6, x0, 6
mul_13_positive:
    addi x10, x6, 0
    add x22, x22, 10
    slli x10, x25, 24
    srai x10, x10, 24
    addi x11, x14, 0
    xor x5, x10, 11
    bge x10, x0, mul_14_a
    sub x10, x0, 10
mul_14_a:
    bge x11, x0, mul_14_b
    sub x11, x0, 11
mul_14_b:
    addi x6, x0, 0
mul_14_loop:
    beq x11, x0, mul_14_done
    andi x7, x11, 1
    beq x7, x0, mul_14_skip
    add x6, x6, 10
mul_14_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_14_loop
mul_14_done:
    bge x5, x0, mul_14_positive
    sub x6, x0, 6
mul_14_positive:
    addi x10, x6, 0
    add x22, x22, 10
    slli x10, x25, 16
    srai x10, x10, 24
    addi x11, x15, 0
    xor x5, x10, 11
    bge x10, x0, mul_15_a
    sub x10, x0, 10
mul_15_a:
    bge x11, x0, mul_15_b
    sub x11, x0, 11
mul_15_b:
    addi x6, x0, 0
mul_15_loop:
    beq x11, x0, mul_15_done
    andi x7, x11, 1
    beq x7, x0, mul_15_skip
    add x6, x6, 10
mul_15_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_15_loop
mul_15_done:
    bge x5, x0, mul_15_positive
    sub x6, x0, 6
mul_15_positive:
    addi x10, x6, 0
    add x22, x22, 10
    slli x10, x25, 8
    srai x10, x10, 24
    addi x11, x16, 0
    xor x5, x10, 11
    bge x10, x0, mul_16_a
    sub x10, x0, 10
mul_16_a:
    bge x11, x0, mul_16_b
    sub x11, x0, 11
mul_16_b:
    addi x6, x0, 0
mul_16_loop:
    beq x11, x0, mul_16_done
    andi x7, x11, 1
    beq x7, x0, mul_16_skip
    add x6, x6, 10
mul_16_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_16_loop
mul_16_done:
    bge x5, x0, mul_16_positive
    sub x6, x0, 6
mul_16_positive:
    addi x10, x6, 0
    add x22, x22, 10
    addi x10, x25, 0
    srai x10, x10, 24
    addi x11, x17, 0
    xor x5, x10, 11
    bge x10, x0, mul_17_a
    sub x10, x0, 10
mul_17_a:
    bge x11, x0, mul_17_b
    sub x11, x0, 11
mul_17_b:
    addi x6, x0, 0
mul_17_loop:
    beq x11, x0, mul_17_done
    andi x7, x11, 1
    beq x7, x0, mul_17_skip
    add x6, x6, 10
mul_17_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_17_loop
mul_17_done:
    bge x5, x0, mul_17_positive
    sub x6, x0, 6
mul_17_positive:
    addi x10, x6, 0
    add x22, x22, 10
    sw x22, 0(x19)
    addi x18, x18, 8
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
