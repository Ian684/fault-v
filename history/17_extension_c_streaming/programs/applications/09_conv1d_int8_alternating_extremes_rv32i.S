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
    bge x10, x0, mul_91a
    sub x10, x0, x10
mul_91a:
    bge x11, x0, mul_91b
    sub x11, x0, x11
mul_91b:
    addi x6, x0, 0
mul_91loop:
    beq x11, x0, mul_91done
    andi x7, x11, 1
    beq x7, x0, mul_91skip
    add x6, x6, x10
mul_91skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_91loop
mul_91done:
    bge x5, x0, mul_91positive
    sub x6, x0, x6
mul_91positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_92a
    sub x10, x0, x10
mul_92a:
    bge x11, x0, mul_92b
    sub x11, x0, x11
mul_92b:
    addi x6, x0, 0
mul_92loop:
    beq x11, x0, mul_92done
    andi x7, x11, 1
    beq x7, x0, mul_92skip
    add x6, x6, x10
mul_92skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_92loop
mul_92done:
    bge x5, x0, mul_92positive
    sub x6, x0, x6
mul_92positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_93a
    sub x10, x0, x10
mul_93a:
    bge x11, x0, mul_93b
    sub x11, x0, x11
mul_93b:
    addi x6, x0, 0
mul_93loop:
    beq x11, x0, mul_93done
    andi x7, x11, 1
    beq x7, x0, mul_93skip
    add x6, x6, x10
mul_93skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_93loop
mul_93done:
    bge x5, x0, mul_93positive
    sub x6, x0, x6
mul_93positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_94a
    sub x10, x0, x10
mul_94a:
    bge x11, x0, mul_94b
    sub x11, x0, x11
mul_94b:
    addi x6, x0, 0
mul_94loop:
    beq x11, x0, mul_94done
    andi x7, x11, 1
    beq x7, x0, mul_94skip
    add x6, x6, x10
mul_94skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_94loop
mul_94done:
    bge x5, x0, mul_94positive
    sub x6, x0, x6
mul_94positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_95a
    sub x10, x0, x10
mul_95a:
    bge x11, x0, mul_95b
    sub x11, x0, x11
mul_95b:
    addi x6, x0, 0
mul_95loop:
    beq x11, x0, mul_95done
    andi x7, x11, 1
    beq x7, x0, mul_95skip
    add x6, x6, x10
mul_95skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_95loop
mul_95done:
    bge x5, x0, mul_95positive
    sub x6, x0, x6
mul_95positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_96a
    sub x10, x0, x10
mul_96a:
    bge x11, x0, mul_96b
    sub x11, x0, x11
mul_96b:
    addi x6, x0, 0
mul_96loop:
    beq x11, x0, mul_96done
    andi x7, x11, 1
    beq x7, x0, mul_96skip
    add x6, x6, x10
mul_96skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_96loop
mul_96done:
    bge x5, x0, mul_96positive
    sub x6, x0, x6
mul_96positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_97a
    sub x10, x0, x10
mul_97a:
    bge x11, x0, mul_97b
    sub x11, x0, x11
mul_97b:
    addi x6, x0, 0
mul_97loop:
    beq x11, x0, mul_97done
    andi x7, x11, 1
    beq x7, x0, mul_97skip
    add x6, x6, x10
mul_97skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_97loop
mul_97done:
    bge x5, x0, mul_97positive
    sub x6, x0, x6
mul_97positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_98abs
    sub x10, x0, x10
round_98abs:
    beq x12, x0, round_98shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_98shift:
    srl x10, x10, x12
    bge x14, x0, round_98pos
    sub x10, x0, x10
round_98pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_99high
    addi x10, x0, -128
    jal x0, clip_99end
clip_99high:
    addi x5, x0, 127
    bge x5, x10, clip_99end
    addi x10, x0, 127
clip_99end:
    bge x10, x0, relu_100
    addi x10, x0, 0
relu_100:
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
