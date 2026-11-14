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
    bge x10, x0, mul_308a
    sub x10, x0, x10
mul_308a:
    bge x11, x0, mul_308b
    sub x11, x0, x11
mul_308b:
    addi x6, x0, 0
mul_308loop:
    beq x11, x0, mul_308done
    andi x7, x11, 1
    beq x7, x0, mul_308skip
    add x6, x6, x10
mul_308skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_308loop
mul_308done:
    bge x5, x0, mul_308positive
    sub x6, x0, x6
mul_308positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_309a
    sub x10, x0, x10
mul_309a:
    bge x11, x0, mul_309b
    sub x11, x0, x11
mul_309b:
    addi x6, x0, 0
mul_309loop:
    beq x11, x0, mul_309done
    andi x7, x11, 1
    beq x7, x0, mul_309skip
    add x6, x6, x10
mul_309skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_309loop
mul_309done:
    bge x5, x0, mul_309positive
    sub x6, x0, x6
mul_309positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_310a
    sub x10, x0, x10
mul_310a:
    bge x11, x0, mul_310b
    sub x11, x0, x11
mul_310b:
    addi x6, x0, 0
mul_310loop:
    beq x11, x0, mul_310done
    andi x7, x11, 1
    beq x7, x0, mul_310skip
    add x6, x6, x10
mul_310skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_310loop
mul_310done:
    bge x5, x0, mul_310positive
    sub x6, x0, x6
mul_310positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_311a
    sub x10, x0, x10
mul_311a:
    bge x11, x0, mul_311b
    sub x11, x0, x11
mul_311b:
    addi x6, x0, 0
mul_311loop:
    beq x11, x0, mul_311done
    andi x7, x11, 1
    beq x7, x0, mul_311skip
    add x6, x6, x10
mul_311skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_311loop
mul_311done:
    bge x5, x0, mul_311positive
    sub x6, x0, x6
mul_311positive:
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
    bge x10, x5, clip_312high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_312end
clip_312high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_312end
    lui x10, 0x8
    addi x10, x10, -1
clip_312end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_313high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_313end
clip_313high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_313end
    lui x11, 0x8
    addi x11, x11, -1
clip_313end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_314high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_314end
clip_314high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_314end
    lui x12, 0x8
    addi x12, x12, -1
clip_314end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_315high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_315end
clip_315high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_315end
    lui x13, 0x8
    addi x13, x13, -1
clip_315end:
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
    bge x10, x0, mul_316a
    sub x10, x0, x10
mul_316a:
    bge x11, x0, mul_316b
    sub x11, x0, x11
mul_316b:
    addi x6, x0, 0
mul_316loop:
    beq x11, x0, mul_316done
    andi x7, x11, 1
    beq x7, x0, mul_316skip
    add x6, x6, x10
mul_316skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_316loop
mul_316done:
    bge x5, x0, mul_316positive
    sub x6, x0, x6
mul_316positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_317a
    sub x10, x0, x10
mul_317a:
    bge x11, x0, mul_317b
    sub x11, x0, x11
mul_317b:
    addi x6, x0, 0
mul_317loop:
    beq x11, x0, mul_317done
    andi x7, x11, 1
    beq x7, x0, mul_317skip
    add x6, x6, x10
mul_317skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_317loop
mul_317done:
    bge x5, x0, mul_317positive
    sub x6, x0, x6
mul_317positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_318a
    sub x10, x0, x10
mul_318a:
    bge x11, x0, mul_318b
    sub x11, x0, x11
mul_318b:
    addi x6, x0, 0
mul_318loop:
    beq x11, x0, mul_318done
    andi x7, x11, 1
    beq x7, x0, mul_318skip
    add x6, x6, x10
mul_318skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_318loop
mul_318done:
    bge x5, x0, mul_318positive
    sub x6, x0, x6
mul_318positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_319a
    sub x10, x0, x10
mul_319a:
    bge x11, x0, mul_319b
    sub x11, x0, x11
mul_319b:
    addi x6, x0, 0
mul_319loop:
    beq x11, x0, mul_319done
    andi x7, x11, 1
    beq x7, x0, mul_319skip
    add x6, x6, x10
mul_319skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_319loop
mul_319done:
    bge x5, x0, mul_319positive
    sub x6, x0, x6
mul_319positive:
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
    bge x10, x5, clip_320high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_320end
clip_320high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_320end
    lui x10, 0x8
    addi x10, x10, -1
clip_320end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_321high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_321end
clip_321high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_321end
    lui x11, 0x8
    addi x11, x11, -1
clip_321end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_322high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_322end
clip_322high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_322end
    lui x12, 0x8
    addi x12, x12, -1
clip_322end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_323high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_323end
clip_323high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_323end
    lui x13, 0x8
    addi x13, x13, -1
clip_323end:
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
    bge x10, x0, mul_324a
    sub x10, x0, x10
mul_324a:
    bge x11, x0, mul_324b
    sub x11, x0, x11
mul_324b:
    addi x6, x0, 0
mul_324loop:
    beq x11, x0, mul_324done
    andi x7, x11, 1
    beq x7, x0, mul_324skip
    add x6, x6, x10
mul_324skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_324loop
mul_324done:
    bge x5, x0, mul_324positive
    sub x6, x0, x6
mul_324positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_325a
    sub x10, x0, x10
mul_325a:
    bge x11, x0, mul_325b
    sub x11, x0, x11
mul_325b:
    addi x6, x0, 0
mul_325loop:
    beq x11, x0, mul_325done
    andi x7, x11, 1
    beq x7, x0, mul_325skip
    add x6, x6, x10
mul_325skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_325loop
mul_325done:
    bge x5, x0, mul_325positive
    sub x6, x0, x6
mul_325positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_326a
    sub x10, x0, x10
mul_326a:
    bge x11, x0, mul_326b
    sub x11, x0, x11
mul_326b:
    addi x6, x0, 0
mul_326loop:
    beq x11, x0, mul_326done
    andi x7, x11, 1
    beq x7, x0, mul_326skip
    add x6, x6, x10
mul_326skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_326loop
mul_326done:
    bge x5, x0, mul_326positive
    sub x6, x0, x6
mul_326positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_327a
    sub x10, x0, x10
mul_327a:
    bge x11, x0, mul_327b
    sub x11, x0, x11
mul_327b:
    addi x6, x0, 0
mul_327loop:
    beq x11, x0, mul_327done
    andi x7, x11, 1
    beq x7, x0, mul_327skip
    add x6, x6, x10
mul_327skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_327loop
mul_327done:
    bge x5, x0, mul_327positive
    sub x6, x0, x6
mul_327positive:
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
    bge x10, x5, clip_328high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_328end
clip_328high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_328end
    lui x10, 0x8
    addi x10, x10, -1
clip_328end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_329high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_329end
clip_329high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_329end
    lui x11, 0x8
    addi x11, x11, -1
clip_329end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_330high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_330end
clip_330high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_330end
    lui x12, 0x8
    addi x12, x12, -1
clip_330end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_331high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_331end
clip_331high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_331end
    lui x13, 0x8
    addi x13, x13, -1
clip_331end:
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
    bge x10, x0, mul_332a
    sub x10, x0, x10
mul_332a:
    bge x11, x0, mul_332b
    sub x11, x0, x11
mul_332b:
    addi x6, x0, 0
mul_332loop:
    beq x11, x0, mul_332done
    andi x7, x11, 1
    beq x7, x0, mul_332skip
    add x6, x6, x10
mul_332skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_332loop
mul_332done:
    bge x5, x0, mul_332positive
    sub x6, x0, x6
mul_332positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_333a
    sub x10, x0, x10
mul_333a:
    bge x11, x0, mul_333b
    sub x11, x0, x11
mul_333b:
    addi x6, x0, 0
mul_333loop:
    beq x11, x0, mul_333done
    andi x7, x11, 1
    beq x7, x0, mul_333skip
    add x6, x6, x10
mul_333skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_333loop
mul_333done:
    bge x5, x0, mul_333positive
    sub x6, x0, x6
mul_333positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_334a
    sub x10, x0, x10
mul_334a:
    bge x11, x0, mul_334b
    sub x11, x0, x11
mul_334b:
    addi x6, x0, 0
mul_334loop:
    beq x11, x0, mul_334done
    andi x7, x11, 1
    beq x7, x0, mul_334skip
    add x6, x6, x10
mul_334skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_334loop
mul_334done:
    bge x5, x0, mul_334positive
    sub x6, x0, x6
mul_334positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_335a
    sub x10, x0, x10
mul_335a:
    bge x11, x0, mul_335b
    sub x11, x0, x11
mul_335b:
    addi x6, x0, 0
mul_335loop:
    beq x11, x0, mul_335done
    andi x7, x11, 1
    beq x7, x0, mul_335skip
    add x6, x6, x10
mul_335skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_335loop
mul_335done:
    bge x5, x0, mul_335positive
    sub x6, x0, x6
mul_335positive:
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
    bge x10, x5, clip_336high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_336end
clip_336high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_336end
    lui x10, 0x8
    addi x10, x10, -1
clip_336end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_337high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_337end
clip_337high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_337end
    lui x11, 0x8
    addi x11, x11, -1
clip_337end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_338high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_338end
clip_338high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_338end
    lui x12, 0x8
    addi x12, x12, -1
clip_338end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_339high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_339end
clip_339high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_339end
    lui x13, 0x8
    addi x13, x13, -1
clip_339end:
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
