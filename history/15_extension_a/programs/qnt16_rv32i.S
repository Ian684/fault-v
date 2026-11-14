.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 448
    lui x19, 0x10000
    addi x19, x19, 512
    addi x20, x0, 16
    addi x11, x0, 3
outer:
    lw x10, 0(x18)
    sra x10, x10, 11
    addi x5, x0, -128
    bge x10, x5, qnt_26_high_check
    addi x10, x0, -128
    jal x0, qnt_26_end
qnt_26_high_check:
    addi x5, x0, 127
    bge x5, x10, qnt_26_end
    addi x10, x0, 127
qnt_26_end:
    sw x10, 0(x19)
    addi x18, x18, 4
    addi x19, x19, 4
    addi x20, x20, -1
    bne x20, x0, outer
kernel_end:
    addi x0, x0, 0
    lui x21, 0x20000
    addi x21, x21, 0
    addi x10, x0, 1
    sw x10, 0(x21)
    ebreak
