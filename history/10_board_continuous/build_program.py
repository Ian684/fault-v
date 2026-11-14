from pathlib import Path
from assembler_support import iword
from program_model import MemoryProgram
root=Path(__file__).resolve().parent
class BoardProgram(MemoryProgram):
    def encode(self, ins, pc):
        if ins[0]=='xori':return iword(ins[3],ins[2],ins[1],f3=4)
        return super().encode(ins,pc)
p=BoardProgram()
p.li(1,0x20000200);p.li(7,0x20000000)
p.li(3,0);p.li(6,10)
p.label('sweep')
p.li(8,0x10000000);p.li(5,4096)
p.label('word')
p.emit('sw',3,8,0);p.emit('lw',4,8,0);p.emit('bne',3,4,'fail')
p.emit('addi',3,3,1);p.emit('addi',8,8,4);p.emit('addi',5,5,-1)
p.emit('bne',5,0,'word')
# Change LEDs only after the complete 16 KiB sweep passed.
p.emit('xori',6,6,15);p.emit('sw',6,1,0)
p.li(10,1);p.emit('sw',10,7,0)
p.li(31,500000)
p.label('delay')
p.emit('addi',31,31,-1);p.emit('bne',31,0,'delay')
p.emit('jal',0,'sweep')
p.label('fail')
p.li(6,15);p.emit('sw',6,1,0);p.li(10,2);p.emit('sw',10,7,0);p.emit('ebreak')
words=[p.encode(ins,k*4) for k,ins in enumerate(p.ops)]
(root/'programs/board_loop.mem').write_text(''.join(f'{w:08x}\n' for w in words+[0]*(4096-len(words))))
labels={offset:name for name,offset in p.labels.items()}
lines=['.section .text','.globl _start','_start:']
for k,(op,*a) in enumerate(p.ops):
    if k*4 in labels:lines.append(labels[k*4]+':')
    if op in ('sw','lw'):text=f'{op} x{a[0]}, {a[2]}(x{a[1]})'
    elif op=='bne':text=f'bne x{a[0]}, x{a[1]}, {a[2]}'
    elif op=='jal':text=f'jal x{a[0]}, {a[1]}'
    elif op=='lui':text=f'lui x{a[0]}, 0x{a[1]:x}'
    elif op in ('addi','xori'):text=f'{op} x{a[0]}, x{a[1]}, {a[2]}'
    else:text=op
    lines.append('    '+text)
(root/'programs/board_loop.S').write_text('\n'.join(lines)+'\n')
print(f'Generated {len(words)} instructions: 4096 words per sweep, LED 5/A on pass, F on failure')
