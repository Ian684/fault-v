.section .text
.globl _start
_start:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x24, 0x10000
    addi x24, x24, 768
    lui x26, 0x10001
    addi x26, x26, 512
    addi x20, x0, 32
fir_output:
    addi x18, x24, 0
    lui x19, 0x10000
    addi x19, x19, 896
    addi x22, x0, 0
    addi x23, x0, 8
fir_tap:
    lh x10, 0(x18)
    lh x11, 0(x19)
    xor x5, x10, x11
    bge x10, x0, mul_190a
    sub x10, x0, x10
mul_190a:
    bge x11, x0, mul_190b
    sub x11, x0, x11
mul_190b:
    addi x6, x0, 0
mul_190loop:
    beq x11, x0, mul_190done
    andi x7, x11, 1
    beq x7, x0, mul_190skip
    add x6, x6, x10
mul_190skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_190loop
mul_190done:
    bge x5, x0, mul_190positive
    sub x6, x0, x6
mul_190positive:
    addi x10, x6, 0
    add x22, x22, x10
    addi x18, x18, 2
    addi x19, x19, 2
    addi x23, x23, -1
    bne x23, x0, fir_tap
    srai x22, x22, 15
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x22, x5, clip_191high
    lui x22, 0xffff8
    addi x22, x22, 0
    jal x0, clip_191end
clip_191high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x22, clip_191end
    lui x22, 0x8
    addi x22, x22, -1
clip_191end:
    sw x22, 0(x26)
    addi x24, x24, 2
    addi x26, x26, 4
    addi x20, x20, -1
    bne x20, x0, fir_output
kernel_end:
    lui x30, 0x20000
    addi x30, x30, 0
    addi x10, x0, 1
    sw x10, 0(x30)
    ebreak
