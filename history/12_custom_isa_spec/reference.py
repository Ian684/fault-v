"""Fault-V custom ISA semantic model; no CPU timing model."""
MASK = 0xffffffff
OPS = {'DOT4': 0, 'MUL16': 1, 'ADDSAT': 2, 'QNT8': 3}

def signed(value, width):
    value &= (1 << width) - 1
    return value - (1 << width) if value & (1 << (width - 1)) else value

def clamp(value, lo, hi):
    return min(hi, max(lo, value))

def execute(op, a, b):
    a &= MASK
    b &= MASK
    if op == 'DOT4':
        value = sum(signed(a >> (8*i), 8) * signed(b >> (8*i), 8) for i in range(4))
    elif op == 'MUL16':
        value = signed(a, 16) * signed(b, 16)
    elif op == 'ADDSAT':
        value = clamp(signed(a, 32) + signed(b, 32), -(1 << 31), (1 << 31)-1)
    elif op == 'QNT8':
        value = clamp(signed(a, 32) >> (b & 31), -128, 127)
    else:
        raise ValueError('Unsupported custom operation')
    return value & MASK

def encode(op, rd, rs1, rs2):
    if op not in OPS or any(not isinstance(r, int) or not 0 <= r < 32 for r in (rd, rs1, rs2)):
        raise ValueError('Invalid operation or register')
    return (rs2 << 20) | (rs1 << 15) | (OPS[op] << 12) | (rd << 7) | 0x0b

def decode(inst):
    if not isinstance(inst, int) or not 0 <= inst <= MASK:
        raise ValueError('Instruction must be a 32-bit word')
    function = (inst >> 12) & 7
    if inst & 0x7f != 0x0b or inst >> 25 != 0 or function not in OPS.values():
        raise ValueError('Illegal custom encoding')
    op = next(name for name, code in OPS.items() if code == function)
    return op, (inst >> 7) & 31, (inst >> 15) & 31, (inst >> 20) & 31

def step(inst, regs):
    """One semantic commit, with both sources sampled before destination write."""
    op, rd, rs1, rs2 = decode(inst)
    a = 0 if rs1 == 0 else regs[rs1]
    b = 0 if rs2 == 0 else regs[rs2]
    value = execute(op, a, b)
    if rd != 0:
        regs[rd] = value
    regs[0] = 0
    return value

def pack8(values):
    if len(values) != 4 or any(not -128 <= x <= 127 for x in values):
        raise ValueError('Four signed INT8 values required')
    return sum((x & 255) << (8*i) for i, x in enumerate(values))

def soft_multiply(a, b, width):
    """Mathematical shift/add baseline, not an executed RV32I assembly program."""
    a, b = signed(a, width), signed(b, width)
    negative = (a < 0) != (b < 0)
    a, b = abs(a), abs(b)
    total = 0
    for _ in range(width):
        if b & 1:
            total += a
        a <<= 1
        b >>= 1
    return -total if negative else total
