.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10001
    addi x18, x18, 1792
    lui x19, 0x10001
    addi x19, x19, 1856
    lui x23, 0x10001
    addi x23, x23, 1920
    lui x26, 0x10002
    addi x26, x26, -1600
    addi x20, x0, 16
outer:
    lw x24, 0(x18)
    lw x25, 0(x19)
    addi x22, x0, 0
    slli x10, x24, 24
    srai x10, x10, 24
    srli x11, x25, 0
    andi x11, x11, 255
    xor x5, x10, x11
    bge x10, x0, mul_45_a
    sub x10, x0, x10
mul_45_a:
    bge x11, x0, mul_45_b
    sub x11, x0, x11
mul_45_b:
    addi x6, x0, 0
mul_45_loop:
    beq x11, x0, mul_45_done
    andi x7, x11, 1
    beq x7, x0, mul_45_skip
    add x6, x6, x10
mul_45_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_45_loop
mul_45_done:
    bge x5, x0, mul_45_positive
    sub x6, x0, x6
mul_45_positive:
    addi x10, x6, 0
    add x22, x22, x10
    slli x10, x24, 16
    srai x10, x10, 24
    srli x11, x25, 8
    andi x11, x11, 255
    xor x5, x10, x11
    bge x10, x0, mul_46_a
    sub x10, x0, x10
mul_46_a:
    bge x11, x0, mul_46_b
    sub x11, x0, x11
mul_46_b:
    addi x6, x0, 0
mul_46_loop:
    beq x11, x0, mul_46_done
    andi x7, x11, 1
    beq x7, x0, mul_46_skip
    add x6, x6, x10
mul_46_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_46_loop
mul_46_done:
    bge x5, x0, mul_46_positive
    sub x6, x0, x6
mul_46_positive:
    addi x10, x6, 0
    add x22, x22, x10
    slli x10, x24, 8
    srai x10, x10, 24
    srli x11, x25, 16
    andi x11, x11, 255
    xor x5, x10, x11
    bge x10, x0, mul_47_a
    sub x10, x0, x10
mul_47_a:
    bge x11, x0, mul_47_b
    sub x11, x0, x11
mul_47_b:
    addi x6, x0, 0
mul_47_loop:
    beq x11, x0, mul_47_done
    andi x7, x11, 1
    beq x7, x0, mul_47_skip
    add x6, x6, x10
mul_47_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_47_loop
mul_47_done:
    bge x5, x0, mul_47_positive
    sub x6, x0, x6
mul_47_positive:
    addi x10, x6, 0
    add x22, x22, x10
    addi x10, x24, 0
    srai x10, x10, 24
    srli x11, x25, 24
    andi x11, x11, 255
    xor x5, x10, x11
    bge x10, x0, mul_48_a
    sub x10, x0, x10
mul_48_a:
    bge x11, x0, mul_48_b
    sub x11, x0, x11
mul_48_b:
    addi x6, x0, 0
mul_48_loop:
    beq x11, x0, mul_48_done
    andi x7, x11, 1
    beq x7, x0, mul_48_skip
    add x6, x6, x10
mul_48_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_48_loop
mul_48_done:
    bge x5, x0, mul_48_positive
    sub x6, x0, x6
mul_48_positive:
    addi x10, x6, 0
    add x22, x22, x10
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
