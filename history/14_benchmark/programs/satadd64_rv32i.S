.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 1280
    lui x19, 0x10000
    addi x19, x19, 1536
    lui x23, 0x10000
    addi x23, x23, 1792
    addi x20, x0, 64
outer:
    lw x10, 0(x18)
    lw x11, 0(x19)
    add x5, x10, 11
    xor x6, x10, 11
    blt x6, x0, sat_27_normal
    xor x6, x10, 5
    bge x6, x0, sat_27_normal
    srli x6, x10, 31
    lui x10, 0x80000
    addi x10, x10, -1
    add x10, x10, 6
    jal x0, sat_27_end
sat_27_normal:
    addi x10, x5, 0
sat_27_end:
    sw x10, 0(x23)
    addi x18, x18, 4
    addi x19, x19, 4
    addi x23, x23, 4
    addi x20, x20, -1
    bne x20, x0, outer
kernel_end:
    addi x0, x0, 0
    lui x21, 0x20000
    addi x21, x21, 0
    addi x10, x0, 1
    sw x10, 0(x21)
    ebreak
