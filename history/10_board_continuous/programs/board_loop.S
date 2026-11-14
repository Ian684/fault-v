.section .text
.globl _start
_start:
    lui x1, 0x20000
    addi x1, x1, 512
    lui x7, 0x20000
    addi x7, x7, 0
    addi x3, x0, 0
    addi x6, x0, 10
sweep:
    lui x8, 0x10000
    addi x8, x8, 0
    lui x5, 0x1
    addi x5, x5, 0
word:
    sw x3, 0(x8)
    lw x4, 0(x8)
    bne x3, x4, fail
    addi x3, x3, 1
    addi x8, x8, 4
    addi x5, x5, -1
    bne x5, x0, word
    xori x6, x6, 15
    sw x6, 0(x1)
    addi x10, x0, 1
    sw x10, 0(x7)
    lui x31, 0x7a
    addi x31, x31, 288
delay:
    addi x31, x31, -1
    bne x31, x0, delay
    jal x0, sweep
fail:
    addi x6, x0, 15
    sw x6, 0(x1)
    addi x10, x0, 2
    sw x10, 0(x7)
    ebreak
