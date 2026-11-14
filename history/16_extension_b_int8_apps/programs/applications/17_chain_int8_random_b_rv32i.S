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
    bge x10, x0, mul_166a
    sub x10, x0, x10
mul_166a:
    bge x11, x0, mul_166b
    sub x11, x0, x11
mul_166b:
    addi x6, x0, 0
mul_166loop:
    beq x11, x0, mul_166done
    andi x7, x11, 1
    beq x7, x0, mul_166skip
    add x6, x6, x10
mul_166skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_166loop
mul_166done:
    bge x5, x0, mul_166positive
    sub x6, x0, x6
mul_166positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_167a
    sub x10, x0, x10
mul_167a:
    bge x11, x0, mul_167b
    sub x11, x0, x11
mul_167b:
    addi x6, x0, 0
mul_167loop:
    beq x11, x0, mul_167done
    andi x7, x11, 1
    beq x7, x0, mul_167skip
    add x6, x6, x10
mul_167skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_167loop
mul_167done:
    bge x5, x0, mul_167positive
    sub x6, x0, x6
mul_167positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_168a
    sub x10, x0, x10
mul_168a:
    bge x11, x0, mul_168b
    sub x11, x0, x11
mul_168b:
    addi x6, x0, 0
mul_168loop:
    beq x11, x0, mul_168done
    andi x7, x11, 1
    beq x7, x0, mul_168skip
    add x6, x6, x10
mul_168skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_168loop
mul_168done:
    bge x5, x0, mul_168positive
    sub x6, x0, x6
mul_168positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_169a
    sub x10, x0, x10
mul_169a:
    bge x11, x0, mul_169b
    sub x11, x0, x11
mul_169b:
    addi x6, x0, 0
mul_169loop:
    beq x11, x0, mul_169done
    andi x7, x11, 1
    beq x7, x0, mul_169skip
    add x6, x6, x10
mul_169skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_169loop
mul_169done:
    bge x5, x0, mul_169positive
    sub x6, x0, x6
mul_169positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_170a
    sub x10, x0, x10
mul_170a:
    bge x11, x0, mul_170b
    sub x11, x0, x11
mul_170b:
    addi x6, x0, 0
mul_170loop:
    beq x11, x0, mul_170done
    andi x7, x11, 1
    beq x7, x0, mul_170skip
    add x6, x6, x10
mul_170skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_170loop
mul_170done:
    bge x5, x0, mul_170positive
    sub x6, x0, x6
mul_170positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_171a
    sub x10, x0, x10
mul_171a:
    bge x11, x0, mul_171b
    sub x11, x0, x11
mul_171b:
    addi x6, x0, 0
mul_171loop:
    beq x11, x0, mul_171done
    andi x7, x11, 1
    beq x7, x0, mul_171skip
    add x6, x6, x10
mul_171skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_171loop
mul_171done:
    bge x5, x0, mul_171positive
    sub x6, x0, x6
mul_171positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_172a
    sub x10, x0, x10
mul_172a:
    bge x11, x0, mul_172b
    sub x11, x0, x11
mul_172b:
    addi x6, x0, 0
mul_172loop:
    beq x11, x0, mul_172done
    andi x7, x11, 1
    beq x7, x0, mul_172skip
    add x6, x6, x10
mul_172skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_172loop
mul_172done:
    bge x5, x0, mul_172positive
    sub x6, x0, x6
mul_172positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_173abs
    sub x10, x0, x10
round_173abs:
    beq x12, x0, round_173shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_173shift:
    srl x10, x10, x12
    bge x14, x0, round_173pos
    sub x10, x0, x10
round_173pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_174high
    addi x10, x0, -128
    jal x0, clip_174end
clip_174high:
    addi x5, x0, 127
    bge x5, x10, clip_174end
    addi x10, x0, 127
clip_174end:
    bge x10, x0, relu_175
    addi x10, x0, 0
relu_175:
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
    bge x10, x0, mul_176a
    sub x10, x0, x10
mul_176a:
    bge x11, x0, mul_176b
    sub x11, x0, x11
mul_176b:
    addi x6, x0, 0
mul_176loop:
    beq x11, x0, mul_176done
    andi x7, x11, 1
    beq x7, x0, mul_176skip
    add x6, x6, x10
mul_176skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_176loop
mul_176done:
    bge x5, x0, mul_176positive
    sub x6, x0, x6
mul_176positive:
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
    bge x10, x0, mul_177a
    sub x10, x0, x10
mul_177a:
    bge x11, x0, mul_177b
    sub x11, x0, x11
mul_177b:
    addi x6, x0, 0
mul_177loop:
    beq x11, x0, mul_177done
    andi x7, x11, 1
    beq x7, x0, mul_177skip
    add x6, x6, x10
mul_177skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_177loop
mul_177done:
    bge x5, x0, mul_177positive
    sub x6, x0, x6
mul_177positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_178abs
    sub x10, x0, x10
round_178abs:
    beq x12, x0, round_178shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_178shift:
    srl x10, x10, x12
    bge x14, x0, round_178pos
    sub x10, x0, x10
round_178pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_179high
    addi x10, x0, -128
    jal x0, clip_179end
clip_179high:
    addi x5, x0, 127
    bge x5, x10, clip_179end
    addi x10, x0, 127
clip_179end:
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
