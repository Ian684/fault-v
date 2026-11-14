.section .text
.globl _start
_start:
    addi x1,x0,100
    addi x2,x0,0
    addi x3,x0,0
loop:
    addi x2,x2,1
    add x3,x3,x2
    blt x2,x1,loop
    lui x8,0x10000
    addi x8,x8,0
    sw x3,0(x8)
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
