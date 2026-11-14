.section .text
.globl _start
_start:
    lui x10, 0x807f0
    addi x10, x10, 255
    lui x11, 0x7f810
    addi x11, x11, -255
    addi x12, x0, 0
    .insn r 0x0b, 0, 0, x12, x10, x11 # DOT4
    lui x13, 0xffff8
    addi x13, x13, 255
    beq x12, x13, ok1
    jal x0, failure
ok1:
    lui x10, 0x8
    addi x10, x10, 0
    lui x11, 0x10
    addi x11, x11, -1
    addi x12, x0, 0
    .insn r 0x0b, 1, 0, x12, x10, x11 # MUL16
    lui x13, 0x8
    addi x13, x13, 0
    beq x12, x13, ok2
    jal x0, failure
ok2:
    lui x10, 0x80000
    addi x10, x10, -1
    addi x11, x0, 1
    addi x12, x0, 0
    .insn r 0x0b, 2, 0, x12, x10, x11 # ADDSAT
    lui x13, 0x80000
    addi x13, x13, -1
    beq x12, x13, ok3
    jal x0, failure
ok3:
    addi x10, x0, -128
    addi x11, x0, 3
    addi x12, x0, 0
    .insn r 0x0b, 3, 0, x12, x10, x11 # QNT8
    addi x13, x0, -16
    beq x12, x13, ok4
    jal x0, failure
ok4:
    lui x10, 0x1020
    addi x10, x10, 772
    addi x11, x0, -1
    addi x12, x0, 123
    .insn r 0x0b, 0, 1, x12, x10, x11 # DOT4ACC
    addi x13, x0, 113
    beq x12, x13, ok5
    jal x0, failure
ok5:
    addi x10, x0, 1
    addi x11, x0, 1
    lui x12, 0x80000
    addi x12, x12, -1
    .insn r 0x0b, 1, 1, x12, x10, x11 # MAC16
    lui x13, 0x80000
    addi x13, x13, 0
    beq x12, x13, ok6
    jal x0, failure
ok6:
    lui x10, 0x7f808
    addi x10, x10, -128
    lui x11, 0x7f808
    addi x11, x11, -128
    addi x12, x0, 0
    .insn r 0x0b, 2, 1, x12, x10, x11 # ADD8SAT
    lui x13, 0x7f808
    addi x13, x13, -128
    beq x12, x13, ok7
    jal x0, failure
ok7:
    lui x10, 0x7f808
    addi x10, x10, -128
    lui x11, 0x807f8
    addi x11, x11, 127
    addi x12, x0, 0
    .insn r 0x0b, 3, 1, x12, x10, x11 # SUB8SAT
    lui x13, 0x7f808
    addi x13, x13, -128
    beq x12, x13, ok8
    jal x0, failure
ok8:
    addi x10, x0, -3
    lui x11, 0x410
    addi x11, x11, 1
    addi x12, x0, 0
    .insn r 0x0b, 4, 1, x12, x10, x11 # RQNT8
    addi x13, x0, 0
    beq x12, x13, ok9
    jal x0, failure
ok9:
    lui x10, 0x80008
    addi x10, x10, 0
    lui x11, 0x80008
    addi x11, x11, 0
    addi x12, x0, 0
    .insn r 0x0b, 5, 1, x12, x10, x11 # DOT2SAT
    lui x13, 0x80000
    addi x13, x13, -1
    beq x12, x13, ok10
    jal x0, failure
ok10:
    lui x10, 0x87f01
    addi x10, x10, 564
    lui x11, 0xf7812
    addi x11, x11, 832
    addi x12, x0, 0
    .insn r 0x0b, 6, 1, x12, x10, x11 # DOT8
    addi x13, x0, 85
    beq x12, x13, ok11
    jal x0, failure
ok11:
    lui x10, 0xff808
    addi x10, x10, -255
    lui x11, 0xff008
    addi x11, x11, 255
    addi x12, x0, 0
    .insn r 0x0b, 7, 1, x12, x10, x11 # DOT4SU
    lui x13, 0x4
    addi x13, x13, -128
    beq x12, x13, ok12
    jal x0, failure
ok12:
    lui x28, 0x10000
    addi x28, x28, 0
    lui x29, 0x807f0
    addi x29, x29, 255
    sw x29, 0(x28)
    lui x28, 0x10000
    addi x28, x28, 4
    lui x29, 0x7f810
    addi x29, x29, -255
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 776
    lui x29, 0x10000
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 780
    addi x29, x0, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 784
    lui x29, 0x10010
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 788
    addi x29, x0, 1
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 768
    addi x29, x0, 1
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 768
dma:
    lw x29, 4(x28)
    andi x30, x29, 1
    bne x30, x0, dma
    addi x13, x0, 2
    beq x29, x13, ok13
    jal x0, failure
ok13:
    lui x28, 0x20000
    addi x28, x28, 1032
    lui x29, 0x10010
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1036
    lui x29, 0x10000
    addi x29, x29, 4
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1040
    lui x29, 0x10003
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1044
    addi x29, x0, 1
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1024
    addi x29, x0, 1
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1024
acc:
    lw x29, 4(x28)
    andi x30, x29, 1
    bne x30, x0, acc
    addi x13, x0, 2
    beq x29, x13, ok14
    jal x0, failure
ok14:
    lui x28, 0x10003
    addi x28, x28, 0
    lw x12, 0(x28)
    lui x13, 0xffff8
    addi x13, x13, 255
    beq x12, x13, ok15
    jal x0, failure
ok15:
    lui x28, 0x20000
    addi x28, x28, 512
    addi x29, x0, 5
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 0
    addi x29, x0, 1
    sw x29, 0(x28)
    ebreak
failure:
    lui x28, 0x20000
    addi x28, x28, 512
    addi x29, x0, 15
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 0
    addi x29, x0, 2
    sw x29, 0(x28)
    ebreak
