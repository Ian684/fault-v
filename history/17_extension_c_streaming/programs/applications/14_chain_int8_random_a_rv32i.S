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
    bge x10, x0, mul_136a
    sub x10, x0, x10
mul_136a:
    bge x11, x0, mul_136b
    sub x11, x0, x11
mul_136b:
    addi x6, x0, 0
mul_136loop:
    beq x11, x0, mul_136done
    andi x7, x11, 1
    beq x7, x0, mul_136skip
    add x6, x6, x10
mul_136skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_136loop
mul_136done:
    bge x5, x0, mul_136positive
    sub x6, x0, x6
mul_136positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_137a
    sub x10, x0, x10
mul_137a:
    bge x11, x0, mul_137b
    sub x11, x0, x11
mul_137b:
    addi x6, x0, 0
mul_137loop:
    beq x11, x0, mul_137done
    andi x7, x11, 1
    beq x7, x0, mul_137skip
    add x6, x6, x10
mul_137skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_137loop
mul_137done:
    bge x5, x0, mul_137positive
    sub x6, x0, x6
mul_137positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_138a
    sub x10, x0, x10
mul_138a:
    bge x11, x0, mul_138b
    sub x11, x0, x11
mul_138b:
    addi x6, x0, 0
mul_138loop:
    beq x11, x0, mul_138done
    andi x7, x11, 1
    beq x7, x0, mul_138skip
    add x6, x6, x10
mul_138skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_138loop
mul_138done:
    bge x5, x0, mul_138positive
    sub x6, x0, x6
mul_138positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_139a
    sub x10, x0, x10
mul_139a:
    bge x11, x0, mul_139b
    sub x11, x0, x11
mul_139b:
    addi x6, x0, 0
mul_139loop:
    beq x11, x0, mul_139done
    andi x7, x11, 1
    beq x7, x0, mul_139skip
    add x6, x6, x10
mul_139skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_139loop
mul_139done:
    bge x5, x0, mul_139positive
    sub x6, x0, x6
mul_139positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_140a
    sub x10, x0, x10
mul_140a:
    bge x11, x0, mul_140b
    sub x11, x0, x11
mul_140b:
    addi x6, x0, 0
mul_140loop:
    beq x11, x0, mul_140done
    andi x7, x11, 1
    beq x7, x0, mul_140skip
    add x6, x6, x10
mul_140skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_140loop
mul_140done:
    bge x5, x0, mul_140positive
    sub x6, x0, x6
mul_140positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_141a
    sub x10, x0, x10
mul_141a:
    bge x11, x0, mul_141b
    sub x11, x0, x11
mul_141b:
    addi x6, x0, 0
mul_141loop:
    beq x11, x0, mul_141done
    andi x7, x11, 1
    beq x7, x0, mul_141skip
    add x6, x6, x10
mul_141skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_141loop
mul_141done:
    bge x5, x0, mul_141positive
    sub x6, x0, x6
mul_141positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_142a
    sub x10, x0, x10
mul_142a:
    bge x11, x0, mul_142b
    sub x11, x0, x11
mul_142b:
    addi x6, x0, 0
mul_142loop:
    beq x11, x0, mul_142done
    andi x7, x11, 1
    beq x7, x0, mul_142skip
    add x6, x6, x10
mul_142skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_142loop
mul_142done:
    bge x5, x0, mul_142positive
    sub x6, x0, x6
mul_142positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_143abs
    sub x10, x0, x10
round_143abs:
    beq x12, x0, round_143shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_143shift:
    srl x10, x10, x12
    bge x14, x0, round_143pos
    sub x10, x0, x10
round_143pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_144high
    addi x10, x0, -128
    jal x0, clip_144end
clip_144high:
    addi x5, x0, 127
    bge x5, x10, clip_144end
    addi x10, x0, 127
clip_144end:
    bge x10, x0, relu_145
    addi x10, x0, 0
relu_145:
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
    bge x10, x0, mul_146a
    sub x10, x0, x10
mul_146a:
    bge x11, x0, mul_146b
    sub x11, x0, x11
mul_146b:
    addi x6, x0, 0
mul_146loop:
    beq x11, x0, mul_146done
    andi x7, x11, 1
    beq x7, x0, mul_146skip
    add x6, x6, x10
mul_146skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_146loop
mul_146done:
    bge x5, x0, mul_146positive
    sub x6, x0, x6
mul_146positive:
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
    bge x10, x0, mul_147a
    sub x10, x0, x10
mul_147a:
    bge x11, x0, mul_147b
    sub x11, x0, x11
mul_147b:
    addi x6, x0, 0
mul_147loop:
    beq x11, x0, mul_147done
    andi x7, x11, 1
    beq x7, x0, mul_147skip
    add x6, x6, x10
mul_147skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_147loop
mul_147done:
    bge x5, x0, mul_147positive
    sub x6, x0, x6
mul_147positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_148abs
    sub x10, x0, x10
round_148abs:
    beq x12, x0, round_148shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_148shift:
    srl x10, x10, x12
    bge x14, x0, round_148pos
    sub x10, x0, x10
round_148pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_149high
    addi x10, x0, -128
    jal x0, clip_149end
clip_149high:
    addi x5, x0, 127
    bge x5, x10, clip_149end
    addi x10, x0, 127
clip_149end:
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
