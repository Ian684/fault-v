.section .text
.globl _start
_start:
    lui x8,0x10000
    addi x8,x8,0
    lui x9,0x10000
    addi x9,x9,512
    addi x10,x0,64
    addi x11,x0,0
fill:
    sw x11,0(x8)
    addi x8,x8,4
    addi x11,x11,1
    blt x11,x10,fill
    lui x8,0x10000
    addi x8,x8,0
    addi x11,x0,0
    addi x12,x0,0
copy:
    lw x13,0(x8)
    sw x13,0(x9)
    add x12,x12,x13
    addi x8,x8,4
    addi x9,x9,4
    addi x11,x11,1
    blt x11,x10,copy
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
