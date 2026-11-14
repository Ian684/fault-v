.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 256
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
    lb x10, 0(x18)
    addi x11, x8, 0
    xor x5, x10, 11
    bge x10, x0, mul_2_a
    sub x10, x0, 10
mul_2_a:
    bge x11, x0, mul_2_b
    sub x11, x0, 11
mul_2_b:
    addi x6, x0, 0
mul_2_loop:
    beq x11, x0, mul_2_done
    andi x7, x11, 1
    beq x7, x0, mul_2_skip
    add x6, x6, 10
mul_2_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_2_loop
mul_2_done:
    bge x5, x0, mul_2_positive
    sub x6, x0, 6
mul_2_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lb x10, 1(x18)
    addi x11, x9, 0
    xor x5, x10, 11
    bge x10, x0, mul_3_a
    sub x10, x0, 10
mul_3_a:
    bge x11, x0, mul_3_b
    sub x11, x0, 11
mul_3_b:
    addi x6, x0, 0
mul_3_loop:
    beq x11, x0, mul_3_done
    andi x7, x11, 1
    beq x7, x0, mul_3_skip
    add x6, x6, 10
mul_3_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_3_loop
mul_3_done:
    bge x5, x0, mul_3_positive
    sub x6, x0, 6
mul_3_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lb x10, 2(x18)
    addi x11, x12, 0
    xor x5, x10, 11
    bge x10, x0, mul_4_a
    sub x10, x0, 10
mul_4_a:
    bge x11, x0, mul_4_b
    sub x11, x0, 11
mul_4_b:
    addi x6, x0, 0
mul_4_loop:
    beq x11, x0, mul_4_done
    andi x7, x11, 1
    beq x7, x0, mul_4_skip
    add x6, x6, 10
mul_4_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_4_loop
mul_4_done:
    bge x5, x0, mul_4_positive
    sub x6, x0, 6
mul_4_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lb x10, 3(x18)
    addi x11, x13, 0
    xor x5, x10, 11
    bge x10, x0, mul_5_a
    sub x10, x0, 10
mul_5_a:
    bge x11, x0, mul_5_b
    sub x11, x0, 11
mul_5_b:
    addi x6, x0, 0
mul_5_loop:
    beq x11, x0, mul_5_done
    andi x7, x11, 1
    beq x7, x0, mul_5_skip
    add x6, x6, 10
mul_5_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_5_loop
mul_5_done:
    bge x5, x0, mul_5_positive
    sub x6, x0, 6
mul_5_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lb x10, 4(x18)
    addi x11, x14, 0
    xor x5, x10, 11
    bge x10, x0, mul_6_a
    sub x10, x0, 10
mul_6_a:
    bge x11, x0, mul_6_b
    sub x11, x0, 11
mul_6_b:
    addi x6, x0, 0
mul_6_loop:
    beq x11, x0, mul_6_done
    andi x7, x11, 1
    beq x7, x0, mul_6_skip
    add x6, x6, 10
mul_6_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_6_loop
mul_6_done:
    bge x5, x0, mul_6_positive
    sub x6, x0, 6
mul_6_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lb x10, 5(x18)
    addi x11, x15, 0
    xor x5, x10, 11
    bge x10, x0, mul_7_a
    sub x10, x0, 10
mul_7_a:
    bge x11, x0, mul_7_b
    sub x11, x0, 11
mul_7_b:
    addi x6, x0, 0
mul_7_loop:
    beq x11, x0, mul_7_done
    andi x7, x11, 1
    beq x7, x0, mul_7_skip
    add x6, x6, 10
mul_7_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_7_loop
mul_7_done:
    bge x5, x0, mul_7_positive
    sub x6, x0, 6
mul_7_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lb x10, 6(x18)
    addi x11, x16, 0
    xor x5, x10, 11
    bge x10, x0, mul_8_a
    sub x10, x0, 10
mul_8_a:
    bge x11, x0, mul_8_b
    sub x11, x0, 11
mul_8_b:
    addi x6, x0, 0
mul_8_loop:
    beq x11, x0, mul_8_done
    andi x7, x11, 1
    beq x7, x0, mul_8_skip
    add x6, x6, 10
mul_8_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_8_loop
mul_8_done:
    bge x5, x0, mul_8_positive
    sub x6, x0, 6
mul_8_positive:
    addi x10, x6, 0
    add x22, x22, 10
    lb x10, 7(x18)
    addi x11, x17, 0
    xor x5, x10, 11
    bge x10, x0, mul_9_a
    sub x10, x0, 10
mul_9_a:
    bge x11, x0, mul_9_b
    sub x11, x0, 11
mul_9_b:
    addi x6, x0, 0
mul_9_loop:
    beq x11, x0, mul_9_done
    andi x7, x11, 1
    beq x7, x0, mul_9_skip
    add x6, x6, 10
mul_9_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_9_loop
mul_9_done:
    bge x5, x0, mul_9_positive
    sub x6, x0, 6
mul_9_positive:
    addi x10, x6, 0
    add x22, x22, 10
    sw x22, 0(x19)
    addi x18, x18, 1
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
