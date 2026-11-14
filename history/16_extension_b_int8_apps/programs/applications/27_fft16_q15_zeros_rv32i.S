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
    bge x10, x0, mul_212a
    sub x10, x0, x10
mul_212a:
    bge x11, x0, mul_212b
    sub x11, x0, x11
mul_212b:
    addi x6, x0, 0
mul_212loop:
    beq x11, x0, mul_212done
    andi x7, x11, 1
    beq x7, x0, mul_212skip
    add x6, x6, x10
mul_212skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_212loop
mul_212done:
    bge x5, x0, mul_212positive
    sub x6, x0, x6
mul_212positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_213a
    sub x10, x0, x10
mul_213a:
    bge x11, x0, mul_213b
    sub x11, x0, x11
mul_213b:
    addi x6, x0, 0
mul_213loop:
    beq x11, x0, mul_213done
    andi x7, x11, 1
    beq x7, x0, mul_213skip
    add x6, x6, x10
mul_213skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_213loop
mul_213done:
    bge x5, x0, mul_213positive
    sub x6, x0, x6
mul_213positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_214a
    sub x10, x0, x10
mul_214a:
    bge x11, x0, mul_214b
    sub x11, x0, x11
mul_214b:
    addi x6, x0, 0
mul_214loop:
    beq x11, x0, mul_214done
    andi x7, x11, 1
    beq x7, x0, mul_214skip
    add x6, x6, x10
mul_214skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_214loop
mul_214done:
    bge x5, x0, mul_214positive
    sub x6, x0, x6
mul_214positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_215a
    sub x10, x0, x10
mul_215a:
    bge x11, x0, mul_215b
    sub x11, x0, x11
mul_215b:
    addi x6, x0, 0
mul_215loop:
    beq x11, x0, mul_215done
    andi x7, x11, 1
    beq x7, x0, mul_215skip
    add x6, x6, x10
mul_215skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_215loop
mul_215done:
    bge x5, x0, mul_215positive
    sub x6, x0, x6
mul_215positive:
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
    bge x10, x5, clip_216high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_216end
clip_216high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_216end
    lui x10, 0x8
    addi x10, x10, -1
clip_216end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_217high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_217end
clip_217high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_217end
    lui x11, 0x8
    addi x11, x11, -1
clip_217end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_218high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_218end
clip_218high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_218end
    lui x12, 0x8
    addi x12, x12, -1
clip_218end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_219high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_219end
clip_219high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_219end
    lui x13, 0x8
    addi x13, x13, -1
clip_219end:
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
    bge x10, x0, mul_220a
    sub x10, x0, x10
mul_220a:
    bge x11, x0, mul_220b
    sub x11, x0, x11
mul_220b:
    addi x6, x0, 0
mul_220loop:
    beq x11, x0, mul_220done
    andi x7, x11, 1
    beq x7, x0, mul_220skip
    add x6, x6, x10
mul_220skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_220loop
mul_220done:
    bge x5, x0, mul_220positive
    sub x6, x0, x6
mul_220positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_221a
    sub x10, x0, x10
mul_221a:
    bge x11, x0, mul_221b
    sub x11, x0, x11
mul_221b:
    addi x6, x0, 0
mul_221loop:
    beq x11, x0, mul_221done
    andi x7, x11, 1
    beq x7, x0, mul_221skip
    add x6, x6, x10
mul_221skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_221loop
mul_221done:
    bge x5, x0, mul_221positive
    sub x6, x0, x6
mul_221positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_222a
    sub x10, x0, x10
mul_222a:
    bge x11, x0, mul_222b
    sub x11, x0, x11
mul_222b:
    addi x6, x0, 0
mul_222loop:
    beq x11, x0, mul_222done
    andi x7, x11, 1
    beq x7, x0, mul_222skip
    add x6, x6, x10
mul_222skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_222loop
mul_222done:
    bge x5, x0, mul_222positive
    sub x6, x0, x6
mul_222positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_223a
    sub x10, x0, x10
mul_223a:
    bge x11, x0, mul_223b
    sub x11, x0, x11
mul_223b:
    addi x6, x0, 0
mul_223loop:
    beq x11, x0, mul_223done
    andi x7, x11, 1
    beq x7, x0, mul_223skip
    add x6, x6, x10
mul_223skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_223loop
mul_223done:
    bge x5, x0, mul_223positive
    sub x6, x0, x6
mul_223positive:
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
    bge x10, x5, clip_224high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_224end
clip_224high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_224end
    lui x10, 0x8
    addi x10, x10, -1
clip_224end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_225high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_225end
clip_225high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_225end
    lui x11, 0x8
    addi x11, x11, -1
clip_225end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_226high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_226end
clip_226high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_226end
    lui x12, 0x8
    addi x12, x12, -1
clip_226end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_227high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_227end
clip_227high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_227end
    lui x13, 0x8
    addi x13, x13, -1
clip_227end:
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
    bge x10, x0, mul_228a
    sub x10, x0, x10
mul_228a:
    bge x11, x0, mul_228b
    sub x11, x0, x11
mul_228b:
    addi x6, x0, 0
mul_228loop:
    beq x11, x0, mul_228done
    andi x7, x11, 1
    beq x7, x0, mul_228skip
    add x6, x6, x10
mul_228skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_228loop
mul_228done:
    bge x5, x0, mul_228positive
    sub x6, x0, x6
mul_228positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_229a
    sub x10, x0, x10
mul_229a:
    bge x11, x0, mul_229b
    sub x11, x0, x11
mul_229b:
    addi x6, x0, 0
mul_229loop:
    beq x11, x0, mul_229done
    andi x7, x11, 1
    beq x7, x0, mul_229skip
    add x6, x6, x10
mul_229skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_229loop
mul_229done:
    bge x5, x0, mul_229positive
    sub x6, x0, x6
mul_229positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_230a
    sub x10, x0, x10
mul_230a:
    bge x11, x0, mul_230b
    sub x11, x0, x11
mul_230b:
    addi x6, x0, 0
mul_230loop:
    beq x11, x0, mul_230done
    andi x7, x11, 1
    beq x7, x0, mul_230skip
    add x6, x6, x10
mul_230skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_230loop
mul_230done:
    bge x5, x0, mul_230positive
    sub x6, x0, x6
mul_230positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_231a
    sub x10, x0, x10
mul_231a:
    bge x11, x0, mul_231b
    sub x11, x0, x11
mul_231b:
    addi x6, x0, 0
mul_231loop:
    beq x11, x0, mul_231done
    andi x7, x11, 1
    beq x7, x0, mul_231skip
    add x6, x6, x10
mul_231skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_231loop
mul_231done:
    bge x5, x0, mul_231positive
    sub x6, x0, x6
mul_231positive:
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
    bge x10, x5, clip_232high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_232end
clip_232high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_232end
    lui x10, 0x8
    addi x10, x10, -1
clip_232end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_233high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_233end
clip_233high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_233end
    lui x11, 0x8
    addi x11, x11, -1
clip_233end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_234high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_234end
clip_234high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_234end
    lui x12, 0x8
    addi x12, x12, -1
clip_234end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_235high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_235end
clip_235high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_235end
    lui x13, 0x8
    addi x13, x13, -1
clip_235end:
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
    bge x10, x0, mul_236a
    sub x10, x0, x10
mul_236a:
    bge x11, x0, mul_236b
    sub x11, x0, x11
mul_236b:
    addi x6, x0, 0
mul_236loop:
    beq x11, x0, mul_236done
    andi x7, x11, 1
    beq x7, x0, mul_236skip
    add x6, x6, x10
mul_236skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_236loop
mul_236done:
    bge x5, x0, mul_236positive
    sub x6, x0, x6
mul_236positive:
    addi x10, x6, 0
    addi x28, x10, 0
    addi x10, x25, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_237a
    sub x10, x0, x10
mul_237a:
    bge x11, x0, mul_237b
    sub x11, x0, x11
mul_237b:
    addi x6, x0, 0
mul_237loop:
    beq x11, x0, mul_237done
    andi x7, x11, 1
    beq x7, x0, mul_237skip
    add x6, x6, x10
mul_237skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_237loop
mul_237done:
    bge x5, x0, mul_237positive
    sub x6, x0, x6
mul_237positive:
    addi x10, x6, 0
    sub x28, x28, x10
    srai x28, x28, 15
    addi x10, x24, 0
    addi x11, x9, 0
    xor x5, x10, x11
    bge x10, x0, mul_238a
    sub x10, x0, x10
mul_238a:
    bge x11, x0, mul_238b
    sub x11, x0, x11
mul_238b:
    addi x6, x0, 0
mul_238loop:
    beq x11, x0, mul_238done
    andi x7, x11, 1
    beq x7, x0, mul_238skip
    add x6, x6, x10
mul_238skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_238loop
mul_238done:
    bge x5, x0, mul_238positive
    sub x6, x0, x6
mul_238positive:
    addi x10, x6, 0
    addi x29, x10, 0
    addi x10, x25, 0
    addi x11, x8, 0
    xor x5, x10, x11
    bge x10, x0, mul_239a
    sub x10, x0, x10
mul_239a:
    bge x11, x0, mul_239b
    sub x11, x0, x11
mul_239b:
    addi x6, x0, 0
mul_239loop:
    beq x11, x0, mul_239done
    andi x7, x11, 1
    beq x7, x0, mul_239skip
    add x6, x6, x10
mul_239skip:
    slli x10, x10, 1
    srli x11, x11, 1
    jal x0, mul_239loop
mul_239done:
    bge x5, x0, mul_239positive
    sub x6, x0, x6
mul_239positive:
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
    bge x10, x5, clip_240high
    lui x10, 0xffff8
    addi x10, x10, 0
    jal x0, clip_240end
clip_240high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x10, clip_240end
    lui x10, 0x8
    addi x10, x10, -1
clip_240end:
    srai x11, x11, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x11, x5, clip_241high
    lui x11, 0xffff8
    addi x11, x11, 0
    jal x0, clip_241end
clip_241high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x11, clip_241end
    lui x11, 0x8
    addi x11, x11, -1
clip_241end:
    srai x12, x12, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x12, x5, clip_242high
    lui x12, 0xffff8
    addi x12, x12, 0
    jal x0, clip_242end
clip_242high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x12, clip_242end
    lui x12, 0x8
    addi x12, x12, -1
clip_242end:
    srai x13, x13, 1
    lui x5, 0xffff8
    addi x5, x5, 0
    bge x13, x5, clip_243high
    lui x13, 0xffff8
    addi x13, x13, 0
    jal x0, clip_243end
clip_243high:
    lui x5, 0x8
    addi x5, x5, -1
    bge x5, x13, clip_243end
    lui x13, 0x8
    addi x13, x13, -1
clip_243end:
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
