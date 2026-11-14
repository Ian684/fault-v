from pathlib import Path
import json
import copy
from program_model import MemoryProgram,BASE,MMIO
root=Path(__file__).resolve().parent
p=MemoryProgram()
p.li(2,BASE+16384);p.li(8,BASE);p.emit('addi',9,8,0)
p.li(10,0);p.li(11,1);p.li(12,10)
p.label('fib_loop');p.emit('sw',10,9,0);p.emit('add',13,10,11);p.emit('addi',10,11,0)
p.emit('addi',11,13,0);p.emit('addi',9,9,4);p.emit('addi',12,12,-1);p.emit('bne',12,0,'fib_loop')
p.emit('jal',1,'sum_fib');p.li(17,176);p.emit('bne',10,17,'fail1');p.emit('sw',10,8,64)
p.li(18,0x89abcdef);p.emit('sw',18,8,48)
for op,off,value in [('lb',51,-119),('lbu',51,137),('lh',50,-30293),('lhu',50,35243)]:
    p.emit(op,19,8,off);p.li(20,value);p.emit('bne',19,20,'fail2')
p.emit('sb',0,8,49);p.li(21,0x1234);p.emit('sh',21,8,50);p.emit('lw',22,8,48)
p.li(23,0x123400ef);p.emit('bne',22,23,'fail3');p.emit('fence')
p.li(24,MMIO);p.li(25,1);p.emit('sw',25,24,0);p.emit('lw',26,24,0);p.emit('bne',26,25,'fail4');p.emit('ebreak')
p.label('sum_fib');p.emit('addi',2,2,-4);p.emit('sw',1,2,0);p.li(10,0);p.emit('addi',14,8,0);p.li(15,10)
p.label('sum_loop');p.emit('lw',16,14,0);p.emit('add',10,10,16);p.emit('addi',14,14,4);p.emit('addi',15,15,-1)
p.emit('bne',15,0,'sum_loop');p.emit('jal',1,'double');p.emit('lw',1,2,0);p.emit('addi',2,2,4);p.emit('jalr',0,1,0)
p.label('double');p.emit('add',10,10,10);p.emit('jalr',0,1,0)
for i in range(1,5):
    p.label(f'fail{i}');p.li(24,MMIO);p.li(25,i+1);p.emit('sw',25,24,0);p.emit('ebreak')
programs=[]
def save(name,p):
    words,trace,regs,mem,tx,stop=p.run()
    status=sum(mem[16384+k]<<(8*k) for k in range(4))
    programs.append(dict(name=name,words=words,trace=trace,regs=regs,ram=[sum(mem[j+k]<<(8*k) for k in range(4)) for j in range(0,16384,4)],
                         tx=tx,stop=stop,status=status,labels=p.labels,ops=p.ops))
    (root/f'programs/{name}.mem').write_text('\n'.join(f'{w:08x}' for w in words+[0]*(4096-len(words)))+'\n')
save('integration',p)
assert programs[0]['status']==1 and programs[0]['regs'][10]==176
assert programs[0]['ram'][:10]==[0,1,1,2,3,5,8,13,21,34]
q=MemoryProgram();q.li(1,5);q.emit('raw',0xffffffff);save('illegal',q)
q=MemoryProgram();q.li(1,BASE);q.emit('lw',2,1,1);save('misaligned',q)
q=MemoryProgram();q.li(1,BASE+16384);q.emit('sw',0,1,0);save('unmapped_store',q)
q=MemoryProgram();q.li(1,0x4000);q.emit('jalr',5,1,0);save('fetch_error',q)
q=MemoryProgram();q.li(1,MMIO+4);q.emit('lw',2,1,0);save('unmapped_mmio',q)
q=copy.deepcopy(p)
q.ops=[('addi',17,0,177) if ins==('addi',17,0,176) else ins for ins in q.ops]
save('software_fail',q)
assert programs[-1]['status']==2
# Independent byte-model ends unavailable MMIO at its configured mapping boundary.

def assembly(prog):
    labels={v:k for k,v in prog['labels'].items()};out=['.section .text','.globl _start','_start:']
    for idx,ins in enumerate(prog['ops']):
        if idx*4 in labels:out.append(labels[idx*4]+':')
        op,*a=ins
        if op in ['lb','lbu','lh','lhu','lw','sb','sh','sw','jalr']:s=f'{op} x{a[0]},{a[2]}(x{a[1]})'
        elif op in ['bne','beq','blt','bge','bltu','bgeu']:s=f'{op} x{a[0]},x{a[1]},{a[2]}'
        elif op=='jal':s=f'jal x{a[0]},{a[1]}'
        elif op=='addi':s=f'addi x{a[0]},x{a[1]},{a[2]}'
        elif op=='add':s=f'add x{a[0]},x{a[1]},x{a[2]}'
        elif op=='lui':s=f'lui x{a[0]},0x{a[1]:x}'
        elif op=='raw':s=f'.word 0x{a[0]:08x}'
        elif op=='fence':s='fence iorw,iorw'
        else:s=op
        out.append('    '+s)
    return '\n'.join(out)+'\n'
for prog in programs:(root/f'programs/{prog["name"]}.S').write_text(assembly(prog))
(root/'program_specs.json').write_text(json.dumps(programs,indent=2))
lines=['case(id)']
for k,c in enumerate(programs):
    cause,pc,addr=c['stop'];lines.append(f'{k}: begin expected_count={len(c["trace"])}; expected_data_count={len(c["tx"])};')
    lines.append(f"expected_cause=halt_cause_t'({cause}); expected_fault_pc=32'h{pc:08x}; expected_fault_addr=32'h{addr:08x}; expected_status=32'h{c['status']:08x};")
    for j,(pc,w,rd,v,nxt) in enumerate(c['trace']):lines.append(f"gold_pc[{j}]=32'h{pc:08x}; gold_inst[{j}]=32'h{w:08x}; gold_rd[{j}]=5'd{rd}; gold_data[{j}]=32'h{v:08x}; gold_next[{j}]=32'h{nxt:08x};")
    for j,v in enumerate(c['regs']):lines.append(f"gold_regs[{j}]=32'h{v:08x};")
    for j,v in enumerate(c['ram']):
        if v:lines.append(f"gold_ram[{j}]=32'h{v:08x};")
    lines.append('end')
lines+=['default: $fatal(1,"bad program id");','endcase']
(root/'verify/program_expectations.svh').write_text('\n'.join(lines)+'\n')
print([(c['name'],len(c['trace']),len(c['tx']),c['stop'],c['status']) for c in programs])
