from pathlib import Path
import os,json,math
R=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(R/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from application_models import fir,iir,fft
data=json.loads((R/'programs/application_datasets.json').read_text())
def case(app,name):return next(d for d in data if d['app']==app and d['name']==name)
fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
d=case('FIR8_Q15','impulse');fixed,_=fir(d)
ideal=[sum(d['samples'][n+k]*d['coefficients'][k] for k in range(8))/32768 for n in range(32)]
axes[0,0].plot([x/32768 for x in ideal],label='Float reference',lw=2)
axes[0,0].plot([x/32768 for x in fixed],'o',ms=3,label='Fixed Q15')
axes[0,0].set(title='FIR8 impulse response',xlabel='Valid-window index',ylabel='Output amplitude')
d=case('IIR1_Q15','step');fixed,q=iir(d)
axes[0,1].plot([x/32768 for x in q['ideal']],label='Float reference',lw=2)
axes[0,1].plot([x/32768 for x in fixed],'o',ms=3,label='Fixed Q15')
axes[0,1].set(title='IIR1 step response',xlabel='Sample index',ylabel='Output amplitude')
d=case('FFT16_Q15','complex_tone');fixed,q=fft(d)
mag=[math.hypot(*v)/32768 for v in fixed];ideal=[math.hypot(*v)/32768 for v in q['ideal']]
axes[1,0].plot(range(16),ideal,label='Direct DFT / 16',lw=2)
axes[1,0].plot(range(16),mag,'o',ms=4,label='Fixed FFT / 16')
axes[1,0].set(title='Complex tone at bin 5',xlabel='Frequency bin',ylabel='Normalized magnitude',xticks=range(0,16,2))
axes[1,1].plot(range(16),[fixed[k][0]-q['ideal'][k][0] for k in range(16)],'o-',label='Real error')
axes[1,1].plot(range(16),[fixed[k][1]-q['ideal'][k][1] for k in range(16)],'s-',label='Imaginary error')
axes[1,1].set(title='FFT quantization error',xlabel='Frequency bin',ylabel='Error (raw Q15 LSB)',xticks=range(0,16,2))
for ax in axes.flat:ax.grid(alpha=.25);ax.legend(fontsize=8)
fig.suptitle('Fault-V application precision: fixed-point results and independent float references',fontsize=13)
(R/'figures').mkdir(exist_ok=True)
fig.savefig(R/'figures/DSP_Precision.png',dpi=180)
fig.savefig(R/'figures/DSP_Precision.pdf')
print('Created standalone PNG and PDF precision figure.')
