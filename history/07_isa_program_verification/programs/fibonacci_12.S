.section .text
.globl _start
_start:
    lui x8,0x10000
    addi x8,x8,0
    addi x9,x8,0
    addi x10,x0,0
    addi x11,x0,1
    addi x12,x0,12
loop:
    sw x10,0(x9)
    add x13,x10,x11
    addi x10,x11,0
    addi x11,x13,0
    addi x9,x9,4
    addi x12,x12,-1
    bne x12,x0,loop
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
