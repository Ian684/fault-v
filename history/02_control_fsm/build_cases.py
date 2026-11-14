from pathlib import Path
import json
root=Path(__file__).resolve().parent
previous=json.loads((root.parent/'week5/test_spec.json').read_text(encoding='utf-8'))
cases=[]
def add(n,inst,av=0,bv=0,wr=0,wb=0,pc=4,cause='HALT_NONE',fault=0,requests=0,err=0,bus=0,store=0,mask=0):
    cases.append([n,inst,av,bv,wr,wb,pc,cause,fault,requests,err,bus,store,mask])
alu_examples={x[0].split()[0]:x for x in previous['integration'][:21]}
branches={'BEQ':(5,5),'BNE':(5,6),'BLT':(0xffffffff,1),'BGE':(5,5),'BLTU':(0,0xffffffff),'BGEU':(0xffffffff,0)}
for n,inst,cl,*rest in previous['decoder']:
    if cl==1:
        ex=alu_examples[n]
        value=ex[-1]
        if n=='AUIPC':value=0x12345000
        add(n,inst,ex[2],ex[3],1,value)
    elif cl==4:
        av,bv=branches[n];add(n+' taken',inst,av,bv,pc=0xfffffffc)
    elif cl==5:add(n,inst,wr=1,wb=4,pc=0xfffffffc)
    elif cl==6:add(n,inst,av=0x200,wr=1,wb=4,pc=0x1fc)
    elif cl==2:
        value={'LB':1,'LH':0x7f01,'LW':0x80ff7f01,'LBU':1,'LHU':0x7f01}[n]
        add(n,inst,av=0x10000004,wr=1,wb=value,requests=1,bus=0x10000000)
    elif cl==3:
        mask={'SB':1,'SH':3,'SW':15}[n]
        add(n,inst,av=0x10000004,bv=0xa1b2c3d4,requests=1,bus=0x10000000,store=0xa1b2c3d4,mask=mask)
    elif cl==7:add(n,inst)
    elif cl==8:add(n,inst,pc=0,cause='HALT_ECALL')
    elif cl==9:add(n,inst,pc=0,cause='HALT_EBREAK')
false_values={'BEQ':(5,6),'BNE':(5,5),'BLT':(1,0xffffffff),'BGE':(0xffffffff,1),'BLTU':(0xffffffff,0),'BGEU':(0,0xffffffff)}
for n,inst,cl,*rest in previous['decoder']:
    if cl==4:add(n+' not taken',inst,*false_values[n])
add('untaken misaligned branch',0x00730163,5,6)
add('taken misaligned branch',0x00730163,5,5,pc=0,cause='HALT_INSTR_ALIGN',fault=2)
add('misaligned JAL',0x002002ef,pc=0,cause='HALT_INSTR_ALIGN',fault=2)
add('JALR clears bit zero',0x000302e7,0x101,wr=1,wb=4,pc=0x100)
add('JALR still misaligned',0x000302e7,0x103,pc=0,cause='HALT_INSTR_ALIGN',fault=0x102)
add('canonical NOP x0',0x00000013)
add('JAL to x0',0x0040006f)
add('Load to x0 still accesses',0x00032003,0x10000000,requests=1,bus=0x10000000)
add('LB upper negative byte',0x00030283,0x10000003,wr=1,wb=0xffffff80,requests=1,bus=0x10000000)
add('LBU upper byte',0x00034283,0x10000003,wr=1,wb=0x80,requests=1,bus=0x10000000)
add('LH upper negative halfword',0x00031283,0x10000002,wr=1,wb=0xffff80ff,requests=1,bus=0x10000000)
add('LHU upper halfword',0x00035283,0x10000002,wr=1,wb=0x80ff,requests=1,bus=0x10000000)
add('SB upper byte mask',0x00730023,0x10000003,0xa1b2c3d4,requests=1,bus=0x10000000,store=0xd4000000,mask=8)
add('SH upper halfword mask',0x00731023,0x10000002,0xa1b2c3d4,requests=1,bus=0x10000000,store=0xc3d40000,mask=12)
add('misaligned LW',0x00032283,0x10000002,pc=0,cause='HALT_LOAD_ALIGN',fault=0x10000002)
add('misaligned SW',0x00732023,0x10000002,pc=0,cause='HALT_STORE_ALIGN',fault=0x10000002)
add('misaligned LH',0x00031283,0x10000001,pc=0,cause='HALT_LOAD_ALIGN',fault=0x10000001)
add('misaligned SH',0x00731023,0x10000001,pc=0,cause='HALT_STORE_ALIGN',fault=0x10000001)
add('narrow MMIO load rejected',0x00030283,0x20000000,pc=0,cause='HALT_LOAD_ACCESS',fault=0x20000000)
add('narrow MMIO store rejected',0x00731023,0x20000000,pc=0,cause='HALT_STORE_ACCESS',fault=0x20000000)
add('word MMIO load accepted',0x00032283,0x20000000,wr=1,wb=0x80ff7f01,requests=1,bus=0x20000000)
add('word MMIO store accepted',0x00732023,0x20000000,0xa1b2c3d4,requests=1,bus=0x20000000,store=0xa1b2c3d4,mask=15)
add('load response error',0x00032283,0x10000000,pc=0,cause='HALT_LOAD_ACCESS',fault=0x10000000,requests=1,err=1,bus=0x10000000)
add('byte response error raw fault address',0x00030283,0x10000003,pc=0,cause='HALT_LOAD_ACCESS',fault=0x10000003,requests=1,err=1,bus=0x10000000)
add('store response error',0x00732023,0x10000000,0xa1b2c3d4,pc=0,cause='HALT_STORE_ACCESS',fault=0x10000000,requests=1,err=1,bus=0x10000000,store=0xa1b2c3d4,mask=15)
add('illegal instruction',0xffffffff,pc=0,cause='HALT_ILLEGAL')
add('MUL unsupported',0x027302b3,pc=0,cause='HALT_ILLEGAL')
add('CSR unsupported',0x300312f3,pc=0,cause='HALT_ILLEGAL')
add('FENCE reserved fields',0xffff8f8f)
lines=[]
for n,i,av,bv,wr,wb,pc,cause,fa,req,err,bus,store,mask in cases:
    vals=[f'"{n}"',f"32'h{i:08x}",f"32'h{av:08x}",f"32'h{bv:08x}",str(wr),f"32'h{wb:08x}",f"32'h{pc:08x}",cause,f"32'h{fa:08x}",str(req),str(err),f"32'h{bus:08x}",f"32'h{store:08x}",f"4'h{mask:x}"]
    lines.append('        run_case('+','.join(vals)+');')
p=root/'verify/tb_control_path.sv'
s=p.read_text(encoding='utf-8')
s=s.replace('// CASES_INSERT','\n'.join(lines))
p.write_text(s,encoding='utf-8')
(root/'case_spec.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
print('Generated',len(cases),'directed integration cases plus target-fetch fault sequence.')
