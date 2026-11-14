.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10001
    addi x18, x18, 1280
    lui x19, 0x10001
    addi x19, x19, 1344
    lui x23, 0x10001
    addi x23, x23, 1408
    lui x26, 0x10002
    addi x26, x26, -1728
    addi x20, x0, 16
outer:
    lw x24, 0(x18)
    lw x25, 0(x19)
    slli x10, x24, 16
    srai x10, x10, 16
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_34_a
    sub x10, x0, x10
mul_34_a:
    bge x11, x0, mul_34_b
    sub x11, x0, x11
mul_34_b:
    addi x6, x0, 0
mul_34_loop:
    beq x11, x0, mul_34_done
    andi x7, x11, 1
    beq x7, x0, mul_34_skip
    add x6, x6, x10
mul_34_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_34_loop
mul_34_done:
    bge x5, x0, mul_34_positive
    sub x6, x0, x6
mul_34_positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x24, 0
    srai x10, x10, 16
    addi x11, x25, 0
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_35_a
    sub x10, x0, x10
mul_35_a:
    bge x11, x0, mul_35_b
    sub x11, x0, x11
mul_35_b:
    addi x6, x0, 0
mul_35_loop:
    beq x11, x0, mul_35_done
    andi x7, x11, 1
    beq x7, x0, mul_35_skip
    add x6, x6, x10
mul_35_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_35_loop
mul_35_done:
    bge x5, x0, mul_35_positive
    sub x6, x0, x6
mul_35_positive:
    addi x10, x6, 0
    addi x11, x10, 0
    addi x10, x28, 0
    add x5, x10, x11
    xor x6, x10, x11
    blt x6, x0, sat_36_normal
    xor x6, x10, x5
    bge x6, x0, sat_36_normal
    srli x6, x10, 31
    lui x10, 0x80000
    addi x10, x10, -1
    add x10, x10, x6
    jal x0, sat_36_end
sat_36_normal:
    addi x10, x5, 0
sat_36_end:
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
