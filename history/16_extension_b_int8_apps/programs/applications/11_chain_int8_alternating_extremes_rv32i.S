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
    bge x10, x0, mul_106a
    sub x10, x0, x10
mul_106a:
    bge x11, x0, mul_106b
    sub x11, x0, x11
mul_106b:
    addi x6, x0, 0
mul_106loop:
    beq x11, x0, mul_106done
    andi x7, x11, 1
    beq x7, x0, mul_106skip
    add x6, x6, x10
mul_106skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_106loop
mul_106done:
    bge x5, x0, mul_106positive
    sub x6, x0, x6
mul_106positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_107a
    sub x10, x0, x10
mul_107a:
    bge x11, x0, mul_107b
    sub x11, x0, x11
mul_107b:
    addi x6, x0, 0
mul_107loop:
    beq x11, x0, mul_107done
    andi x7, x11, 1
    beq x7, x0, mul_107skip
    add x6, x6, x10
mul_107skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_107loop
mul_107done:
    bge x5, x0, mul_107positive
    sub x6, x0, x6
mul_107positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_108a
    sub x10, x0, x10
mul_108a:
    bge x11, x0, mul_108b
    sub x11, x0, x11
mul_108b:
    addi x6, x0, 0
mul_108loop:
    beq x11, x0, mul_108done
    andi x7, x11, 1
    beq x7, x0, mul_108skip
    add x6, x6, x10
mul_108skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_108loop
mul_108done:
    bge x5, x0, mul_108positive
    sub x6, x0, x6
mul_108positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_109a
    sub x10, x0, x10
mul_109a:
    bge x11, x0, mul_109b
    sub x11, x0, x11
mul_109b:
    addi x6, x0, 0
mul_109loop:
    beq x11, x0, mul_109done
    andi x7, x11, 1
    beq x7, x0, mul_109skip
    add x6, x6, x10
mul_109skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_109loop
mul_109done:
    bge x5, x0, mul_109positive
    sub x6, x0, x6
mul_109positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_110a
    sub x10, x0, x10
mul_110a:
    bge x11, x0, mul_110b
    sub x11, x0, x11
mul_110b:
    addi x6, x0, 0
mul_110loop:
    beq x11, x0, mul_110done
    andi x7, x11, 1
    beq x7, x0, mul_110skip
    add x6, x6, x10
mul_110skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_110loop
mul_110done:
    bge x5, x0, mul_110positive
    sub x6, x0, x6
mul_110positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_111a
    sub x10, x0, x10
mul_111a:
    bge x11, x0, mul_111b
    sub x11, x0, x11
mul_111b:
    addi x6, x0, 0
mul_111loop:
    beq x11, x0, mul_111done
    andi x7, x11, 1
    beq x7, x0, mul_111skip
    add x6, x6, x10
mul_111skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_111loop
mul_111done:
    bge x5, x0, mul_111positive
    sub x6, x0, x6
mul_111positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_112a
    sub x10, x0, x10
mul_112a:
    bge x11, x0, mul_112b
    sub x11, x0, x11
mul_112b:
    addi x6, x0, 0
mul_112loop:
    beq x11, x0, mul_112done
    andi x7, x11, 1
    beq x7, x0, mul_112skip
    add x6, x6, x10
mul_112skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_112loop
mul_112done:
    bge x5, x0, mul_112positive
    sub x6, x0, x6
mul_112positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_113abs
    sub x10, x0, x10
round_113abs:
    beq x12, x0, round_113shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_113shift:
    srl x10, x10, x12
    bge x14, x0, round_113pos
    sub x10, x0, x10
round_113pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_114high
    addi x10, x0, -128
    jal x0, clip_114end
clip_114high:
    addi x5, x0, 127
    bge x5, x10, clip_114end
    addi x10, x0, 127
clip_114end:
    bge x10, x0, relu_115
    addi x10, x0, 0
relu_115:
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
    bge x10, x0, mul_116a
    sub x10, x0, x10
mul_116a:
    bge x11, x0, mul_116b
    sub x11, x0, x11
mul_116b:
    addi x6, x0, 0
mul_116loop:
    beq x11, x0, mul_116done
    andi x7, x11, 1
    beq x7, x0, mul_116skip
    add x6, x6, x10
mul_116skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_116loop
mul_116done:
    bge x5, x0, mul_116positive
    sub x6, x0, x6
mul_116positive:
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
    bge x10, x0, mul_117a
    sub x10, x0, x10
mul_117a:
    bge x11, x0, mul_117b
    sub x11, x0, x11
mul_117b:
    addi x6, x0, 0
mul_117loop:
    beq x11, x0, mul_117done
    andi x7, x11, 1
    beq x7, x0, mul_117skip
    add x6, x6, x10
mul_117skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_117loop
mul_117done:
    bge x5, x0, mul_117positive
    sub x6, x0, x6
mul_117positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_118abs
    sub x10, x0, x10
round_118abs:
    beq x12, x0, round_118shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_118shift:
    srl x10, x10, x12
    bge x14, x0, round_118pos
    sub x10, x0, x10
round_118pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_119high
    addi x10, x0, -128
    jal x0, clip_119end
clip_119high:
    addi x5, x0, 127
    bge x5, x10, clip_119end
    addi x10, x0, 127
clip_119end:
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
