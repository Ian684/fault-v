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
    bge x10, x0, mul_46a
    sub x10, x0, x10
mul_46a:
    bge x11, x0, mul_46b
    sub x11, x0, x11
mul_46b:
    addi x6, x0, 0
mul_46loop:
    beq x11, x0, mul_46done
    andi x7, x11, 1
    beq x7, x0, mul_46skip
    add x6, x6, x10
mul_46skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_46loop
mul_46done:
    bge x5, x0, mul_46positive
    sub x6, x0, x6
mul_46positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_47a
    sub x10, x0, x10
mul_47a:
    bge x11, x0, mul_47b
    sub x11, x0, x11
mul_47b:
    addi x6, x0, 0
mul_47loop:
    beq x11, x0, mul_47done
    andi x7, x11, 1
    beq x7, x0, mul_47skip
    add x6, x6, x10
mul_47skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_47loop
mul_47done:
    bge x5, x0, mul_47positive
    sub x6, x0, x6
mul_47positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_48a
    sub x10, x0, x10
mul_48a:
    bge x11, x0, mul_48b
    sub x11, x0, x11
mul_48b:
    addi x6, x0, 0
mul_48loop:
    beq x11, x0, mul_48done
    andi x7, x11, 1
    beq x7, x0, mul_48skip
    add x6, x6, x10
mul_48skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_48loop
mul_48done:
    bge x5, x0, mul_48positive
    sub x6, x0, x6
mul_48positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_49a
    sub x10, x0, x10
mul_49a:
    bge x11, x0, mul_49b
    sub x11, x0, x11
mul_49b:
    addi x6, x0, 0
mul_49loop:
    beq x11, x0, mul_49done
    andi x7, x11, 1
    beq x7, x0, mul_49skip
    add x6, x6, x10
mul_49skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_49loop
mul_49done:
    bge x5, x0, mul_49positive
    sub x6, x0, x6
mul_49positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_50a
    sub x10, x0, x10
mul_50a:
    bge x11, x0, mul_50b
    sub x11, x0, x11
mul_50b:
    addi x6, x0, 0
mul_50loop:
    beq x11, x0, mul_50done
    andi x7, x11, 1
    beq x7, x0, mul_50skip
    add x6, x6, x10
mul_50skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_50loop
mul_50done:
    bge x5, x0, mul_50positive
    sub x6, x0, x6
mul_50positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_51a
    sub x10, x0, x10
mul_51a:
    bge x11, x0, mul_51b
    sub x11, x0, x11
mul_51b:
    addi x6, x0, 0
mul_51loop:
    beq x11, x0, mul_51done
    andi x7, x11, 1
    beq x7, x0, mul_51skip
    add x6, x6, x10
mul_51skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_51loop
mul_51done:
    bge x5, x0, mul_51positive
    sub x6, x0, x6
mul_51positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_52a
    sub x10, x0, x10
mul_52a:
    bge x11, x0, mul_52b
    sub x11, x0, x11
mul_52b:
    addi x6, x0, 0
mul_52loop:
    beq x11, x0, mul_52done
    andi x7, x11, 1
    beq x7, x0, mul_52skip
    add x6, x6, x10
mul_52skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_52loop
mul_52done:
    bge x5, x0, mul_52positive
    sub x6, x0, x6
mul_52positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_53abs
    sub x10, x0, x10
round_53abs:
    beq x12, x0, round_53shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_53shift:
    srl x10, x10, x12
    bge x14, x0, round_53pos
    sub x10, x0, x10
round_53pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_54high
    addi x10, x0, -128
    jal x0, clip_54end
clip_54high:
    addi x5, x0, 127
    bge x5, x10, clip_54end
    addi x10, x0, 127
clip_54end:
    bge x10, x0, relu_55
    addi x10, x0, 0
relu_55:
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
    bge x10, x0, mul_56a
    sub x10, x0, x10
mul_56a:
    bge x11, x0, mul_56b
    sub x11, x0, x11
mul_56b:
    addi x6, x0, 0
mul_56loop:
    beq x11, x0, mul_56done
    andi x7, x11, 1
    beq x7, x0, mul_56skip
    add x6, x6, x10
mul_56skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_56loop
mul_56done:
    bge x5, x0, mul_56positive
    sub x6, x0, x6
mul_56positive:
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
    bge x10, x0, mul_57a
    sub x10, x0, x10
mul_57a:
    bge x11, x0, mul_57b
    sub x11, x0, x11
mul_57b:
    addi x6, x0, 0
mul_57loop:
    beq x11, x0, mul_57done
    andi x7, x11, 1
    beq x7, x0, mul_57skip
    add x6, x6, x10
mul_57skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_57loop
mul_57done:
    bge x5, x0, mul_57positive
    sub x6, x0, x6
mul_57positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_58abs
    sub x10, x0, x10
round_58abs:
    beq x12, x0, round_58shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_58shift:
    srl x10, x10, x12
    bge x14, x0, round_58pos
    sub x10, x0, x10
round_58pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_59high
    addi x10, x0, -128
    jal x0, clip_59end
clip_59high:
    addi x5, x0, 127
    bge x5, x10, clip_59end
    addi x10, x0, 127
clip_59end:
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
