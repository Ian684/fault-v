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
    bge x10, x0, mul_196a
    sub x10, x0, x10
mul_196a:
    bge x11, x0, mul_196b
    sub x11, x0, x11
mul_196b:
    addi x6, x0, 0
mul_196loop:
    beq x11, x0, mul_196done
    andi x7, x11, 1
    beq x7, x0, mul_196skip
    add x6, x6, x10
mul_196skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_196loop
mul_196done:
    bge x5, x0, mul_196positive
    sub x6, x0, x6
mul_196positive:
    addi x10, x6, 0
    add x22, x22, x10
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_197a
    sub x10, x0, x10
mul_197a:
    bge x11, x0, mul_197b
    sub x11, x0, x11
mul_197b:
    addi x6, x0, 0
mul_197loop:
    beq x11, x0, mul_197done
    andi x7, x11, 1
    beq x7, x0, mul_197skip
    add x6, x6, x10
mul_197skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_197loop
mul_197done:
    bge x5, x0, mul_197positive
    sub x6, x0, x6
mul_197positive:
    addi x10, x6, 0
    add x22, x22, x10
    srai x22, x22, 15
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x22, x5, clip_198high
    lui x22, 0xffff8
    addi x22, x22, 0
    jal x0, clip_198end
clip_198high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x22, clip_198end
    lui x22, 0x8
    addi x22, x22, -1
clip_198end:
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
