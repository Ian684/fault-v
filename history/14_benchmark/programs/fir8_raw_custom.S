.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 256
    lui x19, 0x10000
    addi x19, x19, 384
    addi x20, x0, 16
    lw x26, 320(x21)
    lw x27, 324(x21)
outer:
    addi x22, x0, 0
    addi x10, x0, 0
    lbu x11, 0(x18)
    or x10, x10, 11
    lbu x11, 1(x18)
    slli x11, x11, 8
    or x10, x10, 11
    lbu x11, 2(x18)
    slli x11, x11, 16
    or x10, x10, 11
    lbu x11, 3(x18)
    slli x11, x11, 24
    or x10, x10, 11
    .insn r 0x0b, 0, 0, x10, x10, x26 # DOT4
    add x22, x22, 10
    addi x10, x0, 0
    lbu x11, 4(x18)
    or x10, x10, 11
    lbu x11, 5(x18)
    slli x11, x11, 8
    or x10, x10, 11
    lbu x11, 6(x18)
    slli x11, x11, 16
    or x10, x10, 11
    lbu x11, 7(x18)
    slli x11, x11, 24
    or x10, x10, 11
    .insn r 0x0b, 0, 0, x10, x10, x27 # DOT4
    add x22, x22, 10
    sw x22, 0(x19)
    addi x18, x18, 1
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
