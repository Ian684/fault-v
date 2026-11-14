"""Generate an independent stress image; leave peripheral_demo unchanged."""
from pathlib import Path
from assembler_support import iword
from program_model import MemoryProgram

ROOT = Path(__file__).resolve().parent
class StressProgram(MemoryProgram):
    def encode(self, ins, pc):
        if ins[0] == 'andi':
            return iword(ins[3], ins[2], ins[1], f3=7)
        return super().encode(ins, pc)

p = StressProgram()
for reg, value in [(1, 0x20000100), (2, 0x20000200),
                   (7, 0x20000000), (8, 0x10000000), (5, 1024)]:
    p.li(reg, value)
p.li(3, 0)
p.label('loop')
p.emit('sw', 3, 8, 0)
p.emit('lw', 4, 8, 0)
p.emit('bne', 3, 4, 'fail')
p.emit('andi', 6, 3, 255)
p.emit('sb', 3, 8, 4)
p.emit('lbu', 4, 8, 4)
p.emit('bne', 6, 4, 'fail')
p.emit('sh', 3, 8, 6)
p.emit('lhu', 4, 8, 6)
p.emit('bne', 3, 4, 'fail')
p.emit('sw', 3, 2, 0)
p.emit('lw', 4, 2, 0)
p.emit('andi', 6, 3, 15)
p.emit('bne', 6, 4, 'fail')
p.emit('lw', 4, 2, 4)
p.li(6, 3)
p.emit('bne', 6, 4, 'fail')
# Intentionally do not poll before writes: exercise UART backpressure.
p.emit('sw', 3, 1, 0)
p.emit('addi', 3, 3, 1)
p.emit('bne', 3, 5, 'loop')
p.label('drain')
p.emit('lw', 4, 1, 4)
p.emit('andi', 4, 4, 1)
p.emit('beq', 4, 0, 'drain')
p.li(3, 1)
p.emit('sw', 3, 7, 0)
p.emit('ebreak')
p.label('fail')
p.li(3, 2)
p.emit('sw', 3, 7, 0)
p.emit('ebreak')
words = [p.encode(ins, k * 4) for k, ins in enumerate(p.ops)]
(ROOT / 'programs/stress.mem').write_text(
    ''.join(f'{word:08x}\n' for word in words + [0] * (4096-len(words))))
labels = {offset: name for name, offset in p.labels.items()}
lines = ['.section .text', '.globl _start', '_start:']
for k, (op, *a) in enumerate(p.ops):
    if k * 4 in labels:
        lines.append(labels[k * 4] + ':')
    if op in ('lw', 'sw', 'sb', 'lbu', 'sh', 'lhu'):
        text = f'{op} x{a[0]}, {a[2]}(x{a[1]})'
    elif op in ('beq', 'bne'):
        text = f'{op} x{a[0]}, x{a[1]}, {a[2]}'
    elif op == 'lui':
        text = f'lui x{a[0]}, 0x{a[1]:x}'
    elif op in ('addi', 'andi'):
        text = f'{op} x{a[0]}, x{a[1]}, {a[2]}'
    else:
        text = op
    lines.append('    ' + text)
(ROOT / 'programs/stress.S').write_text('\n'.join(lines) + '\n')
print(f'Generated {len(words)} words: 1024 iterations, UART bytes 00..FF repeated four times')
