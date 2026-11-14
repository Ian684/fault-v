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
    bge x10, x0, mul_356a
    sub x10, x0, x10
mul_356a:
    bge x11, x0, mul_356b
    sub x11, x0, x11
mul_356b:
    addi x6, x0, 0
mul_356loop:
    beq x11, x0, mul_356done
    andi x7, x11, 1
    beq x7, x0, mul_356skip
    add x6, x6, x10
mul_356skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_356loop
mul_356done:
    bge x5, x0, mul_356positive
    sub x6, x0, x6
mul_356positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_357a
    sub x10, x0, x10
mul_357a:
    bge x11, x0, mul_357b
    sub x11, x0, x11
mul_357b:
    addi x6, x0, 0
mul_357loop:
    beq x11, x0, mul_357done
    andi x7, x11, 1
    beq x7, x0, mul_357skip
    add x6, x6, x10
mul_357skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_357loop
mul_357done:
    bge x5, x0, mul_357positive
    sub x6, x0, x6
mul_357positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_358a
    sub x10, x0, x10
mul_358a:
    bge x11, x0, mul_358b
    sub x11, x0, x11
mul_358b:
    addi x6, x0, 0
mul_358loop:
    beq x11, x0, mul_358done
    andi x7, x11, 1
    beq x7, x0, mul_358skip
    add x6, x6, x10
mul_358skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_358loop
mul_358done:
    bge x5, x0, mul_358positive
    sub x6, x0, x6
mul_358positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_359a
    sub x10, x0, x10
mul_359a:
    bge x11, x0, mul_359b
    sub x11, x0, x11
mul_359b:
    addi x6, x0, 0
mul_359loop:
    beq x11, x0, mul_359done
    andi x7, x11, 1
    beq x7, x0, mul_359skip
    add x6, x6, x10
mul_359skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_359loop
mul_359done:
    bge x5, x0, mul_359positive
    sub x6, x0, x6
mul_359positive:
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
    bge x10, x5, clip_360high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_360end
clip_360high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_360end
    lui x10, 0x8
    addi x10, x10, -1
clip_360end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_361high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_361end
clip_361high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_361end
    lui x11, 0x8
    addi x11, x11, -1
clip_361end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_362high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_362end
clip_362high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_362end
    lui x12, 0x8
    addi x12, x12, -1
clip_362end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_363high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_363end
clip_363high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_363end
    lui x13, 0x8
    addi x13, x13, -1
clip_363end:
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
    bge x10, x0, mul_364a
    sub x10, x0, x10
mul_364a:
    bge x11, x0, mul_364b
    sub x11, x0, x11
mul_364b:
    addi x6, x0, 0
mul_364loop:
    beq x11, x0, mul_364done
    andi x7, x11, 1
    beq x7, x0, mul_364skip
    add x6, x6, x10
mul_364skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_364loop
mul_364done:
    bge x5, x0, mul_364positive
    sub x6, x0, x6
mul_364positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_365a
    sub x10, x0, x10
mul_365a:
    bge x11, x0, mul_365b
    sub x11, x0, x11
mul_365b:
    addi x6, x0, 0
mul_365loop:
    beq x11, x0, mul_365done
    andi x7, x11, 1
    beq x7, x0, mul_365skip
    add x6, x6, x10
mul_365skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_365loop
mul_365done:
    bge x5, x0, mul_365positive
    sub x6, x0, x6
mul_365positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_366a
    sub x10, x0, x10
mul_366a:
    bge x11, x0, mul_366b
    sub x11, x0, x11
mul_366b:
    addi x6, x0, 0
mul_366loop:
    beq x11, x0, mul_366done
    andi x7, x11, 1
    beq x7, x0, mul_366skip
    add x6, x6, x10
mul_366skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_366loop
mul_366done:
    bge x5, x0, mul_366positive
    sub x6, x0, x6
mul_366positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_367a
    sub x10, x0, x10
mul_367a:
    bge x11, x0, mul_367b
    sub x11, x0, x11
mul_367b:
    addi x6, x0, 0
mul_367loop:
    beq x11, x0, mul_367done
    andi x7, x11, 1
    beq x7, x0, mul_367skip
    add x6, x6, x10
mul_367skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_367loop
mul_367done:
    bge x5, x0, mul_367positive
    sub x6, x0, x6
mul_367positive:
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
    bge x10, x5, clip_368high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_368end
clip_368high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_368end
    lui x10, 0x8
    addi x10, x10, -1
clip_368end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_369high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_369end
clip_369high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_369end
    lui x11, 0x8
    addi x11, x11, -1
clip_369end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_370high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_370end
clip_370high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_370end
    lui x12, 0x8
    addi x12, x12, -1
clip_370end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_371high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_371end
clip_371high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_371end
    lui x13, 0x8
    addi x13, x13, -1
clip_371end:
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
    bge x10, x0, mul_372a
    sub x10, x0, x10
mul_372a:
    bge x11, x0, mul_372b
    sub x11, x0, x11
mul_372b:
    addi x6, x0, 0
mul_372loop:
    beq x11, x0, mul_372done
    andi x7, x11, 1
    beq x7, x0, mul_372skip
    add x6, x6, x10
mul_372skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_372loop
mul_372done:
    bge x5, x0, mul_372positive
    sub x6, x0, x6
mul_372positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_373a
    sub x10, x0, x10
mul_373a:
    bge x11, x0, mul_373b
    sub x11, x0, x11
mul_373b:
    addi x6, x0, 0
mul_373loop:
    beq x11, x0, mul_373done
    andi x7, x11, 1
    beq x7, x0, mul_373skip
    add x6, x6, x10
mul_373skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_373loop
mul_373done:
    bge x5, x0, mul_373positive
    sub x6, x0, x6
mul_373positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_374a
    sub x10, x0, x10
mul_374a:
    bge x11, x0, mul_374b
    sub x11, x0, x11
mul_374b:
    addi x6, x0, 0
mul_374loop:
    beq x11, x0, mul_374done
    andi x7, x11, 1
    beq x7, x0, mul_374skip
    add x6, x6, x10
mul_374skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_374loop
mul_374done:
    bge x5, x0, mul_374positive
    sub x6, x0, x6
mul_374positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_375a
    sub x10, x0, x10
mul_375a:
    bge x11, x0, mul_375b
    sub x11, x0, x11
mul_375b:
    addi x6, x0, 0
mul_375loop:
    beq x11, x0, mul_375done
    andi x7, x11, 1
    beq x7, x0, mul_375skip
    add x6, x6, x10
mul_375skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_375loop
mul_375done:
    bge x5, x0, mul_375positive
    sub x6, x0, x6
mul_375positive:
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
    bge x10, x5, clip_376high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_376end
clip_376high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_376end
    lui x10, 0x8
    addi x10, x10, -1
clip_376end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_377high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_377end
clip_377high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_377end
    lui x11, 0x8
    addi x11, x11, -1
clip_377end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_378high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_378end
clip_378high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_378end
    lui x12, 0x8
    addi x12, x12, -1
clip_378end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_379high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_379end
clip_379high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_379end
    lui x13, 0x8
    addi x13, x13, -1
clip_379end:
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
    bge x10, x0, mul_380a
    sub x10, x0, x10
mul_380a:
    bge x11, x0, mul_380b
    sub x11, x0, x11
mul_380b:
    addi x6, x0, 0
mul_380loop:
    beq x11, x0, mul_380done
    andi x7, x11, 1
    beq x7, x0, mul_380skip
    add x6, x6, x10
mul_380skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_380loop
mul_380done:
    bge x5, x0, mul_380positive
    sub x6, x0, x6
mul_380positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_381a
    sub x10, x0, x10
mul_381a:
    bge x11, x0, mul_381b
    sub x11, x0, x11
mul_381b:
    addi x6, x0, 0
mul_381loop:
    beq x11, x0, mul_381done
    andi x7, x11, 1
    beq x7, x0, mul_381skip
    add x6, x6, x10
mul_381skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_381loop
mul_381done:
    bge x5, x0, mul_381positive
    sub x6, x0, x6
mul_381positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_382a
    sub x10, x0, x10
mul_382a:
    bge x11, x0, mul_382b
    sub x11, x0, x11
mul_382b:
    addi x6, x0, 0
mul_382loop:
    beq x11, x0, mul_382done
    andi x7, x11, 1
    beq x7, x0, mul_382skip
    add x6, x6, x10
mul_382skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_382loop
mul_382done:
    bge x5, x0, mul_382positive
    sub x6, x0, x6
mul_382positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_383a
    sub x10, x0, x10
mul_383a:
    bge x11, x0, mul_383b
    sub x11, x0, x11
mul_383b:
    addi x6, x0, 0
mul_383loop:
    beq x11, x0, mul_383done
    andi x7, x11, 1
    beq x7, x0, mul_383skip
    add x6, x6, x10
mul_383skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_383loop
mul_383done:
    bge x5, x0, mul_383positive
    sub x6, x0, x6
mul_383positive:
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
    bge x10, x5, clip_384high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_384end
clip_384high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_384end
    lui x10, 0x8
    addi x10, x10, -1
clip_384end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_385high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_385end
clip_385high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_385end
    lui x11, 0x8
    addi x11, x11, -1
clip_385end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_386high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_386end
clip_386high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_386end
    lui x12, 0x8
    addi x12, x12, -1
clip_386end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_387high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_387end
clip_387high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_387end
    lui x13, 0x8
    addi x13, x13, -1
clip_387end:
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
