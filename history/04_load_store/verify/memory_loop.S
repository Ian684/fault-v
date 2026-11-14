.section .text
.globl _start
_start:
    lui x1,0x10000
    addi x1,x1,0
    addi x2,x1,0
    addi x3,x0,4
    addi x4,x0,1
    addi x5,x0,0
loop:
    sw x4,0(x2)
    lw x6,0(x2)
    add x5,x5,x6
    addi x2,x2,4
    addi x4,x4,1
    blt x4,x3,loop
    beq x4,x3,last
    ebreak
last:
    sw x4,0(x2)
    lw x6,0(x2)
    add x5,x5,x6
    fence iorw,iorw
    ebreak
