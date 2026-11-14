.section .text
.globl _start
_start:
    addi x1,x0,5
    addi x2,x0,0
    addi x3,x0,0
loop:
    addi x2,x2,1
    add x3,x3,x2
    blt x2,x1,loop
    jal x1,function
    jal x0,done
function:
    addi x3,x3,10
    jalr x0,0(x1)
done:
    ebreak
