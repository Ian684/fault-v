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
    bge x10, x0, mul_151a
    sub x10, x0, x10
mul_151a:
    bge x11, x0, mul_151b
    sub x11, x0, x11
mul_151b:
    addi x6, x0, 0
mul_151loop:
    beq x11, x0, mul_151done
    andi x7, x11, 1
    beq x7, x0, mul_151skip
    add x6, x6, x10
mul_151skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_151loop
mul_151done:
    bge x5, x0, mul_151positive
    sub x6, x0, x6
mul_151positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_152a
    sub x10, x0, x10
mul_152a:
    bge x11, x0, mul_152b
    sub x11, x0, x11
mul_152b:
    addi x6, x0, 0
mul_152loop:
    beq x11, x0, mul_152done
    andi x7, x11, 1
    beq x7, x0, mul_152skip
    add x6, x6, x10
mul_152skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_152loop
mul_152done:
    bge x5, x0, mul_152positive
    sub x6, x0, x6
mul_152positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_153a
    sub x10, x0, x10
mul_153a:
    bge x11, x0, mul_153b
    sub x11, x0, x11
mul_153b:
    addi x6, x0, 0
mul_153loop:
    beq x11, x0, mul_153done
    andi x7, x11, 1
    beq x7, x0, mul_153skip
    add x6, x6, x10
mul_153skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_153loop
mul_153done:
    bge x5, x0, mul_153positive
    sub x6, x0, x6
mul_153positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_154a
    sub x10, x0, x10
mul_154a:
    bge x11, x0, mul_154b
    sub x11, x0, x11
mul_154b:
    addi x6, x0, 0
mul_154loop:
    beq x11, x0, mul_154done
    andi x7, x11, 1
    beq x7, x0, mul_154skip
    add x6, x6, x10
mul_154skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_154loop
mul_154done:
    bge x5, x0, mul_154positive
    sub x6, x0, x6
mul_154positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_155a
    sub x10, x0, x10
mul_155a:
    bge x11, x0, mul_155b
    sub x11, x0, x11
mul_155b:
    addi x6, x0, 0
mul_155loop:
    beq x11, x0, mul_155done
    andi x7, x11, 1
    beq x7, x0, mul_155skip
    add x6, x6, x10
mul_155skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_155loop
mul_155done:
    bge x5, x0, mul_155positive
    sub x6, x0, x6
mul_155positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_156a
    sub x10, x0, x10
mul_156a:
    bge x11, x0, mul_156b
    sub x11, x0, x11
mul_156b:
    addi x6, x0, 0
mul_156loop:
    beq x11, x0, mul_156done
    andi x7, x11, 1
    beq x7, x0, mul_156skip
    add x6, x6, x10
mul_156skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_156loop
mul_156done:
    bge x5, x0, mul_156positive
    sub x6, x0, x6
mul_156positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_157a
    sub x10, x0, x10
mul_157a:
    bge x11, x0, mul_157b
    sub x11, x0, x11
mul_157b:
    addi x6, x0, 0
mul_157loop:
    beq x11, x0, mul_157done
    andi x7, x11, 1
    beq x7, x0, mul_157skip
    add x6, x6, x10
mul_157skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_157loop
mul_157done:
    bge x5, x0, mul_157positive
    sub x6, x0, x6
mul_157positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_158abs
    sub x10, x0, x10
round_158abs:
    beq x12, x0, round_158shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_158shift:
    srl x10, x10, x12
    bge x14, x0, round_158pos
    sub x10, x0, x10
round_158pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_159high
    addi x10, x0, -128
    jal x0, clip_159end
clip_159high:
    addi x5, x0, 127
    bge x5, x10, clip_159end
    addi x10, x0, 127
clip_159end:
    bge x10, x0, relu_160
    addi x10, x0, 0
relu_160:
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
