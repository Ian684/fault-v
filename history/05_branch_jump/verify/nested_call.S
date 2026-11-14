.section .text
.globl _start
_start:
    jal x1,outer
    jal x0,done
outer:
    addi x5,x1,0
    jal x1,inner
    addi x10,x10,2
    jalr x0,0(x5)
inner:
    addi x10,x10,3
    jalr x0,0(x1)
done:
    ebreak
