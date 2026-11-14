.section .text
.globl _start
_start:
    addi x10,x0,48
    addi x11,x0,18
loop:
    beq x10,x11,done
    bltu x10,x11,less
    sub x10,x10,x11
    jal x0,loop
less:
    sub x11,x11,x10
    jal x0,loop
done:
    lui x8,0x10000
    addi x8,x8,0
    sw x10,0(x8)
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
