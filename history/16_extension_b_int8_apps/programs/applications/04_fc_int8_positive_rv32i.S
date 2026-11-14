.section .text
.globl _start
_start:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x19, 0x10000
    addi x19, x19, 384
    lui x28, 0x10000
    addi x28, x28, 512
    lui x29, 0x10000
    addi x29, x29, 528
    lui x26, 0x10001
    addi x26, x26, 256
    lui x27, 0x10001
    addi x27, x27, -1792
    addi x20, x0, 4
fc_neuron:
    lui x18, 0x10000
    addi x18, x18, 256
    lw x22, 0(x28)
    addi x23, x0, 24
fc_inner:
    lb x10, 0(x18)
    lb x11, 0(x19)
    xor x5, x10, x11
    bge x10, x0, mul_42a
    sub x10, x0, x10
mul_42a:
    bge x11, x0, mul_42b
    sub x11, x0, x11
mul_42b:
    addi x6, x0, 0
mul_42loop:
    beq x11, x0, mul_42done
    andi x7, x11, 1
    beq x7, x0, mul_42skip
    add x6, x6, x10
mul_42skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_42loop
mul_42done:
    bge x5, x0, mul_42positive
    sub x6, x0, x6
mul_42positive:
    addi x10, x6, 0
    add x22, x22, x10
    addi x18, x18, 1
    addi x19, x19, 1
    addi x23, x23, -1
    bne x23, x0, fc_inner
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_43a
    sub x10, x0, x10
mul_43a:
    bge x11, x0, mul_43b
    sub x11, x0, x11
mul_43b:
    addi x6, x0, 0
mul_43loop:
    beq x11, x0, mul_43done
    andi x7, x11, 1
    beq x7, x0, mul_43skip
    add x6, x6, x10
mul_43skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_43loop
mul_43done:
    bge x5, x0, mul_43positive
    sub x6, x0, x6
mul_43positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_44abs
    sub x10, x0, x10
round_44abs:
    beq x12, x0, round_44shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_44shift:
    srl x10, x10, x12
    bge x14, x0, round_44pos
    sub x10, x0, x10
round_44pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_45high
    addi x10, x0, -128
    jal x0, clip_45end
clip_45high:
    addi x5, x0, 127
    bge x5, x10, clip_45end
    addi x10, x0, 127
clip_45end:
    sb x10, 0(x26)
    addi x28, x28, 4
    addi x29, x29, 4
    addi x26, x26, 1
    addi x27, x27, 4
    addi x20, x20, -1
    bne x20, x0, fc_neuron
    lui x18, 0x10001
    addi x18, x18, 256
    lb x22, 0(x18)
    addi x24, x0, 0
    addi x20, x0, 1
    addi x23, x0, 4
argmax:
    add x19, x18, x20
    lb x10, 0(x19)
    bge x22, x10, argmax_skip
    addi x22, x10, 0
    addi x24, x20, 0
argmax_skip:
    addi x20, x20, 1
    bne x20, x23, argmax
    lui x19, 0x10001
    addi x19, x19, 272
    sw x24, 0(x19)
kernel_end:
    lui x30, 0x20000
    addi x30, x30, 0
    addi x10, x0, 1
    sw x10, 0(x30)
    ebreak
