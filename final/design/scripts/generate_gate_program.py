from pathlib import Path
import sys,json,zlib,struct
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R))
from application_asm import Asm,words,assembly
from reference import execute
p=Asm();checks=0
def check(reg,value):
 global checks
 checks+=1;p.li(13,value);p.emit('beq',reg,13,'ok%d'%checks);p.emit('jal',0,'failure');p.label('ok%d'%checks)
def wr(addr,value):
 p.li(28,addr);p.li(29,value);p.emit('sw',29,28,0)
def cfg(base,a,b,dst):
 for off,val in [(8,a),(12,b),(16,dst),(20,1),(0,1)]:wr(base+off,val)
def poll(base,label):
 p.li(28,base);p.label(label);p.emit('lw',29,28,4);p.emit('andi',30,29,1);p.emit('bne',30,0,label);check(29,2)
vectors=[
 ('DOT4',0x807f00ff,0x7f80ff01,0),
 ('MUL16',0x8000,0xffff,0),
 ('ADDSAT',0x7fffffff,1,0),
 ('QNT8',0xffffff80,3,0),
 ('DOT4ACC',0x01020304,0xffffffff,123),
 ('MAC16',1,1,0x7fffffff),
 ('ADD8SAT',0x7f807f80,0x7f807f80,0),
 ('SUB8SAT',0x7f807f80,0x807f807f,0),
 ('RQNT8',0xfffffffd,1|(1<<16)|(2<<21),0),
 ('DOT2SAT',0x80008000,0x80008000,0),
 ('DOT8',0x87f01234,0xf7812340,0),
 ('DOT4SU',0xff807f01,0xff0080ff,0)]
for op,a,b,acc in vectors:
 p.li(10,a);p.li(11,b);p.li(12,acc);p.emit(op,12,10,11);check(12,execute(op,a,b,acc))
a=0x807f00ff;b=0x7f80ff01
wr(0x10000000,a);wr(0x10000004,b)
cfg(0x20000300,0x10000000,0,0x10010000);poll(0x20000300,'dma')
cfg(0x20000400,0x10010000,0x10000004,0x10003000);poll(0x20000400,'acc')
p.li(28,0x10003000);p.emit('lw',12,28,0);check(12,execute('DOT4',a,b))
wr(0x20000200,5);wr(0x20000000,1);halt_pc=len(p.ops)*4;p.emit('ebreak')
p.label('failure');wr(0x20000200,15);wr(0x20000000,2);p.emit('ebreak')
image=words(p);payload=b''.join(struct.pack('<I',x) for x in image)
packet=b'FV\x01\x00'+struct.pack('<H',len(image))+payload+struct.pack('<I',zlib.crc32(payload))
(R/'programs/gate_program.mem').write_text(''.join('%08x\n'%w for w in image))
(R/'programs/gate_program.s').write_text(assembly(p))
(R/'programs/gate_packet.hex').write_text(''.join('%02x\n'%b for b in packet))
meta=dict(words=len(image),packet_bytes=len(packet),checks=checks,halt_pc=halt_pc,crc32=zlib.crc32(payload))
(R/'programs/gate_program.json').write_text(json.dumps(meta,indent=2))
template=(R/'verify/tb_gate_template.sv').read_text().replace('@PACKET_BYTES@',str(len(packet))).replace('@HALT_PC@',str(halt_pc))
(R/'verify/tb_gate.sv').write_text(template)
print('Gate program:',meta)
