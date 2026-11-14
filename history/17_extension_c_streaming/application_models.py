"""Direct application references; independent of generated instruction execution."""
import cmath,math,random
MASK=0xffffffff
TWIDDLES=[(32767,0),(30274,-12540),(23170,-23170),(12540,-30274),(0,-32768),(-12540,-30274),(-23170,-23170),(-30274,-12540)]
def clip16(x):return max(-32768,min(32767,x))
def requant(x,ctrl):
 m=(ctrl&65535);m=m-65536 if m&32768 else m
 s=(ctrl>>16)&31;z=(ctrl>>21)&255;z=z-256 if z&128 else z
 product=x*m;assert -(1<<31)<product<(1<<31),'Application software quantization range'
 q,r=divmod(abs(product),1<<s)
 if s and r*2>=1<<s:q+=1
 return max(-128,min(127,(-q if product<0 else q)+z))
def control(m,s,z=0):return (m&65535)|(s<<16)|((z&255)<<21)
def convolution(d):
 raw=[d['conv_bias'][o]+sum(d['input'][(n+k)*2+c]*d['conv_weights'][o][k*2+c] for k in range(3) for c in range(2)) for n in range(8) for o in range(3)]
 assert all(-(1<<31)<x<1<<31 for x in raw)
 q=[max(0,requant(x,d['conv_control'][i%3])) for i,x in enumerate(raw)]
 return raw,q
def dense(d,input_values):
 raw=[d['fc_bias'][o]+sum(x*w for x,w in zip(input_values,d['fc_weights'][o])) for o in range(4)]
 q=[requant(x,d['fc_control'][o]) for o,x in enumerate(raw)]
 return raw,q,max(range(4),key=lambda i:q[i])
def fir(d):
 raw=[sum(d['samples'][n+k]*d['coefficients'][k] for k in range(8)) for n in range(32)]
 assert max(abs(x) for x in raw)<1<<31
 result=[clip16(x>>15) for x in raw]
 ideal=[max(-32768,min(32767,x/32768)) for x in raw]
 return result,dict(max_abs_error_lsb=max(abs(a-b) for a,b in zip(result,ideal)),saturation_count=sum(not -32768<=x>>15<=32767 for x in raw),maximum_accumulator=max(abs(x) for x in raw))
def iir(d):
 previous=0;floating=0.;result=[];ideal=[]
 for x in d['samples']:
  acc=8192*x+24576*previous;assert -(1<<31)<acc<1<<31
  previous=clip16(acc>>15);result.append(previous)
  floating=.25*x+.75*floating;ideal.append(floating)
 error=max(abs(a-b) for a,b in zip(result,ideal));assert error<=4
 return result,dict(max_abs_error_lsb=error,ideal=ideal)
def fft(d):
 values=[list(d['samples'][int(f'{i:04b}'[::-1],2)]) for i in range(16)]
 saturations=0;maximum=0
 for m in [2,4,8,16]:
  for start in range(0,16,m):
   for j in range(m//2):
    ur,ui=values[start+j];vr,vi=values[start+j+m//2];wr,wi=TWIDDLES[j*16//m]
    real=vr*wr-vi*wi;imag=vr*wi+vi*wr
    assert max(abs(real),abs(imag))<1<<31
    maximum=max(maximum,abs(real),abs(imag));tr,ti=real>>15,imag>>15
    raw=[(ur+tr)>>1,(ui+ti)>>1,(ur-tr)>>1,(ui-ti)>>1]
    saturations+=sum(not -32768<=v<=32767 for v in raw)
    values[start+j]=[clip16(raw[0]),clip16(raw[1])]
    values[start+j+m//2]=[clip16(raw[2]),clip16(raw[3])]
 ideal=[sum(complex(*d['samples'][n])*cmath.exp(-2j*math.pi*k*n/16) for n in range(16))/16 for k in range(16)]
 error=max(max(abs(values[k][0]-ideal[k].real),abs(values[k][1]-ideal[k].imag)) for k in range(16))
 if d['name']!='fullscale_saturation':assert error<=12 and saturations==0
 return values,dict(max_abs_error_lsb=error,saturation_count=saturations,maximum_product_sum=maximum,ideal=[[v.real,v.imag] for v in ideal])

def datasets():
 rng=random.Random(0xb1719);out=[]
 for k,name in enumerate(['zeros','positive','negative','alternating_extremes','random_a','random_b']):
  x=[0]*20 if k==0 else [32]*20 if k==1 else [-32]*20 if k==2 else [127,-128]*10 if k==3 else [rng.randrange(-128,128) for _ in range(20)]
  d=dict(name=name,input=x,conv_weights=[[rng.randrange(-32,33) for _ in range(6)] for _ in range(3)],conv_bias=[-200,0,200],conv_control=[control(3,8),control(7,9),control(11,10)],fc_input=[rng.randrange(-128,128) for _ in range(24)],fc_weights=[[rng.randrange(-32,33) for _ in range(24)] for _ in range(4)],fc_bias=[-300,100,250,-50],fc_control=[control(7,10,-5)]*4)
  for app in ['CONV1D_INT8','FC_INT8','CHAIN_INT8']:
   item=dict(app=app,**d)
   if app=='FC_INT8' and k<4:item['fc_input']=[0]*24 if k==0 else [32]*24 if k==1 else [-32]*24 if k==2 else [127,-128]*12
   out.append(item)
 smooth=[1024,2048,4096,9216,9216,4096,2048,1024]
 for name,samples,coef in [('impulse',[0]*7+[20000]+[0]*31,smooth),('step',[20000]*39,smooth),('random',[rng.randrange(-20000,20001) for _ in range(39)],smooth),('positive_saturation',[20000]*39,[8192]*8),('negative_saturation',[-20000]*39,[8192]*8)]:out.append(dict(app='FIR8_Q15',name=name,samples=samples,coefficients=coef))
 for name,samples in [('impulse',[32767]+[0]*31),('step',[10000]*32),('alternating',[32767,-32768]*16),('random',[rng.randrange(-32768,32768) for _ in range(32)])]:out.append(dict(app='IIR1_Q15',name=name,samples=samples))
 fft_cases=[('zeros',[(0,0)]*16),('impulse',[(8192,0)]+[(0,0)]*15),('dc',[(4096,0)]*16),('real_tone',[(round(8192*math.cos(2*math.pi*3*n/16)),0) for n in range(16)]),('complex_tone',[(round(4096*math.cos(2*math.pi*5*n/16)),round(4096*math.sin(2*math.pi*5*n/16))) for n in range(16)]),('random',[(rng.randrange(-6000,6001),rng.randrange(-6000,6001)) for _ in range(16)]),('fullscale_saturation',[(32767 if math.cos(2*math.pi*n/16)>=0 else -32768,32767 if math.sin(2*math.pi*n/16)>=0 else -32768) for n in range(16)])]
 for name,samples in fft_cases:out.append(dict(app='FFT16_Q15',name=name,samples=samples))
 assert len(out)==34
 return out

def input_image(d):
 ram=bytearray(16384)
 def fill(offset,values,size):
  for i,x in enumerate(values):ram[offset+i*size:offset+(i+1)*size]=(x&((1<<(size*8))-1)).to_bytes(size,'little')
 if d['app'] in ['CONV1D_INT8','FC_INT8','CHAIN_INT8']:
  fill(0,d['input'],1);fill(0x40,[x for row in d['conv_weights'] for x in row],1);fill(0x80,d['conv_bias'],4);fill(0x90,d['conv_control'],4)
  fill(0x100,d['fc_input'],1);fill(0x180,[x for row in d['fc_weights'] for x in row],1);fill(0x200,d['fc_bias'],4);fill(0x210,d['fc_control'],4)
 elif d['app']=='FIR8_Q15':fill(0x300,d['samples'],2);fill(0x380,d['coefficients'],2)
 elif d['app']=='IIR1_Q15':fill(0x400,d['samples'],2)
 else:fill(0x500,[x for pair in d['samples'] for x in pair],2);fill(0x580,[x for pair in TWIDDLES for x in pair],2)
 return ram

def outputs(d):
 expected=bytearray(16384);offsets=[];quality={}
 def save(off,values,size):
  for i,x in enumerate(values):expected[off+i*size:off+(i+1)*size]=(x&((1<<(size*8))-1)).to_bytes(size,'little')
  offsets.extend(range(off//4,(off+len(values)*size+3)//4))
 if d['app'] in ['CONV1D_INT8','CHAIN_INT8']:
  raw,q=convolution(d);save(0x800,raw,4);save(0x1000,q,1)
 if d['app'] in ['FC_INT8','CHAIN_INT8']:
  raw,q,pred=dense(d,convolution(d)[1] if d['app']=='CHAIN_INT8' else d['fc_input']);save(0x900,raw,4);save(0x1100,q,1);save(0x1110,[pred],4)
 if d['app']=='FIR8_Q15':result,quality=fir(d);save(0x1200,result,4)
 if d['app']=='IIR1_Q15':result,quality=iir(d);save(0x1300,result,4)
 if d['app']=='FFT16_Q15':result,quality=fft(d);save(0x1400,[v for pair in result for v in pair],4)
 return [(i,int.from_bytes(expected[i*4:i*4+4],'little')) for i in offsets],quality
