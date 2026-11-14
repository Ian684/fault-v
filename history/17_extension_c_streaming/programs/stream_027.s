.section .text
.globl _start
_start:
    lui x28, 0x20000
    addi x28, x28, 776
    lui x29, 0x10010
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 780
    addi x29, x0, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 784
    lui x29, 0x10002
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 788
    addi x29, x0, 16
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 768
    addi x29, x0, 1
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 768
wait:
    lw x29, 4(x28)
    andi x30, x29, 1
    bne x30, x0, wait
    lui x28, 0x20000
    addi x28, x28, 0
    addi x29, x0, 1
    sw x29, 0(x28)
    ebreak
