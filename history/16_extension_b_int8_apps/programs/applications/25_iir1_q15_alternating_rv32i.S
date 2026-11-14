.section .text
.globl _start
_start:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 1024
    lui x26, 0x10001
    addi x26, x26, 768
    addi x20, x0, 32
    addi x24, x0, 0
    lui x8, 0x2
    addi x8, x8, 0
    lui x9, 0x6
    addi x9, x9, 0
iir_sample:
    addi x22, x0, 0
    lh x10, 0(x18)
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_204a
    sub x10, x0, x10
mul_204a:
    bge x11, x0, mul_204b
    sub x11, x0, x11
mul_204b:
    addi x6, x0, 0
mul_204loop:
    beq x11, x0, mul_204done
    andi x7, x11, 1
    beq x7, x0, mul_204skip
    add x6, x6, x10
mul_204skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_204loop
mul_204done:
    bge x5, x0, mul_204positive
    sub x6, x0, x6
mul_204positive:
    addi x10, x6, 0
    add x22, x22, x10
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_205a
    sub x10, x0, x10
mul_205a:
    bge x11, x0, mul_205b
    sub x11, x0, x11
mul_205b:
    addi x6, x0, 0
mul_205loop:
    beq x11, x0, mul_205done
    andi x7, x11, 1
    beq x7, x0, mul_205skip
    add x6, x6, x10
mul_205skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_205loop
mul_205done:
    bge x5, x0, mul_205positive
    sub x6, x0, x6
mul_205positive:
    addi x10, x6, 0
    add x22, x22, x10
    srai x22, x22, 15
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x22, x5, clip_206high
    lui x22, 0xffff8
    addi x22, x22, 0
    jal x0, clip_206end
clip_206high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x22, clip_206end
    lui x22, 0x8
    addi x22, x22, -1
clip_206end:
    addi x24, x22, 0
    sw x22, 0(x26)
    addi x18, x18, 2
    addi x26, x26, 4
    addi x20, x20, -1
    bne x20, x0, iir_sample
kernel_end:
    lui x30, 0x20000
    addi x30, x30, 0
    addi x10, x0, 1
    sw x10, 0(x30)
    ebreak
