from pathlib import Path
import json,hashlib
from application_models import datasets,input_image,outputs
from application_asm import Asm,kernel,words,assembly,CUSTOM_COUNTS,BASE
from binary_model import run
R=Path(__file__).resolve().parent
(R/'programs/applications').mkdir(exist_ok=True)
manifest=[];data=datasets();qualities=[]
def write_program(stem,p):
 encoded=words(p)
 (R/'programs/applications'/f'{stem}.mem').write_text(''.join(f'{x:08x}\n' for x in encoded+[0]*(4096-len(encoded))))
 (R/'programs/applications'/f'{stem}.S').write_text(assembly(p))
 return encoded
for index,d in enumerate(data):
 initial=input_image(d);gold,quality=outputs(d);qualities.append(dict(app=d['app'],case=d['name'],**quality))
 stem=f"{index:02d}_{d['app'].lower()}_{d['name']}"
 (R/'programs/applications'/f'{stem}_inputs.mem').write_text(''.join(f'{int.from_bytes(initial[i:i+4],"little"):08x}\n' for i in range(0,16384,4)))
 for custom in [False,True]:
  p=kernel(d['app'],custom);p.label('kernel_end');end_pc=len(p.ops)*4
  p.li(30,0x20000000);p.li(10,1);p.emit('sw',10,30,0);p.emit('ebreak')
  name=stem+('_custom' if custom else '_rv32i');encoded=write_program(name,p)
  if not custom:assert all((w&127)!=11 and not ((w&127)==0x33 and w>>25==1) for w in encoded)
  model=run(encoded,initial,end_pc)
  assert model['status']==1 and model['uart']==b''
  for i,v in gold:assert int.from_bytes(model['ram'][i*4:i*4+4],'little')==v,(name,i,hex(v),model['ram'][i*4:i*4+4].hex())
  assert model['counts']['custom']==(CUSTOM_COUNTS[d['app']] if custom else 0)
  manifest.append(dict(id=len(manifest),dataset=index,app=d['app'],case=d['name'],variant='custom' if custom else 'rv32i',image=f'{name}.mem',inputs=f'{stem}_inputs.mem',end_pc=end_pc,halt_pc=(len(encoded)-1)*4,words=len(encoded),outputs=gold,counts=model['counts']))
 print('PASS BINARY APPLICATION',index,d['app'],d['name'])
(R/'programs/application_datasets.json').write_text(json.dumps(data,indent=2))
(R/'programs/application_manifest.json').write_text(json.dumps(manifest,indent=2))
(R/'programs/quality.json').write_text(json.dumps(qualities,indent=2))
lines=[str(len(manifest))]
for m in manifest:
 c=m['counts'];lines.append(f"{m['id']} ../programs/applications/{m['image']} ../programs/applications/{m['inputs']} {m['end_pc']:08x} {m['halt_pc']:08x} {len(m['outputs'])} {c['instructions']} {c['custom']} {c['loads']} {c['stores']} {c['extra']}")
 lines.extend(f'{i} {v:08x}' for i,v in m['outputs'])
(R/'verify/applications.vec').write_text('\n'.join(lines)+'\n')

# A self-contained ROM initializes and checks one representative of each application family.
selected=[next(d for d in data if d['app']==app and d['name']==name) for app,name in [('CHAIN_INT8','alternating_extremes'),('FIR8_Q15','random'),('IIR1_Q15','alternating'),('FFT16_Q15','complex_tone')]]
p=Asm();check=0;demo_expected=[]
for n,d in enumerate(selected):
 initial=input_image(d);p.li(21,BASE)
 # Fill every word in each application's actual input ranges, including zeros.
 ranges=[(0,0xA0),(0x100,0x110)] if d['app']=='CHAIN_INT8' else [(0x300,0x90)] if d['app']=='FIR8_Q15' else [(0x400,0x40)] if d['app']=='IIR1_Q15' else [(0x500,0xA0)]
 # CNN FC weights/bias/control are outside its first input block.
 if d['app']=='CHAIN_INT8':ranges.append((0x180,0xA0))
 for off,length in ranges:
  for i in range(off,off+length,4):p.li(10,int.from_bytes(initial[i:i+4],'little'));p.emit('sw',10,21,i)
 p.emit('jal',31,f'app_{n}')
 gold,_=outputs(d);p.li(21,BASE)
 for i,v in gold:
  check+=1;p.li(30,check);p.li(18,BASE+i*4);p.emit('lw',10,18,0);p.li(11,v)
  p.emit('beq',10,11,f'check_{check}');p.emit('jal',0,'fail');p.label(f'check_{check}')
 demo_expected.extend((i,v) for i,v in gold)
p.li(21,0x20000100)
for n,b in enumerate(b'APP OK\r\n'):
 p.li(10,b);p.label(f'uart_{n}');p.emit('lw',11,21,4);p.emit('andi',11,11,1);p.emit('beq',11,0,f'uart_{n}');p.emit('sw',10,21,0)
p.label('drain');p.emit('lw',11,21,4);p.emit('andi',11,11,1);p.emit('beq',11,0,'drain')
for addr,value in [(0x20000200,5),(0x20000000,1)]:p.li(21,addr);p.li(10,value);p.emit('sw',10,21,0)
p.emit('ebreak');p.label('fail');p.li(21,BASE);p.emit('sw',30,21,0x7FC)
for addr,value in [(0x20000200,15),(0x20000000,2)]:p.li(21,addr);p.li(10,value);p.emit('sw',10,21,0)
p.emit('ebreak')
for n,d in enumerate(selected):
 p.label(f'app_{n}');body=kernel(d['app'],True);body.emit('jalr',0,31,0);p.append(body,f'a{n}_')
encoded=words(p);model=run(encoded,bytearray(16384),end_pc=0)
assert model['status']==1 and model['uart']==b'APP OK\r\n'
for i,v in demo_expected:assert int.from_bytes(model['ram'][i*4:i*4+4],'little')==v
(R/'programs/applications_demo.mem').write_text(''.join(f'{w:08x}\n' for w in encoded+[0]*(4096-len(encoded))))
(R/'programs/applications_demo.S').write_text(assembly(p))
(R/'verify/application_demo_outputs.vec').write_text(str(len(demo_expected))+'\n'+''.join(f'{i} {v:08x}\n' for i,v in demo_expected))
demo=dict(words=len(encoded),checks=check,custom_instructions=model['total_custom'],applications=[{'app':d['app'],'case':d['name']} for d in selected],success_text='APP OK\r\n',physical_benchmark_run=False)
(R/'programs/application_demo_manifest.json').write_text(json.dumps(demo,indent=2))
print('Generated',len(manifest),'images;',len(qualities),'datasets; self-check ROM:',demo)
