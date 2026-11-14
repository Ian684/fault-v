"""Plot checked OpenDB geometry and clock connectivity; this is not routed metal."""
from pathlib import Path
import json,sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Patch
from matplotlib.collections import PatchCollection,LineCollection
R=Path(__file__).resolve().parents[1]
tag=sys.argv[1]
g=json.loads((R/"reports"/tag/"placement_checks.json").read_text())
assert g["pass"]
fig,axes=plt.subplots(1,2,figsize=(12,8.4),layout="constrained")
colors={"imem":"#1d8a83","dmem":"#3568a3","scratch":"#bc7627"}
for ax in axes:
    ax.set_aspect("equal")
    ax.set_xlim(-60,2560);ax.set_ylim(-50,3400)
    ax.add_patch(Rectangle((0,0),2500,3300,fill=False,lw=1.1,ec="#334155"))
    ax.add_patch(Rectangle((80.04,81.6),2339.56,3136.16,fill=False,lw=.7,ls="--",ec="#64748b"))
    ax.set_xlabel("x (um)");ax.set_ylabel("y (um)")
for ax in axes:
    for name,m in g["macros"].items():
        x,y,x2,y2=m["bbox"]
        kind=next(k for k in colors if k in name)
        ax.add_patch(Rectangle((x,y),x2-x,y2-y,facecolor=colors[kind],alpha=.22,ec=colors[kind],lw=.8))
        import re
        index=re.search(r"banks.*?([0-9]+)",name)[1]
        ax.text((x+x2)/2,(y+y2)/2,kind.upper()+" "+index,ha="center",va="center",fontsize=7.5,color="#24364b")
patches=[Rectangle((x,y),x2-x,y2-y) for x,y,x2,y2,master in g["standard_cells"]]
axes[0].add_collection(PatchCollection(patches,facecolor="#334155",edgecolor="none",alpha=.7,rasterized=True))
axes[0].set_title("Placed standard cells + 18 fixed SRAMs",fontsize=11,pad=12)
segments=[[(x,y),(x2,y2)] for x,y,x2,y2 in g["clock_connectivity_edges"]]
axes[1].add_collection(LineCollection(segments,colors="#8051b1",lw=.32,alpha=.48,rasterized=True))
centers=[((box[0]+box[2])/2,(box[1]+box[3])/2) for name,box,master in g["clock_buffers"] if name in g["active_clock_buffer_cells"]]
assert len(centers)==g["active_clock_buffer_count"]
axes[1].scatter([p[0] for p in centers],[p[1] for p in centers],s=4,c="#4b237d",linewidths=0,zorder=4)
axes[1].set_title("Clock connectivity (straight lines, not routes)",fontsize=11,pad=12)
fig.suptitle("Fault-V | Placement and Clock Tree",fontsize=17,fontweight="bold",color="#16324f")
handles=[Patch(facecolor=c,alpha=.35,label=k.upper()) for k,c in colors.items()]
handles.extend([Patch(facecolor="#334155",label="Standard cells"),Patch(facecolor="#8051b1",label="Clock connections")])
fig.legend(handles=handles,loc="outside lower center",ncol=5,frameon=False,fontsize=9)
out=R/"figures";out.mkdir(exist_ok=True)
for suffix in ["png","svg"]:
    fig.savefig(out/("placement_cts."+suffix),dpi=200,facecolor="white")
plt.close(fig)
print("Rendered checked physical geometry and clock connectivity")
