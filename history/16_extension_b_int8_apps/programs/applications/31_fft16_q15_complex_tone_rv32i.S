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
    bge x10, x0, mul_404a
    sub x10, x0, x10
mul_404a:
    bge x11, x0, mul_404b
    sub x11, x0, x11
mul_404b:
    addi x6, x0, 0
mul_404loop:
    beq x11, x0, mul_404done
    andi x7, x11, 1
    beq x7, x0, mul_404skip
    add x6, x6, x10
mul_404skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_404loop
mul_404done:
    bge x5, x0, mul_404positive
    sub x6, x0, x6
mul_404positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_405a
    sub x10, x0, x10
mul_405a:
    bge x11, x0, mul_405b
    sub x11, x0, x11
mul_405b:
    addi x6, x0, 0
mul_405loop:
    beq x11, x0, mul_405done
    andi x7, x11, 1
    beq x7, x0, mul_405skip
    add x6, x6, x10
mul_405skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_405loop
mul_405done:
    bge x5, x0, mul_405positive
    sub x6, x0, x6
mul_405positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_406a
    sub x10, x0, x10
mul_406a:
    bge x11, x0, mul_406b
    sub x11, x0, x11
mul_406b:
    addi x6, x0, 0
mul_406loop:
    beq x11, x0, mul_406done
    andi x7, x11, 1
    beq x7, x0, mul_406skip
    add x6, x6, x10
mul_406skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_406loop
mul_406done:
    bge x5, x0, mul_406positive
    sub x6, x0, x6
mul_406positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_407a
    sub x10, x0, x10
mul_407a:
    bge x11, x0, mul_407b
    sub x11, x0, x11
mul_407b:
    addi x6, x0, 0
mul_407loop:
    beq x11, x0, mul_407done
    andi x7, x11, 1
    beq x7, x0, mul_407skip
    add x6, x6, x10
mul_407skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_407loop
mul_407done:
    bge x5, x0, mul_407positive
    sub x6, x0, x6
mul_407positive:
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
    bge x10, x5, clip_408high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_408end
clip_408high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_408end
    lui x10, 0x8
    addi x10, x10, -1
clip_408end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_409high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_409end
clip_409high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_409end
    lui x11, 0x8
    addi x11, x11, -1
clip_409end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_410high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_410end
clip_410high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_410end
    lui x12, 0x8
    addi x12, x12, -1
clip_410end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_411high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_411end
clip_411high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_411end
    lui x13, 0x8
    addi x13, x13, -1
clip_411end:
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
    bge x10, x0, mul_412a
    sub x10, x0, x10
mul_412a:
    bge x11, x0, mul_412b
    sub x11, x0, x11
mul_412b:
    addi x6, x0, 0
mul_412loop:
    beq x11, x0, mul_412done
    andi x7, x11, 1
    beq x7, x0, mul_412skip
    add x6, x6, x10
mul_412skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_412loop
mul_412done:
    bge x5, x0, mul_412positive
    sub x6, x0, x6
mul_412positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_413a
    sub x10, x0, x10
mul_413a:
    bge x11, x0, mul_413b
    sub x11, x0, x11
mul_413b:
    addi x6, x0, 0
mul_413loop:
    beq x11, x0, mul_413done
    andi x7, x11, 1
    beq x7, x0, mul_413skip
    add x6, x6, x10
mul_413skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_413loop
mul_413done:
    bge x5, x0, mul_413positive
    sub x6, x0, x6
mul_413positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_414a
    sub x10, x0, x10
mul_414a:
    bge x11, x0, mul_414b
    sub x11, x0, x11
mul_414b:
    addi x6, x0, 0
mul_414loop:
    beq x11, x0, mul_414done
    andi x7, x11, 1
    beq x7, x0, mul_414skip
    add x6, x6, x10
mul_414skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_414loop
mul_414done:
    bge x5, x0, mul_414positive
    sub x6, x0, x6
mul_414positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_415a
    sub x10, x0, x10
mul_415a:
    bge x11, x0, mul_415b
    sub x11, x0, x11
mul_415b:
    addi x6, x0, 0
mul_415loop:
    beq x11, x0, mul_415done
    andi x7, x11, 1
    beq x7, x0, mul_415skip
    add x6, x6, x10
mul_415skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_415loop
mul_415done:
    bge x5, x0, mul_415positive
    sub x6, x0, x6
mul_415positive:
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
    bge x10, x5, clip_416high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_416end
clip_416high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_416end
    lui x10, 0x8
    addi x10, x10, -1
clip_416end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_417high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_417end
clip_417high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_417end
    lui x11, 0x8
    addi x11, x11, -1
clip_417end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_418high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_418end
clip_418high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_418end
    lui x12, 0x8
    addi x12, x12, -1
clip_418end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_419high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_419end
clip_419high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_419end
    lui x13, 0x8
    addi x13, x13, -1
clip_419end:
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
    bge x10, x0, mul_420a
    sub x10, x0, x10
mul_420a:
    bge x11, x0, mul_420b
    sub x11, x0, x11
mul_420b:
    addi x6, x0, 0
mul_420loop:
    beq x11, x0, mul_420done
    andi x7, x11, 1
    beq x7, x0, mul_420skip
    add x6, x6, x10
mul_420skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_420loop
mul_420done:
    bge x5, x0, mul_420positive
    sub x6, x0, x6
mul_420positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_421a
    sub x10, x0, x10
mul_421a:
    bge x11, x0, mul_421b
    sub x11, x0, x11
mul_421b:
    addi x6, x0, 0
mul_421loop:
    beq x11, x0, mul_421done
    andi x7, x11, 1
    beq x7, x0, mul_421skip
    add x6, x6, x10
mul_421skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_421loop
mul_421done:
    bge x5, x0, mul_421positive
    sub x6, x0, x6
mul_421positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_422a
    sub x10, x0, x10
mul_422a:
    bge x11, x0, mul_422b
    sub x11, x0, x11
mul_422b:
    addi x6, x0, 0
mul_422loop:
    beq x11, x0, mul_422done
    andi x7, x11, 1
    beq x7, x0, mul_422skip
    add x6, x6, x10
mul_422skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_422loop
mul_422done:
    bge x5, x0, mul_422positive
    sub x6, x0, x6
mul_422positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_423a
    sub x10, x0, x10
mul_423a:
    bge x11, x0, mul_423b
    sub x11, x0, x11
mul_423b:
    addi x6, x0, 0
mul_423loop:
    beq x11, x0, mul_423done
    andi x7, x11, 1
    beq x7, x0, mul_423skip
    add x6, x6, x10
mul_423skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_423loop
mul_423done:
    bge x5, x0, mul_423positive
    sub x6, x0, x6
mul_423positive:
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
    bge x10, x5, clip_424high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_424end
clip_424high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_424end
    lui x10, 0x8
    addi x10, x10, -1
clip_424end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_425high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_425end
clip_425high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_425end
    lui x11, 0x8
    addi x11, x11, -1
clip_425end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_426high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_426end
clip_426high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_426end
    lui x12, 0x8
    addi x12, x12, -1
clip_426end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_427high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_427end
clip_427high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_427end
    lui x13, 0x8
    addi x13, x13, -1
clip_427end:
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
    bge x10, x0, mul_428a
    sub x10, x0, x10
mul_428a:
    bge x11, x0, mul_428b
    sub x11, x0, x11
mul_428b:
    addi x6, x0, 0
mul_428loop:
    beq x11, x0, mul_428done
    andi x7, x11, 1
    beq x7, x0, mul_428skip
    add x6, x6, x10
mul_428skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_428loop
mul_428done:
    bge x5, x0, mul_428positive
    sub x6, x0, x6
mul_428positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_429a
    sub x10, x0, x10
mul_429a:
    bge x11, x0, mul_429b
    sub x11, x0, x11
mul_429b:
    addi x6, x0, 0
mul_429loop:
    beq x11, x0, mul_429done
    andi x7, x11, 1
    beq x7, x0, mul_429skip
    add x6, x6, x10
mul_429skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_429loop
mul_429done:
    bge x5, x0, mul_429positive
    sub x6, x0, x6
mul_429positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_430a
    sub x10, x0, x10
mul_430a:
    bge x11, x0, mul_430b
    sub x11, x0, x11
mul_430b:
    addi x6, x0, 0
mul_430loop:
    beq x11, x0, mul_430done
    andi x7, x11, 1
    beq x7, x0, mul_430skip
    add x6, x6, x10
mul_430skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_430loop
mul_430done:
    bge x5, x0, mul_430positive
    sub x6, x0, x6
mul_430positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_431a
    sub x10, x0, x10
mul_431a:
    bge x11, x0, mul_431b
    sub x11, x0, x11
mul_431b:
    addi x6, x0, 0
mul_431loop:
    beq x11, x0, mul_431done
    andi x7, x11, 1
    beq x7, x0, mul_431skip
    add x6, x6, x10
mul_431skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_431loop
mul_431done:
    bge x5, x0, mul_431positive
    sub x6, x0, x6
mul_431positive:
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
    bge x10, x5, clip_432high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_432end
clip_432high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_432end
    lui x10, 0x8
    addi x10, x10, -1
clip_432end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_433high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_433end
clip_433high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_433end
    lui x11, 0x8
    addi x11, x11, -1
clip_433end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_434high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_434end
clip_434high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_434end
    lui x12, 0x8
    addi x12, x12, -1
clip_434end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_435high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_435end
clip_435high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_435end
    lui x13, 0x8
    addi x13, x13, -1
clip_435end:
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
