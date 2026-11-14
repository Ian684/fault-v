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
    bge x10, x0, mul_260a
    sub x10, x0, x10
mul_260a:
    bge x11, x0, mul_260b
    sub x11, x0, x11
mul_260b:
    addi x6, x0, 0
mul_260loop:
    beq x11, x0, mul_260done
    andi x7, x11, 1
    beq x7, x0, mul_260skip
    add x6, x6, x10
mul_260skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_260loop
mul_260done:
    bge x5, x0, mul_260positive
    sub x6, x0, x6
mul_260positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_261a
    sub x10, x0, x10
mul_261a:
    bge x11, x0, mul_261b
    sub x11, x0, x11
mul_261b:
    addi x6, x0, 0
mul_261loop:
    beq x11, x0, mul_261done
    andi x7, x11, 1
    beq x7, x0, mul_261skip
    add x6, x6, x10
mul_261skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_261loop
mul_261done:
    bge x5, x0, mul_261positive
    sub x6, x0, x6
mul_261positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_262a
    sub x10, x0, x10
mul_262a:
    bge x11, x0, mul_262b
    sub x11, x0, x11
mul_262b:
    addi x6, x0, 0
mul_262loop:
    beq x11, x0, mul_262done
    andi x7, x11, 1
    beq x7, x0, mul_262skip
    add x6, x6, x10
mul_262skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_262loop
mul_262done:
    bge x5, x0, mul_262positive
    sub x6, x0, x6
mul_262positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_263a
    sub x10, x0, x10
mul_263a:
    bge x11, x0, mul_263b
    sub x11, x0, x11
mul_263b:
    addi x6, x0, 0
mul_263loop:
    beq x11, x0, mul_263done
    andi x7, x11, 1
    beq x7, x0, mul_263skip
    add x6, x6, x10
mul_263skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_263loop
mul_263done:
    bge x5, x0, mul_263positive
    sub x6, x0, x6
mul_263positive:
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
    bge x10, x5, clip_264high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_264end
clip_264high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_264end
    lui x10, 0x8
    addi x10, x10, -1
clip_264end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_265high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_265end
clip_265high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_265end
    lui x11, 0x8
    addi x11, x11, -1
clip_265end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_266high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_266end
clip_266high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_266end
    lui x12, 0x8
    addi x12, x12, -1
clip_266end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_267high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_267end
clip_267high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_267end
    lui x13, 0x8
    addi x13, x13, -1
clip_267end:
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
    bge x10, x0, mul_268a
    sub x10, x0, x10
mul_268a:
    bge x11, x0, mul_268b
    sub x11, x0, x11
mul_268b:
    addi x6, x0, 0
mul_268loop:
    beq x11, x0, mul_268done
    andi x7, x11, 1
    beq x7, x0, mul_268skip
    add x6, x6, x10
mul_268skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_268loop
mul_268done:
    bge x5, x0, mul_268positive
    sub x6, x0, x6
mul_268positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_269a
    sub x10, x0, x10
mul_269a:
    bge x11, x0, mul_269b
    sub x11, x0, x11
mul_269b:
    addi x6, x0, 0
mul_269loop:
    beq x11, x0, mul_269done
    andi x7, x11, 1
    beq x7, x0, mul_269skip
    add x6, x6, x10
mul_269skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_269loop
mul_269done:
    bge x5, x0, mul_269positive
    sub x6, x0, x6
mul_269positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_270a
    sub x10, x0, x10
mul_270a:
    bge x11, x0, mul_270b
    sub x11, x0, x11
mul_270b:
    addi x6, x0, 0
mul_270loop:
    beq x11, x0, mul_270done
    andi x7, x11, 1
    beq x7, x0, mul_270skip
    add x6, x6, x10
mul_270skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_270loop
mul_270done:
    bge x5, x0, mul_270positive
    sub x6, x0, x6
mul_270positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_271a
    sub x10, x0, x10
mul_271a:
    bge x11, x0, mul_271b
    sub x11, x0, x11
mul_271b:
    addi x6, x0, 0
mul_271loop:
    beq x11, x0, mul_271done
    andi x7, x11, 1
    beq x7, x0, mul_271skip
    add x6, x6, x10
mul_271skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_271loop
mul_271done:
    bge x5, x0, mul_271positive
    sub x6, x0, x6
mul_271positive:
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
    bge x10, x5, clip_272high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_272end
clip_272high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_272end
    lui x10, 0x8
    addi x10, x10, -1
clip_272end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_273high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_273end
clip_273high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_273end
    lui x11, 0x8
    addi x11, x11, -1
clip_273end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_274high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_274end
clip_274high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_274end
    lui x12, 0x8
    addi x12, x12, -1
clip_274end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_275high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_275end
clip_275high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_275end
    lui x13, 0x8
    addi x13, x13, -1
clip_275end:
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
    bge x10, x0, mul_276a
    sub x10, x0, x10
mul_276a:
    bge x11, x0, mul_276b
    sub x11, x0, x11
mul_276b:
    addi x6, x0, 0
mul_276loop:
    beq x11, x0, mul_276done
    andi x7, x11, 1
    beq x7, x0, mul_276skip
    add x6, x6, x10
mul_276skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_276loop
mul_276done:
    bge x5, x0, mul_276positive
    sub x6, x0, x6
mul_276positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_277a
    sub x10, x0, x10
mul_277a:
    bge x11, x0, mul_277b
    sub x11, x0, x11
mul_277b:
    addi x6, x0, 0
mul_277loop:
    beq x11, x0, mul_277done
    andi x7, x11, 1
    beq x7, x0, mul_277skip
    add x6, x6, x10
mul_277skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_277loop
mul_277done:
    bge x5, x0, mul_277positive
    sub x6, x0, x6
mul_277positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_278a
    sub x10, x0, x10
mul_278a:
    bge x11, x0, mul_278b
    sub x11, x0, x11
mul_278b:
    addi x6, x0, 0
mul_278loop:
    beq x11, x0, mul_278done
    andi x7, x11, 1
    beq x7, x0, mul_278skip
    add x6, x6, x10
mul_278skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_278loop
mul_278done:
    bge x5, x0, mul_278positive
    sub x6, x0, x6
mul_278positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_279a
    sub x10, x0, x10
mul_279a:
    bge x11, x0, mul_279b
    sub x11, x0, x11
mul_279b:
    addi x6, x0, 0
mul_279loop:
    beq x11, x0, mul_279done
    andi x7, x11, 1
    beq x7, x0, mul_279skip
    add x6, x6, x10
mul_279skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_279loop
mul_279done:
    bge x5, x0, mul_279positive
    sub x6, x0, x6
mul_279positive:
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
    bge x10, x5, clip_280high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_280end
clip_280high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_280end
    lui x10, 0x8
    addi x10, x10, -1
clip_280end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_281high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_281end
clip_281high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_281end
    lui x11, 0x8
    addi x11, x11, -1
clip_281end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_282high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_282end
clip_282high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_282end
    lui x12, 0x8
    addi x12, x12, -1
clip_282end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_283high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_283end
clip_283high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_283end
    lui x13, 0x8
    addi x13, x13, -1
clip_283end:
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
    bge x10, x0, mul_284a
    sub x10, x0, x10
mul_284a:
    bge x11, x0, mul_284b
    sub x11, x0, x11
mul_284b:
    addi x6, x0, 0
mul_284loop:
    beq x11, x0, mul_284done
    andi x7, x11, 1
    beq x7, x0, mul_284skip
    add x6, x6, x10
mul_284skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_284loop
mul_284done:
    bge x5, x0, mul_284positive
    sub x6, x0, x6
mul_284positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_285a
    sub x10, x0, x10
mul_285a:
    bge x11, x0, mul_285b
    sub x11, x0, x11
mul_285b:
    addi x6, x0, 0
mul_285loop:
    beq x11, x0, mul_285done
    andi x7, x11, 1
    beq x7, x0, mul_285skip
    add x6, x6, x10
mul_285skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_285loop
mul_285done:
    bge x5, x0, mul_285positive
    sub x6, x0, x6
mul_285positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_286a
    sub x10, x0, x10
mul_286a:
    bge x11, x0, mul_286b
    sub x11, x0, x11
mul_286b:
    addi x6, x0, 0
mul_286loop:
    beq x11, x0, mul_286done
    andi x7, x11, 1
    beq x7, x0, mul_286skip
    add x6, x6, x10
mul_286skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_286loop
mul_286done:
    bge x5, x0, mul_286positive
    sub x6, x0, x6
mul_286positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_287a
    sub x10, x0, x10
mul_287a:
    bge x11, x0, mul_287b
    sub x11, x0, x11
mul_287b:
    addi x6, x0, 0
mul_287loop:
    beq x11, x0, mul_287done
    andi x7, x11, 1
    beq x7, x0, mul_287skip
    add x6, x6, x10
mul_287skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_287loop
mul_287done:
    bge x5, x0, mul_287positive
    sub x6, x0, x6
mul_287positive:
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
    bge x10, x5, clip_288high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_288end
clip_288high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_288end
    lui x10, 0x8
    addi x10, x10, -1
clip_288end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_289high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_289end
clip_289high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_289end
    lui x11, 0x8
    addi x11, x11, -1
clip_289end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_290high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_290end
clip_290high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_290end
    lui x12, 0x8
    addi x12, x12, -1
clip_290end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_291high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_291end
clip_291high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_291end
    lui x13, 0x8
    addi x13, x13, -1
clip_291end:
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
