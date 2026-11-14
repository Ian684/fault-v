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
    addi x24, x0, 0
    lbu x10, 0(x18)
    or x24, x24, x10
    lbu x10, 1(x18)
    slli x10, x10, 8
    or x24, x24, x10
    lbu x10, 2(x18)
    slli x10, x10, 16
    or x24, x24, x10
    lbu x10, 3(x18)
    slli x10, x10, 24
    or x24, x24, x10
    addi x25, x0, 0
    lbu x10, 0(x19)
    or x25, x25, x10
    lbu x10, 1(x19)
    slli x10, x10, 8
    or x25, x25, x10
    lbu x10, 2(x19)
    slli x10, x10, 16
    or x25, x25, x10
    lbu x10, 3(x19)
    slli x10, x10, 24
    or x25, x25, x10
    .insn r 0x0b, 0, 1, x22, x24, x25 # DOT4ACC
    addi x24, x0, 0
    lbu x10, 4(x18)
    or x24, x24, x10
    lbu x10, 5(x18)
    slli x10, x10, 8
    or x24, x24, x10
    addi x25, x0, 0
    lbu x10, 4(x19)
    or x25, x25, x10
    lbu x10, 5(x19)
    slli x10, x10, 8
    or x25, x25, x10
    .insn r 0x0b, 0, 1, x22, x24, x25 # DOT4ACC
    sw x22, 0(x27)
    lw x25, 0(x29)
    .insn r 0x0b, 4, 1, x24, x22, x25 # RQNT8
    bge x24, x0, relu_131
    addi x24, x0, 0
relu_131:
    sb x24, 0(x26)
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
