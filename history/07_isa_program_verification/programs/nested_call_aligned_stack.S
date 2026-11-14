.section .text
.globl _start
_start:
    lui x2,0x10004
    addi x2,x2,0
    addi x10,x0,40
    jal x1,outer
    lui x8,0x10000
    addi x8,x8,0
    sw x10,0(x8)
    jal x0,done
outer:
    addi x2,x2,-16
    sw x1,12(x2)
    jal x1,inner
    addi x10,x10,1
    lw x1,12(x2)
    addi x2,x2,16
    jalr x0,0(x1)
inner:
    addi x10,x10,1
    jalr x0,0(x1)
done:
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
