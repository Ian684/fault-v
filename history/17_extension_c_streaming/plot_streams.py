from pathlib import Path
import os,csv
R=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(R/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=list(csv.DictReader((R/'stream_benchmarks.csv').open()))
fig,axes=plt.subplots(1,2,figsize=(10.5,4.1),sharey=True,layout='constrained')
for mode,ax in enumerate(axes):
 for kind,label,color in [('COPY_main_sp','DMA copy','#246ba5'),('DOT_main','DOT4 accelerator','#be5f16'),('CHAIN','DMA + DOT4 chain','#238365')]:
  data=[r for r in rows if int(r['mode'])==mode and r['kind']==kind]
  data.sort(key=lambda r:int(r['n']))
  ax.plot([int(r['n']) for r in data],[float(r['speedup']) for r in data],marker='o',lw=2,color=color,label=label)
 ax.axhline(1,color='#777777',lw=1,ls='--');ax.set_xscale('log',base=2);ax.set_xticks([1,4,16,64,256,1024],[1,4,16,64,256,1024])
 ax.grid(alpha=.2);ax.set_xlabel('32-bit words / DOT4 groups');ax.set_title('IMEM / data RAM delay = %s clocks'%('1 / 1' if mode==0 else '4 / 7'));ax.set_ylim(0,8.4)
axes[0].set_ylabel('CPU cycles / engine cycles');axes[0].legend(loc='upper left',frameon=False)
fig.suptitle('Fault-V: measured whole-program RTL speedup at the same 50 MHz')
(R/'figures').mkdir(exist_ok=True)
fig.savefig(R/'figures/Streaming_Performance.png',dpi=180);fig.savefig(R/'figures/Streaming_Performance.pdf')
print('Saved PNG and PDF performance plots; includes configuration, polling and termination overhead.')
