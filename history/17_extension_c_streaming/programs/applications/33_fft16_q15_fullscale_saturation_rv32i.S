.section .text
.globl _start
_start:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 1280
    lui x19, 0x10001
    addi x19, x19, 1024
    lh x10, 0(x18)
    lh x11, 2(x18)
    sw x10, 0(x19)
    sw x11, 4(x19)
    lh x10, 32(x18)
    lh x11, 34(x18)
    sw x10, 8(x19)
    sw x11, 12(x19)
    lh x10, 16(x18)
    lh x11, 18(x18)
    sw x10, 16(x19)
    sw x11, 20(x19)
    lh x10, 48(x18)
    lh x11, 50(x18)
    sw x10, 24(x19)
    sw x11, 28(x19)
    lh x10, 8(x18)
    lh x11, 10(x18)
    sw x10, 32(x19)
    sw x11, 36(x19)
    lh x10, 40(x18)
    lh x11, 42(x18)
    sw x10, 40(x19)
    sw x11, 44(x19)
    lh x10, 24(x18)
    lh x11, 26(x18)
    sw x10, 48(x19)
    sw x11, 52(x19)
    lh x10, 56(x18)
    lh x11, 58(x18)
    sw x10, 56(x19)
    sw x11, 60(x19)
    lh x10, 4(x18)
    lh x11, 6(x18)
    sw x10, 64(x19)
    sw x11, 68(x19)
    lh x10, 36(x18)
    lh x11, 38(x18)
    sw x10, 72(x19)
    sw x11, 76(x19)
    lh x10, 20(x18)
    lh x11, 22(x18)
    sw x10, 80(x19)
    sw x11, 84(x19)
    lh x10, 52(x18)
    lh x11, 54(x18)
    sw x10, 88(x19)
    sw x11, 92(x19)
    lh x10, 12(x18)
    lh x11, 14(x18)
    sw x10, 96(x19)
    sw x11, 100(x19)
    lh x10, 44(x18)
    lh x11, 46(x18)
    sw x10, 104(x19)
    sw x11, 108(x19)
    lh x10, 28(x18)
    lh x11, 30(x18)
    sw x10, 112(x19)
    sw x11, 116(x19)
    lh x10, 60(x18)
    lh x11, 62(x18)
    sw x10, 120(x19)
    sw x11, 124(x19)
    lui x18, 0x10001
    addi x18, x18, 1024
    addi x23, x0, 8
fft2_group:
    addi x19, x18, 8
    lui x17, 0x10000
    addi x17, x17, 1408
    addi x20, x0, 1
fft2_butterfly:
    lw x24, 0(x19)
    lw x25, 4(x19)
    lw x26, 0(x18)
    lw x27, 4(x18)
    lh x8, 0(x17)
    lh x9, 2(x17)
    addi x10, x24, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_500a
    sub x10, x0, x10
mul_500a:
    bge x11, x0, mul_500b
    sub x11, x0, x11
mul_500b:
    addi x6, x0, 0
mul_500loop:
    beq x11, x0, mul_500done
    andi x7, x11, 1
    beq x7, x0, mul_500skip
    add x6, x6, x10
mul_500skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_500loop
mul_500done:
    bge x5, x0, mul_500positive
    sub x6, x0, x6
mul_500positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_501a
    sub x10, x0, x10
mul_501a:
    bge x11, x0, mul_501b
    sub x11, x0, x11
mul_501b:
    addi x6, x0, 0
mul_501loop:
    beq x11, x0, mul_501done
    andi x7, x11, 1
    beq x7, x0, mul_501skip
    add x6, x6, x10
mul_501skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_501loop
mul_501done:
    bge x5, x0, mul_501positive
    sub x6, x0, x6
mul_501positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_502a
    sub x10, x0, x10
mul_502a:
    bge x11, x0, mul_502b
    sub x11, x0, x11
mul_502b:
    addi x6, x0, 0
mul_502loop:
    beq x11, x0, mul_502done
    andi x7, x11, 1
    beq x7, x0, mul_502skip
    add x6, x6, x10
mul_502skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_502loop
mul_502done:
    bge x5, x0, mul_502positive
    sub x6, x0, x6
mul_502positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_503a
    sub x10, x0, x10
mul_503a:
    bge x11, x0, mul_503b
    sub x11, x0, x11
mul_503b:
    addi x6, x0, 0
mul_503loop:
    beq x11, x0, mul_503done
    andi x7, x11, 1
    beq x7, x0, mul_503skip
    add x6, x6, x10
mul_503skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_503loop
mul_503done:
    bge x5, x0, mul_503positive
    sub x6, x0, x6
mul_503positive:
    addi x10, x6, 0
    add x29, x29, x10
    srai x29, x29, 15
    add x10, x26, x28
    add x11, x27, x29
    sub x12, x26, x28
    sub x13, x27, x29
    srai x10, x10, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x10, x5, clip_504high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_504end
clip_504high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_504end
    lui x10, 0x8
    addi x10, x10, -1
clip_504end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_505high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_505end
clip_505high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_505end
    lui x11, 0x8
    addi x11, x11, -1
clip_505end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_506high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_506end
clip_506high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_506end
    lui x12, 0x8
    addi x12, x12, -1
clip_506end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_507high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_507end
clip_507high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_507end
    lui x13, 0x8
    addi x13, x13, -1
clip_507end:
    sw x10, 0(x18)
    sw x11, 4(x18)
    sw x12, 0(x19)
    sw x13, 4(x19)
    addi x18, x18, 8
    addi x19, x19, 8
    addi x17, x17, 32
    addi x20, x20, -1
    bne x20, x0, fft2_butterfly
    addi x18, x18, 8
    addi x23, x23, -1
    bne x23, x0, fft2_group
    lui x18, 0x10001
    addi x18, x18, 1024
    addi x23, x0, 4
fft4_group:
    addi x19, x18, 16
    lui x17, 0x10000
    addi x17, x17, 1408
    addi x20, x0, 2
fft4_butterfly:
    lw x24, 0(x19)
    lw x25, 4(x19)
    lw x26, 0(x18)
    lw x27, 4(x18)
    lh x8, 0(x17)
    lh x9, 2(x17)
    addi x10, x24, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_508a
    sub x10, x0, x10
mul_508a:
    bge x11, x0, mul_508b
    sub x11, x0, x11
mul_508b:
    addi x6, x0, 0
mul_508loop:
    beq x11, x0, mul_508done
    andi x7, x11, 1
    beq x7, x0, mul_508skip
    add x6, x6, x10
mul_508skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_508loop
mul_508done:
    bge x5, x0, mul_508positive
    sub x6, x0, x6
mul_508positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_509a
    sub x10, x0, x10
mul_509a:
    bge x11, x0, mul_509b
    sub x11, x0, x11
mul_509b:
    addi x6, x0, 0
mul_509loop:
    beq x11, x0, mul_509done
    andi x7, x11, 1
    beq x7, x0, mul_509skip
    add x6, x6, x10
mul_509skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_509loop
mul_509done:
    bge x5, x0, mul_509positive
    sub x6, x0, x6
mul_509positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_510a
    sub x10, x0, x10
mul_510a:
    bge x11, x0, mul_510b
    sub x11, x0, x11
mul_510b:
    addi x6, x0, 0
mul_510loop:
    beq x11, x0, mul_510done
    andi x7, x11, 1
    beq x7, x0, mul_510skip
    add x6, x6, x10
mul_510skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_510loop
mul_510done:
    bge x5, x0, mul_510positive
    sub x6, x0, x6
mul_510positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_511a
    sub x10, x0, x10
mul_511a:
    bge x11, x0, mul_511b
    sub x11, x0, x11
mul_511b:
    addi x6, x0, 0
mul_511loop:
    beq x11, x0, mul_511done
    andi x7, x11, 1
    beq x7, x0, mul_511skip
    add x6, x6, x10
mul_511skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_511loop
mul_511done:
    bge x5, x0, mul_511positive
    sub x6, x0, x6
mul_511positive:
    addi x10, x6, 0
    add x29, x29, x10
    srai x29, x29, 15
    add x10, x26, x28
    add x11, x27, x29
    sub x12, x26, x28
    sub x13, x27, x29
    srai x10, x10, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x10, x5, clip_512high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_512end
clip_512high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_512end
    lui x10, 0x8
    addi x10, x10, -1
clip_512end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_513high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_513end
clip_513high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_513end
    lui x11, 0x8
    addi x11, x11, -1
clip_513end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_514high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_514end
clip_514high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_514end
    lui x12, 0x8
    addi x12, x12, -1
clip_514end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_515high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_515end
clip_515high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_515end
    lui x13, 0x8
    addi x13, x13, -1
clip_515end:
    sw x10, 0(x18)
    sw x11, 4(x18)
    sw x12, 0(x19)
    sw x13, 4(x19)
    addi x18, x18, 8
    addi x19, x19, 8
    addi x17, x17, 16
    addi x20, x20, -1
    bne x20, x0, fft4_butterfly
    addi x18, x18, 16
    addi x23, x23, -1
    bne x23, x0, fft4_group
    lui x18, 0x10001
    addi x18, x18, 1024
    addi x23, x0, 2
fft8_group:
    addi x19, x18, 32
    lui x17, 0x10000
    addi x17, x17, 1408
    addi x20, x0, 4
fft8_butterfly:
    lw x24, 0(x19)
    lw x25, 4(x19)
    lw x26, 0(x18)
    lw x27, 4(x18)
    lh x8, 0(x17)
    lh x9, 2(x17)
    addi x10, x24, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_516a
    sub x10, x0, x10
mul_516a:
    bge x11, x0, mul_516b
    sub x11, x0, x11
mul_516b:
    addi x6, x0, 0
mul_516loop:
    beq x11, x0, mul_516done
    andi x7, x11, 1
    beq x7, x0, mul_516skip
    add x6, x6, x10
mul_516skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_516loop
mul_516done:
    bge x5, x0, mul_516positive
    sub x6, x0, x6
mul_516positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_517a
    sub x10, x0, x10
mul_517a:
    bge x11, x0, mul_517b
    sub x11, x0, x11
mul_517b:
    addi x6, x0, 0
mul_517loop:
    beq x11, x0, mul_517done
    andi x7, x11, 1
    beq x7, x0, mul_517skip
    add x6, x6, x10
mul_517skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_517loop
mul_517done:
    bge x5, x0, mul_517positive
    sub x6, x0, x6
mul_517positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_518a
    sub x10, x0, x10
mul_518a:
    bge x11, x0, mul_518b
    sub x11, x0, x11
mul_518b:
    addi x6, x0, 0
mul_518loop:
    beq x11, x0, mul_518done
    andi x7, x11, 1
    beq x7, x0, mul_518skip
    add x6, x6, x10
mul_518skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_518loop
mul_518done:
    bge x5, x0, mul_518positive
    sub x6, x0, x6
mul_518positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_519a
    sub x10, x0, x10
mul_519a:
    bge x11, x0, mul_519b
    sub x11, x0, x11
mul_519b:
    addi x6, x0, 0
mul_519loop:
    beq x11, x0, mul_519done
    andi x7, x11, 1
    beq x7, x0, mul_519skip
    add x6, x6, x10
mul_519skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_519loop
mul_519done:
    bge x5, x0, mul_519positive
    sub x6, x0, x6
mul_519positive:
    addi x10, x6, 0
    add x29, x29, x10
    srai x29, x29, 15
    add x10, x26, x28
    add x11, x27, x29
    sub x12, x26, x28
    sub x13, x27, x29
    srai x10, x10, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x10, x5, clip_520high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_520end
clip_520high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_520end
    lui x10, 0x8
    addi x10, x10, -1
clip_520end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_521high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_521end
clip_521high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_521end
    lui x11, 0x8
    addi x11, x11, -1
clip_521end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_522high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_522end
clip_522high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_522end
    lui x12, 0x8
    addi x12, x12, -1
clip_522end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_523high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_523end
clip_523high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_523end
    lui x13, 0x8
    addi x13, x13, -1
clip_523end:
    sw x10, 0(x18)
    sw x11, 4(x18)
    sw x12, 0(x19)
    sw x13, 4(x19)
    addi x18, x18, 8
    addi x19, x19, 8
    addi x17, x17, 8
    addi x20, x20, -1
    bne x20, x0, fft8_butterfly
    addi x18, x18, 32
    addi x23, x23, -1
    bne x23, x0, fft8_group
    lui x18, 0x10001
    addi x18, x18, 1024
    addi x23, x0, 1
fft16_group:
    addi x19, x18, 64
    lui x17, 0x10000
    addi x17, x17, 1408
    addi x20, x0, 8
fft16_butterfly:
    lw x24, 0(x19)
    lw x25, 4(x19)
    lw x26, 0(x18)
    lw x27, 4(x18)
    lh x8, 0(x17)
    lh x9, 2(x17)
    addi x10, x24, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_524a
    sub x10, x0, x10
mul_524a:
    bge x11, x0, mul_524b
    sub x11, x0, x11
mul_524b:
    addi x6, x0, 0
mul_524loop:
    beq x11, x0, mul_524done
    andi x7, x11, 1
    beq x7, x0, mul_524skip
    add x6, x6, x10
mul_524skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_524loop
mul_524done:
    bge x5, x0, mul_524positive
    sub x6, x0, x6
mul_524positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_525a
    sub x10, x0, x10
mul_525a:
    bge x11, x0, mul_525b
    sub x11, x0, x11
mul_525b:
    addi x6, x0, 0
mul_525loop:
    beq x11, x0, mul_525done
    andi x7, x11, 1
    beq x7, x0, mul_525skip
    add x6, x6, x10
mul_525skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_525loop
mul_525done:
    bge x5, x0, mul_525positive
    sub x6, x0, x6
mul_525positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_526a
    sub x10, x0, x10
mul_526a:
    bge x11, x0, mul_526b
    sub x11, x0, x11
mul_526b:
    addi x6, x0, 0
mul_526loop:
    beq x11, x0, mul_526done
    andi x7, x11, 1
    beq x7, x0, mul_526skip
    add x6, x6, x10
mul_526skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_526loop
mul_526done:
    bge x5, x0, mul_526positive
    sub x6, x0, x6
mul_526positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_527a
    sub x10, x0, x10
mul_527a:
    bge x11, x0, mul_527b
    sub x11, x0, x11
mul_527b:
    addi x6, x0, 0
mul_527loop:
    beq x11, x0, mul_527done
    andi x7, x11, 1
    beq x7, x0, mul_527skip
    add x6, x6, x10
mul_527skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_527loop
mul_527done:
    bge x5, x0, mul_527positive
    sub x6, x0, x6
mul_527positive:
    addi x10, x6, 0
    add x29, x29, x10
    srai x29, x29, 15
    add x10, x26, x28
    add x11, x27, x29
    sub x12, x26, x28
    sub x13, x27, x29
    srai x10, x10, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x10, x5, clip_528high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_528end
clip_528high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_528end
    lui x10, 0x8
    addi x10, x10, -1
clip_528end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_529high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_529end
clip_529high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_529end
    lui x11, 0x8
    addi x11, x11, -1
clip_529end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_530high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_530end
clip_530high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_530end
    lui x12, 0x8
    addi x12, x12, -1
clip_530end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_531high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_531end
clip_531high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_531end
    lui x13, 0x8
    addi x13, x13, -1
clip_531end:
    sw x10, 0(x18)
    sw x11, 4(x18)
    sw x12, 0(x19)
    sw x13, 4(x19)
    addi x18, x18, 8
    addi x19, x19, 8
    addi x17, x17, 4
    addi x20, x20, -1
    bne x20, x0, fft16_butterfly
    addi x18, x18, 64
    addi x23, x23, -1
    bne x23, x0, fft16_group
kernel_end:
    lui x30, 0x20000
    addi x30, x30, 0
    addi x10, x0, 1
    sw x10, 0(x30)
    ebreak
