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
    bge x10, x0, mul_121a
    sub x10, x0, x10
mul_121a:
    bge x11, x0, mul_121b
    sub x11, x0, x11
mul_121b:
    addi x6, x0, 0
mul_121loop:
    beq x11, x0, mul_121done
    andi x7, x11, 1
    beq x7, x0, mul_121skip
    add x6, x6, x10
mul_121skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_121loop
mul_121done:
    bge x5, x0, mul_121positive
    sub x6, x0, x6
mul_121positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_122a
    sub x10, x0, x10
mul_122a:
    bge x11, x0, mul_122b
    sub x11, x0, x11
mul_122b:
    addi x6, x0, 0
mul_122loop:
    beq x11, x0, mul_122done
    andi x7, x11, 1
    beq x7, x0, mul_122skip
    add x6, x6, x10
mul_122skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_122loop
mul_122done:
    bge x5, x0, mul_122positive
    sub x6, x0, x6
mul_122positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_123a
    sub x10, x0, x10
mul_123a:
    bge x11, x0, mul_123b
    sub x11, x0, x11
mul_123b:
    addi x6, x0, 0
mul_123loop:
    beq x11, x0, mul_123done
    andi x7, x11, 1
    beq x7, x0, mul_123skip
    add x6, x6, x10
mul_123skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_123loop
mul_123done:
    bge x5, x0, mul_123positive
    sub x6, x0, x6
mul_123positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_124a
    sub x10, x0, x10
mul_124a:
    bge x11, x0, mul_124b
    sub x11, x0, x11
mul_124b:
    addi x6, x0, 0
mul_124loop:
    beq x11, x0, mul_124done
    andi x7, x11, 1
    beq x7, x0, mul_124skip
    add x6, x6, x10
mul_124skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_124loop
mul_124done:
    bge x5, x0, mul_124positive
    sub x6, x0, x6
mul_124positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_125a
    sub x10, x0, x10
mul_125a:
    bge x11, x0, mul_125b
    sub x11, x0, x11
mul_125b:
    addi x6, x0, 0
mul_125loop:
    beq x11, x0, mul_125done
    andi x7, x11, 1
    beq x7, x0, mul_125skip
    add x6, x6, x10
mul_125skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_125loop
mul_125done:
    bge x5, x0, mul_125positive
    sub x6, x0, x6
mul_125positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_126a
    sub x10, x0, x10
mul_126a:
    bge x11, x0, mul_126b
    sub x11, x0, x11
mul_126b:
    addi x6, x0, 0
mul_126loop:
    beq x11, x0, mul_126done
    andi x7, x11, 1
    beq x7, x0, mul_126skip
    add x6, x6, x10
mul_126skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_126loop
mul_126done:
    bge x5, x0, mul_126positive
    sub x6, x0, x6
mul_126positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_127a
    sub x10, x0, x10
mul_127a:
    bge x11, x0, mul_127b
    sub x11, x0, x11
mul_127b:
    addi x6, x0, 0
mul_127loop:
    beq x11, x0, mul_127done
    andi x7, x11, 1
    beq x7, x0, mul_127skip
    add x6, x6, x10
mul_127skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_127loop
mul_127done:
    bge x5, x0, mul_127positive
    sub x6, x0, x6
mul_127positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_128abs
    sub x10, x0, x10
round_128abs:
    beq x12, x0, round_128shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_128shift:
    srl x10, x10, x12
    bge x14, x0, round_128pos
    sub x10, x0, x10
round_128pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_129high
    addi x10, x0, -128
    jal x0, clip_129end
clip_129high:
    addi x5, x0, 127
    bge x5, x10, clip_129end
    addi x10, x0, 127
clip_129end:
    bge x10, x0, relu_130
    addi x10, x0, 0
relu_130:
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
