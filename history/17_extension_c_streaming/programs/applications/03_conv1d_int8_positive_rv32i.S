.section .text
.globl _start
_start:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 0
    lui x26, 0x10001
    addi x26, x26, 0
    lui x27, 0x10001
    addi x27, x27, -2048
    addi x20, x0, 8
conv_position:
    lui x19, 0x10000
    addi x19, x19, 64
    lui x28, 0x10000
    addi x28, x28, 128
    lui x29, 0x10000
    addi x29, x29, 144
    addi x23, x0, 3
conv_channel:
    lw x22, 0(x28)
    lb x10, 0(x18)
    lb x11, 0(x19)
    xor x5, x10, x11
    bge x10, x0, mul_31a
    sub x10, x0, x10
mul_31a:
    bge x11, x0, mul_31b
    sub x11, x0, x11
mul_31b:
    addi x6, x0, 0
mul_31loop:
    beq x11, x0, mul_31done
    andi x7, x11, 1
    beq x7, x0, mul_31skip
    add x6, x6, x10
mul_31skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_31loop
mul_31done:
    bge x5, x0, mul_31positive
    sub x6, x0, x6
mul_31positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 1(x18)
    lb x11, 1(x19)
    xor x5, x10, x11
    bge x10, x0, mul_32a
    sub x10, x0, x10
mul_32a:
    bge x11, x0, mul_32b
    sub x11, x0, x11
mul_32b:
    addi x6, x0, 0
mul_32loop:
    beq x11, x0, mul_32done
    andi x7, x11, 1
    beq x7, x0, mul_32skip
    add x6, x6, x10
mul_32skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_32loop
mul_32done:
    bge x5, x0, mul_32positive
    sub x6, x0, x6
mul_32positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 2(x18)
    lb x11, 2(x19)
    xor x5, x10, x11
    bge x10, x0, mul_33a
    sub x10, x0, x10
mul_33a:
    bge x11, x0, mul_33b
    sub x11, x0, x11
mul_33b:
    addi x6, x0, 0
mul_33loop:
    beq x11, x0, mul_33done
    andi x7, x11, 1
    beq x7, x0, mul_33skip
    add x6, x6, x10
mul_33skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_33loop
mul_33done:
    bge x5, x0, mul_33positive
    sub x6, x0, x6
mul_33positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 3(x18)
    lb x11, 3(x19)
    xor x5, x10, x11
    bge x10, x0, mul_34a
    sub x10, x0, x10
mul_34a:
    bge x11, x0, mul_34b
    sub x11, x0, x11
mul_34b:
    addi x6, x0, 0
mul_34loop:
    beq x11, x0, mul_34done
    andi x7, x11, 1
    beq x7, x0, mul_34skip
    add x6, x6, x10
mul_34skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_34loop
mul_34done:
    bge x5, x0, mul_34positive
    sub x6, x0, x6
mul_34positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 4(x18)
    lb x11, 4(x19)
    xor x5, x10, x11
    bge x10, x0, mul_35a
    sub x10, x0, x10
mul_35a:
    bge x11, x0, mul_35b
    sub x11, x0, x11
mul_35b:
    addi x6, x0, 0
mul_35loop:
    beq x11, x0, mul_35done
    andi x7, x11, 1
    beq x7, x0, mul_35skip
    add x6, x6, x10
mul_35skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_35loop
mul_35done:
    bge x5, x0, mul_35positive
    sub x6, x0, x6
mul_35positive:
    addi x10, x6, 0
    add x22, x22, x10
    lb x10, 5(x18)
    lb x11, 5(x19)
    xor x5, x10, x11
    bge x10, x0, mul_36a
    sub x10, x0, x10
mul_36a:
    bge x11, x0, mul_36b
    sub x11, x0, x11
mul_36b:
    addi x6, x0, 0
mul_36loop:
    beq x11, x0, mul_36done
    andi x7, x11, 1
    beq x7, x0, mul_36skip
    add x6, x6, x10
mul_36skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_36loop
mul_36done:
    bge x5, x0, mul_36positive
    sub x6, x0, x6
mul_36positive:
    addi x10, x6, 0
    add x22, x22, x10
    sw x22, 0(x27)
    lw x25, 0(x29)
    addi x10, x22, 0
    slli x11, x25, 16
    srai x11, x11, 16
    xor x5, x10, x11
    bge x10, x0, mul_37a
    sub x10, x0, x10
mul_37a:
    bge x11, x0, mul_37b
    sub x11, x0, x11
mul_37b:
    addi x6, x0, 0
mul_37loop:
    beq x11, x0, mul_37done
    andi x7, x11, 1
    beq x7, x0, mul_37skip
    add x6, x6, x10
mul_37skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_37loop
mul_37done:
    bge x5, x0, mul_37positive
    sub x6, x0, x6
mul_37positive:
    addi x10, x6, 0
    srli x12, x25, 16
    andi x12, x12, 31
    slli x13, x25, 3
    srai x13, x13, 24
    srai x14, x10, 31
    bge x10, x0, round_38abs
    sub x10, x0, x10
round_38abs:
    beq x12, x0, round_38shift
    addi x16, x12, -1
    addi x15, x0, 1
    sll x15, x15, x16
    add x10, x10, x15
round_38shift:
    srl x10, x10, x12
    bge x14, x0, round_38pos
    sub x10, x0, x10
round_38pos:
    add x10, x10, x13
    addi x5, x0, -128
    bge x10, x5, clip_39high
    addi x10, x0, -128
    jal x0, clip_39end
clip_39high:
    addi x5, x0, 127
    bge x5, x10, clip_39end
    addi x10, x0, 127
clip_39end:
    bge x10, x0, relu_40
    addi x10, x0, 0
relu_40:
    sb x10, 0(x26)
    addi x19, x19, 6
    addi x28, x28, 4
    addi x29, x29, 4
    addi x27, x27, 4
    addi x26, x26, 1
    addi x23, x23, -1
    bne x23, x0, conv_channel
    addi x18, x18, 2
    addi x20, x20, -1
    bne x20, x0, conv_position
kernel_end:
    lui x30, 0x20000
    addi x30, x30, 0
    addi x10, x0, 1
    sw x10, 0(x30)
    ebreak
