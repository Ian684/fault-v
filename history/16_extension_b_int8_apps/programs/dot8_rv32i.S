.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10001
    addi x18, x18, 1536
    lui x19, 0x10001
    addi x19, x19, 1600
    lui x23, 0x10001
    addi x23, x23, 1664
    lui x26, 0x10002
    addi x26, x26, -1664
    addi x20, x0, 16
outer:
    lw x24, 0(x18)
    lw x25, 0(x19)
    addi x22, x0, 0
    slli x10, x24, 28
    srai x10, x10, 28
    slli x11, x25, 28
    srai x11, x11, 28
    xor x5, x10, x11
    bge x10, x0, mul_37_a
    sub x10, x0, x10
mul_37_a:
    bge x11, x0, mul_37_b
    sub x11, x0, x11
mul_37_b:
    addi x6, x0, 0
mul_37_loop:
    beq x11, x0, mul_37_done
    andi x7, x11, 1
    beq x7, x0, mul_37_skip
    add x6, x6, x10
mul_37_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_37_loop
mul_37_done:
    bge x5, x0, mul_37_positive
    sub x6, x0, x6
mul_37_positive:
    addi x10, x6, 0
    add x22, x22, x10
    slli x10, x24, 24
    srai x10, x10, 28
    slli x11, x25, 24
    srai x11, x11, 28
    xor x5, x10, x11
    bge x10, x0, mul_38_a
    sub x10, x0, x10
mul_38_a:
    bge x11, x0, mul_38_b
    sub x11, x0, x11
mul_38_b:
    addi x6, x0, 0
mul_38_loop:
    beq x11, x0, mul_38_done
    andi x7, x11, 1
    beq x7, x0, mul_38_skip
    add x6, x6, x10
mul_38_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_38_loop
mul_38_done:
    bge x5, x0, mul_38_positive
    sub x6, x0, x6
mul_38_positive:
    addi x10, x6, 0
    add x22, x22, x10
    slli x10, x24, 20
    srai x10, x10, 28
    slli x11, x25, 20
    srai x11, x11, 28
    xor x5, x10, x11
    bge x10, x0, mul_39_a
    sub x10, x0, x10
mul_39_a:
    bge x11, x0, mul_39_b
    sub x11, x0, x11
mul_39_b:
    addi x6, x0, 0
mul_39_loop:
    beq x11, x0, mul_39_done
    andi x7, x11, 1
    beq x7, x0, mul_39_skip
    add x6, x6, x10
mul_39_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_39_loop
mul_39_done:
    bge x5, x0, mul_39_positive
    sub x6, x0, x6
mul_39_positive:
    addi x10, x6, 0
    add x22, x22, x10
    slli x10, x24, 16
    srai x10, x10, 28
    slli x11, x25, 16
    srai x11, x11, 28
    xor x5, x10, x11
    bge x10, x0, mul_40_a
    sub x10, x0, x10
mul_40_a:
    bge x11, x0, mul_40_b
    sub x11, x0, x11
mul_40_b:
    addi x6, x0, 0
mul_40_loop:
    beq x11, x0, mul_40_done
    andi x7, x11, 1
    beq x7, x0, mul_40_skip
    add x6, x6, x10
mul_40_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_40_loop
mul_40_done:
    bge x5, x0, mul_40_positive
    sub x6, x0, x6
mul_40_positive:
    addi x10, x6, 0
    add x22, x22, x10
    slli x10, x24, 12
    srai x10, x10, 28
    slli x11, x25, 12
    srai x11, x11, 28
    xor x5, x10, x11
    bge x10, x0, mul_41_a
    sub x10, x0, x10
mul_41_a:
    bge x11, x0, mul_41_b
    sub x11, x0, x11
mul_41_b:
    addi x6, x0, 0
mul_41_loop:
    beq x11, x0, mul_41_done
    andi x7, x11, 1
    beq x7, x0, mul_41_skip
    add x6, x6, x10
mul_41_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_41_loop
mul_41_done:
    bge x5, x0, mul_41_positive
    sub x6, x0, x6
mul_41_positive:
    addi x10, x6, 0
    add x22, x22, x10
    slli x10, x24, 8
    srai x10, x10, 28
    slli x11, x25, 8
    srai x11, x11, 28
    xor x5, x10, x11
    bge x10, x0, mul_42_a
    sub x10, x0, x10
mul_42_a:
    bge x11, x0, mul_42_b
    sub x11, x0, x11
mul_42_b:
    addi x6, x0, 0
mul_42_loop:
    beq x11, x0, mul_42_done
    andi x7, x11, 1
    beq x7, x0, mul_42_skip
    add x6, x6, x10
mul_42_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_42_loop
mul_42_done:
    bge x5, x0, mul_42_positive
    sub x6, x0, x6
mul_42_positive:
    addi x10, x6, 0
    add x22, x22, x10
    slli x10, x24, 4
    srai x10, x10, 28
    slli x11, x25, 4
    srai x11, x11, 28
    xor x5, x10, x11
    bge x10, x0, mul_43_a
    sub x10, x0, x10
mul_43_a:
    bge x11, x0, mul_43_b
    sub x11, x0, x11
mul_43_b:
    addi x6, x0, 0
mul_43_loop:
    beq x11, x0, mul_43_done
    andi x7, x11, 1
    beq x7, x0, mul_43_skip
    add x6, x6, x10
mul_43_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_43_loop
mul_43_done:
    bge x5, x0, mul_43_positive
    sub x6, x0, x6
mul_43_positive:
    addi x10, x6, 0
    add x22, x22, x10
    addi x10, x24, 0
    srai x10, x10, 28
    addi x11, x25, 0
    srai x11, x11, 28
    xor x5, x10, x11
    bge x10, x0, mul_44_a
    sub x10, x0, x10
mul_44_a:
    bge x11, x0, mul_44_b
    sub x11, x0, x11
mul_44_b:
    addi x6, x0, 0
mul_44_loop:
    beq x11, x0, mul_44_done
    andi x7, x11, 1
    beq x7, x0, mul_44_skip
    add x6, x6, x10
mul_44_skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_44_loop
mul_44_done:
    bge x5, x0, mul_44_positive
    sub x6, x0, x6
mul_44_positive:
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
