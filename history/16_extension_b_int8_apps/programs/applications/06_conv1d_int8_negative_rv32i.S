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
    bge x10, x0, mul_61a
    sub x10, x0, x10
mul_61a:
    bge x11, x0, mul_61b
    sub x11, x0, x11
mul_61b:
    addi x6, x0, 0
mul_61loop:
    beq x11, x0, mul_61done
    andi x7, x11, 1
    beq x7, x0, mul_61skip
    add x6, x6, x10
mul_61skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_61loop
mul_61done:
    bge x5, x0, mul_61positive
    sub x6, x0, x6
mul_61positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_62a
    sub x10, x0, x10
mul_62a:
    bge x11, x0, mul_62b
    sub x11, x0, x11
mul_62b:
    addi x6, x0, 0
mul_62loop:
    beq x11, x0, mul_62done
    andi x7, x11, 1
    beq x7, x0, mul_62skip
    add x6, x6, x10
mul_62skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_62loop
mul_62done:
    bge x5, x0, mul_62positive
    sub x6, x0, x6
mul_62positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_63a
    sub x10, x0, x10
mul_63a:
    bge x11, x0, mul_63b
    sub x11, x0, x11
mul_63b:
    addi x6, x0, 0
mul_63loop:
    beq x11, x0, mul_63done
    andi x7, x11, 1
    beq x7, x0, mul_63skip
    add x6, x6, x10
mul_63skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_63loop
mul_63done:
    bge x5, x0, mul_63positive
    sub x6, x0, x6
mul_63positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_64a
    sub x10, x0, x10
mul_64a:
    bge x11, x0, mul_64b
    sub x11, x0, x11
mul_64b:
    addi x6, x0, 0
mul_64loop:
    beq x11, x0, mul_64done
    andi x7, x11, 1
    beq x7, x0, mul_64skip
    add x6, x6, x10
mul_64skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_64loop
mul_64done:
    bge x5, x0, mul_64positive
    sub x6, x0, x6
mul_64positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_65a
    sub x10, x0, x10
mul_65a:
    bge x11, x0, mul_65b
    sub x11, x0, x11
mul_65b:
    addi x6, x0, 0
mul_65loop:
    beq x11, x0, mul_65done
    andi x7, x11, 1
    beq x7, x0, mul_65skip
    add x6, x6, x10
mul_65skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_65loop
mul_65done:
    bge x5, x0, mul_65positive
    sub x6, x0, x6
mul_65positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_66a
    sub x10, x0, x10
mul_66a:
    bge x11, x0, mul_66b
    sub x11, x0, x11
mul_66b:
    addi x6, x0, 0
mul_66loop:
    beq x11, x0, mul_66done
    andi x7, x11, 1
    beq x7, x0, mul_66skip
    add x6, x6, x10
mul_66skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_66loop
mul_66done:
    bge x5, x0, mul_66positive
    sub x6, x0, x6
mul_66positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_67a
    sub x10, x0, x10
mul_67a:
    bge x11, x0, mul_67b
    sub x11, x0, x11
mul_67b:
    addi x6, x0, 0
mul_67loop:
    beq x11, x0, mul_67done
    andi x7, x11, 1
    beq x7, x0, mul_67skip
    add x6, x6, x10
mul_67skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_67loop
mul_67done:
    bge x5, x0, mul_67positive
    sub x6, x0, x6
mul_67positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_68abs
    sub x10, x0, x10
round_68abs:
    beq x12, x0, round_68shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_68shift:
    srl x10, x10, x12
    bge x14, x0, round_68pos
    sub x10, x0, x10
round_68pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_69high
    addi x10, x0, -128
    jal x0, clip_69end
clip_69high:
    addi x5, x0, 127
    bge x5, x10, clip_69end
    addi x10, x0, 127
clip_69end:
    bge x10, x0, relu_70
    addi x10, x0, 0
relu_70:
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
