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
    .insn r 0x0b, 1, 1, x22, x10, x11 # MAC16
    addi x10, x24, 0
    addi x11, x9, 0
    .insn r 0x0b, 1, 1, x22, x10, x11 # MAC16
    srai x22, x22, 15
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x22, x5, clip_211high
    lui x22, 0xffff8
    addi x22, x22, 0
    jal x0, clip_211end
clip_211high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x22, clip_211end
    lui x22, 0x8
    addi x22, x22, -1
clip_211end:
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
