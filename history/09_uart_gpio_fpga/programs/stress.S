.section .text
.globl _start
_start:
    lui x1, 0x20000
    addi x1, x1, 256
    lui x2, 0x20000
    addi x2, x2, 512
    lui x7, 0x20000
    addi x7, x7, 0
    lui x8, 0x10000
    addi x8, x8, 0
    addi x5, x0, 1024
    addi x3, x0, 0
loop:
    sw x3, 0(x8)
    lw x4, 0(x8)
    bne x3, x4, fail
    andi x6, x3, 255
    sb x3, 4(x8)
    lbu x4, 4(x8)
    bne x6, x4, fail
    sh x3, 6(x8)
    lhu x4, 6(x8)
    bne x3, x4, fail
    sw x3, 0(x2)
    lw x4, 0(x2)
    andi x6, x3, 15
    bne x6, x4, fail
    lw x4, 4(x2)
    addi x6, x0, 3
    bne x6, x4, fail
    sw x3, 0(x1)
    addi x3, x3, 1
    bne x3, x5, loop
drain:
    lw x4, 4(x1)
    andi x4, x4, 1
    beq x4, x0, drain
    addi x3, x0, 1
    sw x3, 0(x7)
    ebreak
fail:
    addi x3, x0, 2
    sw x3, 0(x7)
    ebreak
