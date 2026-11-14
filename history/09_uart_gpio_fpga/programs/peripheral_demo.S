.section .text
.globl _start
_start:
    lui x1,0x20000
    addi x1,x1,256
    lui x2,0x20000
    addi x2,x2,512
    lui x7,0x20000
    addi x7,x7,0
    lui x8,0x10000
    addi x8,x8,0
    addi x3,x0,5
    sw x3,0(x2)
    lw x4,0(x2)
    bne x3,x4,fail
    lw x9,4(x2)
    sw x9,0(x8)
    addi x10,x0,70
wait_0:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_0
    sw x10,0(x1)
    addi x10,x0,97
wait_1:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_1
    sw x10,0(x1)
    addi x10,x0,117
wait_2:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_2
    sw x10,0(x1)
    addi x10,x0,108
wait_3:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_3
    sw x10,0(x1)
    addi x10,x0,116
wait_4:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_4
    sw x10,0(x1)
    addi x10,x0,45
wait_5:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_5
    sw x10,0(x1)
    addi x10,x0,86
wait_6:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_6
    sw x10,0(x1)
    addi x10,x0,32
wait_7:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_7
    sw x10,0(x1)
    addi x10,x0,79
wait_8:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_8
    sw x10,0(x1)
    addi x10,x0,75
wait_9:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_9
    sw x10,0(x1)
    addi x10,x0,13
wait_10:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_10
    sw x10,0(x1)
    addi x10,x0,10
wait_11:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_11
    sw x10,0(x1)
drain:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,drain
    addi x3,x0,5
    sw x3,0(x2)
    addi x3,x0,1
    sw x3,0(x7)
    ebreak
fail:
    addi x3,x0,15
    sw x3,0(x2)
    addi x3,x0,2
    sw x3,0(x7)
    ebreak
