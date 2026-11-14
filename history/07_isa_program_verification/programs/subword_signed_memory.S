.section .text
.globl _start
_start:
    lui x8,0x10000
    addi x8,x8,0
    lui x1,0x89abd
    addi x1,x1,-529
    sw x1,0(x8)
    lb x2,3(x8)
    lbu x3,3(x8)
    lh x4,2(x8)
    lhu x5,2(x8)
    sb x0,1(x8)
    lui x6,0x1
    addi x6,x6,564
    sh x6,2(x8)
    lw x7,0(x8)
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
