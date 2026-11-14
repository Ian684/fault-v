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
    bge x10, x0, mul_16a
    sub x10, x0, x10
mul_16a:
    bge x11, x0, mul_16b
    sub x11, x0, x11
mul_16b:
    addi x6, x0, 0
mul_16loop:
    beq x11, x0, mul_16done
    andi x7, x11, 1
    beq x7, x0, mul_16skip
    add x6, x6, x10
mul_16skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_16loop
mul_16done:
    bge x5, x0, mul_16positive
    sub x6, x0, x6
mul_16positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_17a
    sub x10, x0, x10
mul_17a:
    bge x11, x0, mul_17b
    sub x11, x0, x11
mul_17b:
    addi x6, x0, 0
mul_17loop:
    beq x11, x0, mul_17done
    andi x7, x11, 1
    beq x7, x0, mul_17skip
    add x6, x6, x10
mul_17skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_17loop
mul_17done:
    bge x5, x0, mul_17positive
    sub x6, x0, x6
mul_17positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_18a
    sub x10, x0, x10
mul_18a:
    bge x11, x0, mul_18b
    sub x11, x0, x11
mul_18b:
    addi x6, x0, 0
mul_18loop:
    beq x11, x0, mul_18done
    andi x7, x11, 1
    beq x7, x0, mul_18skip
    add x6, x6, x10
mul_18skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_18loop
mul_18done:
    bge x5, x0, mul_18positive
    sub x6, x0, x6
mul_18positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_19a
    sub x10, x0, x10
mul_19a:
    bge x11, x0, mul_19b
    sub x11, x0, x11
mul_19b:
    addi x6, x0, 0
mul_19loop:
    beq x11, x0, mul_19done
    andi x7, x11, 1
    beq x7, x0, mul_19skip
    add x6, x6, x10
mul_19skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_19loop
mul_19done:
    bge x5, x0, mul_19positive
    sub x6, x0, x6
mul_19positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_20a
    sub x10, x0, x10
mul_20a:
    bge x11, x0, mul_20b
    sub x11, x0, x11
mul_20b:
    addi x6, x0, 0
mul_20loop:
    beq x11, x0, mul_20done
    andi x7, x11, 1
    beq x7, x0, mul_20skip
    add x6, x6, x10
mul_20skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_20loop
mul_20done:
    bge x5, x0, mul_20positive
    sub x6, x0, x6
mul_20positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_21a
    sub x10, x0, x10
mul_21a:
    bge x11, x0, mul_21b
    sub x11, x0, x11
mul_21b:
    addi x6, x0, 0
mul_21loop:
    beq x11, x0, mul_21done
    andi x7, x11, 1
    beq x7, x0, mul_21skip
    add x6, x6, x10
mul_21skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_21loop
mul_21done:
    bge x5, x0, mul_21positive
    sub x6, x0, x6
mul_21positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_22a
    sub x10, x0, x10
mul_22a:
    bge x11, x0, mul_22b
    sub x11, x0, x11
mul_22b:
    addi x6, x0, 0
mul_22loop:
    beq x11, x0, mul_22done
    andi x7, x11, 1
    beq x7, x0, mul_22skip
    add x6, x6, x10
mul_22skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_22loop
mul_22done:
    bge x5, x0, mul_22positive
    sub x6, x0, x6
mul_22positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_23abs
    sub x10, x0, x10
round_23abs:
    beq x12, x0, round_23shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_23shift:
    srl x10, x10, x12
    bge x14, x0, round_23pos
    sub x10, x0, x10
round_23pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_24high
    addi x10, x0, -128
    jal x0, clip_24end
clip_24high:
    addi x5, x0, 127
    bge x5, x10, clip_24end
    addi x10, x0, 127
clip_24end:
    bge x10, x0, relu_25
    addi x10, x0, 0
relu_25:
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
    bge x10, x0, mul_26a
    sub x10, x0, x10
mul_26a:
    bge x11, x0, mul_26b
    sub x11, x0, x11
mul_26b:
    addi x6, x0, 0
mul_26loop:
    beq x11, x0, mul_26done
    andi x7, x11, 1
    beq x7, x0, mul_26skip
    add x6, x6, x10
mul_26skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_26loop
mul_26done:
    bge x5, x0, mul_26positive
    sub x6, x0, x6
mul_26positive:
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
    bge x10, x0, mul_27a
    sub x10, x0, x10
mul_27a:
    bge x11, x0, mul_27b
    sub x11, x0, x11
mul_27b:
    addi x6, x0, 0
mul_27loop:
    beq x11, x0, mul_27done
    andi x7, x11, 1
    beq x7, x0, mul_27skip
    add x6, x6, x10
mul_27skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_27loop
mul_27done:
    bge x5, x0, mul_27positive
    sub x6, x0, x6
mul_27positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_28abs
    sub x10, x0, x10
round_28abs:
    beq x12, x0, round_28shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_28shift:
    srl x10, x10, x12
    bge x14, x0, round_28pos
    sub x10, x0, x10
round_28pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_29high
    addi x10, x0, -128
    jal x0, clip_29end
clip_29high:
    addi x5, x0, 127
    bge x5, x10, clip_29end
    addi x10, x0, 127
clip_29end:
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
