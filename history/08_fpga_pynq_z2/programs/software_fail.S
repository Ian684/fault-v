.section .text
.globl _start
_start:
    lui x2,0x10004
    addi x2,x2,0
    lui x8,0x10000
    addi x8,x8,0
    addi x9,x8,0
    addi x10,x0,0
    addi x11,x0,1
    addi x12,x0,10
fib_loop:
    sw x10,0(x9)
    add x13,x10,x11
    addi x10,x11,0
    addi x11,x13,0
    addi x9,x9,4
    addi x12,x12,-1
    bne x12,x0,fib_loop
    jal x1,sum_fib
    addi x17,x0,177
    bne x10,x17,fail1
    sw x10,64(x8)
    lui x18,0x89abd
    addi x18,x18,-529
    sw x18,48(x8)
    lb x19,51(x8)
    addi x20,x0,-119
    bne x19,x20,fail2
    lbu x19,51(x8)
    addi x20,x0,137
    bne x19,x20,fail2
    lh x19,50(x8)
    lui x20,0xffff9
    addi x20,x20,-1621
    bne x19,x20,fail2
    lhu x19,50(x8)
    lui x20,0x9
    addi x20,x20,-1621
    bne x19,x20,fail2
    sb x0,49(x8)
    lui x21,0x1
    addi x21,x21,564
    sh x21,50(x8)
    lw x22,48(x8)
    lui x23,0x12340
    addi x23,x23,239
    bne x22,x23,fail3
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    lw x26,0(x24)
    bne x26,x25,fail4
    ebreak
sum_fib:
    addi x2,x2,-4
    sw x1,0(x2)
    addi x10,x0,0
    addi x14,x8,0
    addi x15,x0,10
sum_loop:
    lw x16,0(x14)
    add x10,x10,x16
    addi x14,x14,4
    addi x15,x15,-1
    bne x15,x0,sum_loop
    jal x1,double
    lw x1,0(x2)
    addi x2,x2,4
    jalr x0,0(x1)
double:
    add x10,x10,x10
    jalr x0,0(x1)
fail1:
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,2
    sw x25,0(x24)
    ebreak
fail2:
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,3
    sw x25,0(x24)
    ebreak
fail3:
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,4
    sw x25,0(x24)
    ebreak
fail4:
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,5
    sw x25,0(x24)
    ebreak
