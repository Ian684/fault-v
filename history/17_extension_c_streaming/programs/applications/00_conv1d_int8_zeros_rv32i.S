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
    bge x10, x0, mul_1a
    sub x10, x0, x10
mul_1a:
    bge x11, x0, mul_1b
    sub x11, x0, x11
mul_1b:
    addi x6, x0, 0
mul_1loop:
    beq x11, x0, mul_1done
    andi x7, x11, 1
    beq x7, x0, mul_1skip
    add x6, x6, x10
mul_1skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_1loop
mul_1done:
    bge x5, x0, mul_1positive
    sub x6, x0, x6
mul_1positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_2a
    sub x10, x0, x10
mul_2a:
    bge x11, x0, mul_2b
    sub x11, x0, x11
mul_2b:
    addi x6, x0, 0
mul_2loop:
    beq x11, x0, mul_2done
    andi x7, x11, 1
    beq x7, x0, mul_2skip
    add x6, x6, x10
mul_2skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_2loop
mul_2done:
    bge x5, x0, mul_2positive
    sub x6, x0, x6
mul_2positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_3a
    sub x10, x0, x10
mul_3a:
    bge x11, x0, mul_3b
    sub x11, x0, x11
mul_3b:
    addi x6, x0, 0
mul_3loop:
    beq x11, x0, mul_3done
    andi x7, x11, 1
    beq x7, x0, mul_3skip
    add x6, x6, x10
mul_3skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_3loop
mul_3done:
    bge x5, x0, mul_3positive
    sub x6, x0, x6
mul_3positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_4a
    sub x10, x0, x10
mul_4a:
    bge x11, x0, mul_4b
    sub x11, x0, x11
mul_4b:
    addi x6, x0, 0
mul_4loop:
    beq x11, x0, mul_4done
    andi x7, x11, 1
    beq x7, x0, mul_4skip
    add x6, x6, x10
mul_4skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_4loop
mul_4done:
    bge x5, x0, mul_4positive
    sub x6, x0, x6
mul_4positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_5a
    sub x10, x0, x10
mul_5a:
    bge x11, x0, mul_5b
    sub x11, x0, x11
mul_5b:
    addi x6, x0, 0
mul_5loop:
    beq x11, x0, mul_5done
    andi x7, x11, 1
    beq x7, x0, mul_5skip
    add x6, x6, x10
mul_5skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_5loop
mul_5done:
    bge x5, x0, mul_5positive
    sub x6, x0, x6
mul_5positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_6a
    sub x10, x0, x10
mul_6a:
    bge x11, x0, mul_6b
    sub x11, x0, x11
mul_6b:
    addi x6, x0, 0
mul_6loop:
    beq x11, x0, mul_6done
    andi x7, x11, 1
    beq x7, x0, mul_6skip
    add x6, x6, x10
mul_6skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_6loop
mul_6done:
    bge x5, x0, mul_6positive
    sub x6, x0, x6
mul_6positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_7a
    sub x10, x0, x10
mul_7a:
    bge x11, x0, mul_7b
    sub x11, x0, x11
mul_7b:
    addi x6, x0, 0
mul_7loop:
    beq x11, x0, mul_7done
    andi x7, x11, 1
    beq x7, x0, mul_7skip
    add x6, x6, x10
mul_7skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_7loop
mul_7done:
    bge x5, x0, mul_7positive
    sub x6, x0, x6
mul_7positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_8abs
    sub x10, x0, x10
round_8abs:
    beq x12, x0, round_8shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_8shift:
    srl x10, x10, x12
    bge x14, x0, round_8pos
    sub x10, x0, x10
round_8pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_9high
    addi x10, x0, -128
    jal x0, clip_9end
clip_9high:
    addi x5, x0, 127
    bge x5, x10, clip_9end
    addi x10, x0, 127
clip_9end:
    bge x10, x0, relu_10
    addi x10, x0, 0
relu_10:
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
kernel_end:
    lui x30, 0x20000
    addi x30, x30, 0
    addi x10, x0, 1
    sw x10, 0(x30)
    ebreak
