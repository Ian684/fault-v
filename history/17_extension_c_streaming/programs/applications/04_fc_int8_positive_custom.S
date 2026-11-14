.section .text
.globl _start
_start:
    lui x21, 0x10000
    addi x21, x21, 0
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
    lui x18, 0x10000
    addi x18, x18, 256
    lw x22, 0(x28)
    addi x23, x0, 6
fc_inner:
    lw x24, 0(x18)
    lw x25, 0(x19)
    .insn r 0x0b, 0, 1, x22, x24, x25 # DOT4ACC
    addi x18, x18, 4
    addi x19, x19, 4
    addi x23, x23, -1
    bne x23, x0, fc_inner
    sw x22, 0(x27)
    lw x25, 0(x29)
    .insn r 0x0b, 4, 1, x24, x22, x25 # RQNT8
    sb x24, 0(x26)
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
