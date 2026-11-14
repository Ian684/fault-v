.section .text
.globl _start
_start:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 0
    lui x26, 0x10001
    addi x26, x26, 0
    lui x27, 0x10001
    addi x27, x27, -2048
    addi x20, x0, 8
conv_position:
    lui x19, 0x10000
    addi x19, x19, 64
    lui x28, 0x10000
    addi x28, x28, 128
    lui x29, 0x10000
    addi x29, x29, 144
    addi x23, x0, 3
conv_channel:
    lw x22, 0(x28)
    lb x10, 0(x18)
    lb x11, 0(x19)
    xor x5, x10, x11
    bge x10, x0, mul_76a
    sub x10, x0, x10
mul_76a:
    bge x11, x0, mul_76b
    sub x11, x0, x11
mul_76b:
    addi x6, x0, 0
mul_76loop:
    beq x11, x0, mul_76done
    andi x7, x11, 1
    beq x7, x0, mul_76skip
    add x6, x6, x10
mul_76skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_76loop
mul_76done:
    bge x5, x0, mul_76positive
    sub x6, x0, x6
mul_76positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_77a
    sub x10, x0, x10
mul_77a:
    bge x11, x0, mul_77b
    sub x11, x0, x11
mul_77b:
    addi x6, x0, 0
mul_77loop:
    beq x11, x0, mul_77done
    andi x7, x11, 1
    beq x7, x0, mul_77skip
    add x6, x6, x10
mul_77skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_77loop
mul_77done:
    bge x5, x0, mul_77positive
    sub x6, x0, x6
mul_77positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_78a
    sub x10, x0, x10
mul_78a:
    bge x11, x0, mul_78b
    sub x11, x0, x11
mul_78b:
    addi x6, x0, 0
mul_78loop:
    beq x11, x0, mul_78done
    andi x7, x11, 1
    beq x7, x0, mul_78skip
    add x6, x6, x10
mul_78skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_78loop
mul_78done:
    bge x5, x0, mul_78positive
    sub x6, x0, x6
mul_78positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_79a
    sub x10, x0, x10
mul_79a:
    bge x11, x0, mul_79b
    sub x11, x0, x11
mul_79b:
    addi x6, x0, 0
mul_79loop:
    beq x11, x0, mul_79done
    andi x7, x11, 1
    beq x7, x0, mul_79skip
    add x6, x6, x10
mul_79skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_79loop
mul_79done:
    bge x5, x0, mul_79positive
    sub x6, x0, x6
mul_79positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_80a
    sub x10, x0, x10
mul_80a:
    bge x11, x0, mul_80b
    sub x11, x0, x11
mul_80b:
    addi x6, x0, 0
mul_80loop:
    beq x11, x0, mul_80done
    andi x7, x11, 1
    beq x7, x0, mul_80skip
    add x6, x6, x10
mul_80skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_80loop
mul_80done:
    bge x5, x0, mul_80positive
    sub x6, x0, x6
mul_80positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_81a
    sub x10, x0, x10
mul_81a:
    bge x11, x0, mul_81b
    sub x11, x0, x11
mul_81b:
    addi x6, x0, 0
mul_81loop:
    beq x11, x0, mul_81done
    andi x7, x11, 1
    beq x7, x0, mul_81skip
    add x6, x6, x10
mul_81skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_81loop
mul_81done:
    bge x5, x0, mul_81positive
    sub x6, x0, x6
mul_81positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_82a
    sub x10, x0, x10
mul_82a:
    bge x11, x0, mul_82b
    sub x11, x0, x11
mul_82b:
    addi x6, x0, 0
mul_82loop:
    beq x11, x0, mul_82done
    andi x7, x11, 1
    beq x7, x0, mul_82skip
    add x6, x6, x10
mul_82skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_82loop
mul_82done:
    bge x5, x0, mul_82positive
    sub x6, x0, x6
mul_82positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_83abs
    sub x10, x0, x10
round_83abs:
    beq x12, x0, round_83shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_83shift:
    srl x10, x10, x12
    bge x14, x0, round_83pos
    sub x10, x0, x10
round_83pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_84high
    addi x10, x0, -128
    jal x0, clip_84end
clip_84high:
    addi x5, x0, 127
    bge x5, x10, clip_84end
    addi x10, x0, 127
clip_84end:
    bge x10, x0, relu_85
    addi x10, x0, 0
relu_85:
    sb x10, 0(x26)
    addi x19, x19, 6
    addi x28, x28, 4
    addi x29, x29, 4
    addi x27, x27, 4
    addi x26, x26, 1
    addi x23, x23, -1
    bne x23, x0, conv_channel
    addi x18, x18, 2
    addi x20, x20, -1
    bne x20, x0, conv_position
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
    lui x18, 0x10001
    addi x18, x18, 0
    lw x22, 0(x28)
    addi x23, x0, 24
fc_inner:
    lb x10, 0(x18)
    lb x11, 0(x19)
    xor x5, x10, x11
    bge x10, x0, mul_86a
    sub x10, x0, x10
mul_86a:
    bge x11, x0, mul_86b
    sub x11, x0, x11
mul_86b:
    addi x6, x0, 0
mul_86loop:
    beq x11, x0, mul_86done
    andi x7, x11, 1
    beq x7, x0, mul_86skip
    add x6, x6, x10
mul_86skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_86loop
mul_86done:
    bge x5, x0, mul_86positive
    sub x6, x0, x6
mul_86positive:
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
    bge x10, x0, mul_87a
    sub x10, x0, x10
mul_87a:
    bge x11, x0, mul_87b
    sub x11, x0, x11
mul_87b:
    addi x6, x0, 0
mul_87loop:
    beq x11, x0, mul_87done
    andi x7, x11, 1
    beq x7, x0, mul_87skip
    add x6, x6, x10
mul_87skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_87loop
mul_87done:
    bge x5, x0, mul_87positive
    sub x6, x0, x6
mul_87positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_88abs
    sub x10, x0, x10
round_88abs:
    beq x12, x0, round_88shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_88shift:
    srl x10, x10, x12
    bge x14, x0, round_88pos
    sub x10, x0, x10
round_88pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_89high
    addi x10, x0, -128
    jal x0, clip_89end
clip_89high:
    addi x5, x0, 127
    bge x5, x10, clip_89end
    addi x10, x0, 127
clip_89end:
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
