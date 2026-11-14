from pathlib import Path
from assembler_support import iword
from program_model import MemoryProgram
root=Path(__file__).resolve().parent
class PeripheralProgram(MemoryProgram):
    def encode(self,ins,pc):
        if ins[0]=='andi':return iword(ins[3],ins[2],ins[1],f3=7)
        return super().encode(ins,pc)
p=PeripheralProgram()
p.li(1,0x20000100);p.li(2,0x20000200);p.li(7,0x20000000);p.li(8,0x10000000)
p.li(3,5);p.emit('sw',3,2,0);p.emit('lw',4,2,0);p.emit('bne',3,4,'fail')
p.emit('lw',9,2,4);p.emit('sw',9,8,0)
for k,byte in enumerate(b'Fault-V OK\r\n'):
    p.li(10,byte);p.label(f'wait_{k}');p.emit('lw',11,1,4)
    p.emit('andi',11,11,1);p.emit('beq',11,0,f'wait_{k}');p.emit('sw',10,1,0)
p.label('drain');p.emit('lw',11,1,4);p.emit('andi',11,11,1);p.emit('beq',11,0,'drain')
p.li(3,5);p.emit('sw',3,2,0);p.li(3,1);p.emit('sw',3,7,0);p.emit('ebreak')
p.label('fail');p.li(3,15);p.emit('sw',3,2,0);p.li(3,2);p.emit('sw',3,7,0);p.emit('ebreak')
words=[p.encode(ins,k*4) for k,ins in enumerate(p.ops)]
(root/'programs/peripheral_demo.mem').write_text(''.join(f'{w:08x}\n' for w in words+[0]*(4096-len(words))))
labels={v:k for k,v in p.labels.items()};lines=['.section .text','.globl _start','_start:']
for k,ins in enumerate(p.ops):
    if k*4 in labels:lines.append(labels[k*4]+':')
    op,*a=ins
    if op in ('lw','sw'):s=f'{op} x{a[0]},{a[2]}(x{a[1]})'
    elif op in ('beq','bne'):s=f'{op} x{a[0]},x{a[1]},{a[2]}'
    elif op=='lui':s=f'lui x{a[0]},0x{a[1]:x}'
    elif op in ('addi','andi'):s=f'{op} x{a[0]},x{a[1]},{a[2]}'
    else:s=op
    lines.append('    '+s)
(root/'programs/peripheral_demo.S').write_text('\n'.join(lines)+'\n')
print(f'Generated {len(words)} words; output: Fault-V OK\\r\\n, final LED=0xA, status=1')
faults=[(0x100,False,2),(0x104,True,2),(0x204,True,2),(0x108,False,2),
        (0x100,True,0),(0x101,False,2),(0x204,False,1),(0x205,True,1)]
for n,(offset,write,f3) in enumerate(faults):
    inst=(1<<15)|(f3<<12)|0x23 if write else iword(0,1,2,op=3,f3=f3)
    image=[(0x20000<<12)|(1<<7)|0x37,iword(offset,1,1),inst,0x00100073]
    (root/f'programs/io_fault_{n}.mem').write_text(''.join(f'{w:08x}\n' for w in image+[0]*(4096-len(image))))
