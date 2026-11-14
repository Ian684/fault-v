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
    .insn r 0x0b, 1, 1, x22, x10, x11 # MAC16
    addi x18, x18, 2
    addi x19, x19, 2
    addi x23, x23, -1
    bne x23, x0, fir_tap
    srai x22, x22, 15
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x22, x5, clip_183high
    lui x22, 0xffff8
    addi x22, x22, 0
    jal x0, clip_183end
clip_183high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x22, clip_183end
    lui x22, 0x8
    addi x22, x22, -1
clip_183end:
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
