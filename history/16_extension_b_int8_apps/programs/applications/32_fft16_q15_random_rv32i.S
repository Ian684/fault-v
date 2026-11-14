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
    bge x10, x0, mul_452a
    sub x10, x0, x10
mul_452a:
    bge x11, x0, mul_452b
    sub x11, x0, x11
mul_452b:
    addi x6, x0, 0
mul_452loop:
    beq x11, x0, mul_452done
    andi x7, x11, 1
    beq x7, x0, mul_452skip
    add x6, x6, x10
mul_452skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_452loop
mul_452done:
    bge x5, x0, mul_452positive
    sub x6, x0, x6
mul_452positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_453a
    sub x10, x0, x10
mul_453a:
    bge x11, x0, mul_453b
    sub x11, x0, x11
mul_453b:
    addi x6, x0, 0
mul_453loop:
    beq x11, x0, mul_453done
    andi x7, x11, 1
    beq x7, x0, mul_453skip
    add x6, x6, x10
mul_453skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_453loop
mul_453done:
    bge x5, x0, mul_453positive
    sub x6, x0, x6
mul_453positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_454a
    sub x10, x0, x10
mul_454a:
    bge x11, x0, mul_454b
    sub x11, x0, x11
mul_454b:
    addi x6, x0, 0
mul_454loop:
    beq x11, x0, mul_454done
    andi x7, x11, 1
    beq x7, x0, mul_454skip
    add x6, x6, x10
mul_454skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_454loop
mul_454done:
    bge x5, x0, mul_454positive
    sub x6, x0, x6
mul_454positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_455a
    sub x10, x0, x10
mul_455a:
    bge x11, x0, mul_455b
    sub x11, x0, x11
mul_455b:
    addi x6, x0, 0
mul_455loop:
    beq x11, x0, mul_455done
    andi x7, x11, 1
    beq x7, x0, mul_455skip
    add x6, x6, x10
mul_455skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_455loop
mul_455done:
    bge x5, x0, mul_455positive
    sub x6, x0, x6
mul_455positive:
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
    bge x10, x5, clip_456high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_456end
clip_456high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_456end
    lui x10, 0x8
    addi x10, x10, -1
clip_456end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_457high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_457end
clip_457high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_457end
    lui x11, 0x8
    addi x11, x11, -1
clip_457end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_458high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_458end
clip_458high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_458end
    lui x12, 0x8
    addi x12, x12, -1
clip_458end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_459high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_459end
clip_459high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_459end
    lui x13, 0x8
    addi x13, x13, -1
clip_459end:
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
    bge x10, x0, mul_460a
    sub x10, x0, x10
mul_460a:
    bge x11, x0, mul_460b
    sub x11, x0, x11
mul_460b:
    addi x6, x0, 0
mul_460loop:
    beq x11, x0, mul_460done
    andi x7, x11, 1
    beq x7, x0, mul_460skip
    add x6, x6, x10
mul_460skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_460loop
mul_460done:
    bge x5, x0, mul_460positive
    sub x6, x0, x6
mul_460positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_461a
    sub x10, x0, x10
mul_461a:
    bge x11, x0, mul_461b
    sub x11, x0, x11
mul_461b:
    addi x6, x0, 0
mul_461loop:
    beq x11, x0, mul_461done
    andi x7, x11, 1
    beq x7, x0, mul_461skip
    add x6, x6, x10
mul_461skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_461loop
mul_461done:
    bge x5, x0, mul_461positive
    sub x6, x0, x6
mul_461positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_462a
    sub x10, x0, x10
mul_462a:
    bge x11, x0, mul_462b
    sub x11, x0, x11
mul_462b:
    addi x6, x0, 0
mul_462loop:
    beq x11, x0, mul_462done
    andi x7, x11, 1
    beq x7, x0, mul_462skip
    add x6, x6, x10
mul_462skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_462loop
mul_462done:
    bge x5, x0, mul_462positive
    sub x6, x0, x6
mul_462positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_463a
    sub x10, x0, x10
mul_463a:
    bge x11, x0, mul_463b
    sub x11, x0, x11
mul_463b:
    addi x6, x0, 0
mul_463loop:
    beq x11, x0, mul_463done
    andi x7, x11, 1
    beq x7, x0, mul_463skip
    add x6, x6, x10
mul_463skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_463loop
mul_463done:
    bge x5, x0, mul_463positive
    sub x6, x0, x6
mul_463positive:
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
    bge x10, x5, clip_464high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_464end
clip_464high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_464end
    lui x10, 0x8
    addi x10, x10, -1
clip_464end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_465high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_465end
clip_465high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_465end
    lui x11, 0x8
    addi x11, x11, -1
clip_465end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_466high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_466end
clip_466high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_466end
    lui x12, 0x8
    addi x12, x12, -1
clip_466end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_467high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_467end
clip_467high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_467end
    lui x13, 0x8
    addi x13, x13, -1
clip_467end:
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
    bge x10, x0, mul_468a
    sub x10, x0, x10
mul_468a:
    bge x11, x0, mul_468b
    sub x11, x0, x11
mul_468b:
    addi x6, x0, 0
mul_468loop:
    beq x11, x0, mul_468done
    andi x7, x11, 1
    beq x7, x0, mul_468skip
    add x6, x6, x10
mul_468skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_468loop
mul_468done:
    bge x5, x0, mul_468positive
    sub x6, x0, x6
mul_468positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_469a
    sub x10, x0, x10
mul_469a:
    bge x11, x0, mul_469b
    sub x11, x0, x11
mul_469b:
    addi x6, x0, 0
mul_469loop:
    beq x11, x0, mul_469done
    andi x7, x11, 1
    beq x7, x0, mul_469skip
    add x6, x6, x10
mul_469skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_469loop
mul_469done:
    bge x5, x0, mul_469positive
    sub x6, x0, x6
mul_469positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_470a
    sub x10, x0, x10
mul_470a:
    bge x11, x0, mul_470b
    sub x11, x0, x11
mul_470b:
    addi x6, x0, 0
mul_470loop:
    beq x11, x0, mul_470done
    andi x7, x11, 1
    beq x7, x0, mul_470skip
    add x6, x6, x10
mul_470skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_470loop
mul_470done:
    bge x5, x0, mul_470positive
    sub x6, x0, x6
mul_470positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_471a
    sub x10, x0, x10
mul_471a:
    bge x11, x0, mul_471b
    sub x11, x0, x11
mul_471b:
    addi x6, x0, 0
mul_471loop:
    beq x11, x0, mul_471done
    andi x7, x11, 1
    beq x7, x0, mul_471skip
    add x6, x6, x10
mul_471skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_471loop
mul_471done:
    bge x5, x0, mul_471positive
    sub x6, x0, x6
mul_471positive:
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
    bge x10, x5, clip_472high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_472end
clip_472high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_472end
    lui x10, 0x8
    addi x10, x10, -1
clip_472end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_473high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_473end
clip_473high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_473end
    lui x11, 0x8
    addi x11, x11, -1
clip_473end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_474high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_474end
clip_474high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_474end
    lui x12, 0x8
    addi x12, x12, -1
clip_474end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_475high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_475end
clip_475high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_475end
    lui x13, 0x8
    addi x13, x13, -1
clip_475end:
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
    bge x10, x0, mul_476a
    sub x10, x0, x10
mul_476a:
    bge x11, x0, mul_476b
    sub x11, x0, x11
mul_476b:
    addi x6, x0, 0
mul_476loop:
    beq x11, x0, mul_476done
    andi x7, x11, 1
    beq x7, x0, mul_476skip
    add x6, x6, x10
mul_476skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_476loop
mul_476done:
    bge x5, x0, mul_476positive
    sub x6, x0, x6
mul_476positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_477a
    sub x10, x0, x10
mul_477a:
    bge x11, x0, mul_477b
    sub x11, x0, x11
mul_477b:
    addi x6, x0, 0
mul_477loop:
    beq x11, x0, mul_477done
    andi x7, x11, 1
    beq x7, x0, mul_477skip
    add x6, x6, x10
mul_477skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_477loop
mul_477done:
    bge x5, x0, mul_477positive
    sub x6, x0, x6
mul_477positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_478a
    sub x10, x0, x10
mul_478a:
    bge x11, x0, mul_478b
    sub x11, x0, x11
mul_478b:
    addi x6, x0, 0
mul_478loop:
    beq x11, x0, mul_478done
    andi x7, x11, 1
    beq x7, x0, mul_478skip
    add x6, x6, x10
mul_478skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_478loop
mul_478done:
    bge x5, x0, mul_478positive
    sub x6, x0, x6
mul_478positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_479a
    sub x10, x0, x10
mul_479a:
    bge x11, x0, mul_479b
    sub x11, x0, x11
mul_479b:
    addi x6, x0, 0
mul_479loop:
    beq x11, x0, mul_479done
    andi x7, x11, 1
    beq x7, x0, mul_479skip
    add x6, x6, x10
mul_479skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_479loop
mul_479done:
    bge x5, x0, mul_479positive
    sub x6, x0, x6
mul_479positive:
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
    bge x10, x5, clip_480high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_480end
clip_480high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_480end
    lui x10, 0x8
    addi x10, x10, -1
clip_480end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_481high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_481end
clip_481high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_481end
    lui x11, 0x8
    addi x11, x11, -1
clip_481end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_482high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_482end
clip_482high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_482end
    lui x12, 0x8
    addi x12, x12, -1
clip_482end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_483high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_483end
clip_483high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_483end
    lui x13, 0x8
    addi x13, x13, -1
clip_483end:
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
