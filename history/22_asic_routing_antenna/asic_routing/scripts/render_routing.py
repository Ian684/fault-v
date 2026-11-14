"""Render checked routed centerlines; macro geometry and clock net labels are actual."""
from pathlib import Path
import json,sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle,Patch
R=Path(__file__).resolve().parents[1]
tag=sys.argv[1]
g=json.loads((R/"reports"/tag/"placement_checks.json").read_text())
w=json.loads((R/"reports"/tag/"route_checks.json").read_text())
segments=json.loads((R/"reports"/tag/"wire_segments.json").read_text())
assert g["pass"] and w["pass"]
fig,axes=plt.subplots(1,2,figsize=(12,8.4),layout="constrained")
colors={"li1":"#8a8e99","met1":"#c55b56","met2":"#5888bb","met3":"#4c9a75","met4":"#ad78bd","met5":"#be9035"}
for ax in axes:
    ax.set_aspect("equal");ax.set_xlim(-60,2560);ax.set_ylim(-50,3400)
    ax.add_patch(Rectangle((0,0),2500,3300,fill=False,lw=1,ec="#334155"))
    ax.add_patch(Rectangle((80.04,81.6),2339.56,3136.16,fill=False,lw=.7,ls="--",ec="#64748b"))
    for name,m in g["macros"].items():
        x,y,x2,y2=m["bbox"]
        ax.add_patch(Rectangle((x,y),x2-x,y2-y,facecolor="#e8edf2",edgecolor="#b5c2d0",lw=.7,zorder=0))
        import re
        kind=next(k for k in ["imem","dmem","scratch"] if k in name)
        number=re.search(r"banks.*?([0-9]+)",name)[1]
        ax.text((x+x2)/2,(y+y2)/2,kind.upper()+" "+number,ha="center",va="center",fontsize=7,color="#64748b",zorder=1)
    ax.set_xlabel("x (um)");ax.set_ylabel("y (um)")
for layer,color in colors.items():
    rows=[[(x,y),(x2,y2)] for l,x,y,x2,y2,clock in segments if l==layer]
    if rows:axes[0].add_collection(LineCollection(rows,colors=color,lw=.22,alpha=.62,rasterized=True,zorder=2))
clock_rows=[[(x,y),(x2,y2)] for l,x,y,x2,y2,clock in segments if clock]
axes[1].add_collection(LineCollection(clock_rows,colors="#674699",lw=.38,alpha=.7,rasterized=True,zorder=2))
axes[0].set_title("Routed signal + clock centerlines",fontsize=11,pad=12)
axes[1].set_title("Clock routes through the CTS network",fontsize=11,pad=12)
fig.suptitle("Fault-V | Detailed Routing",fontsize=17,fontweight="bold",color="#16324f")
fig.legend(handles=[Patch(facecolor=c,label=l) for l,c in colors.items()],loc="lower center",bbox_to_anchor=(0.5,-0.025),ncol=6,frameon=False,fontsize=9)
out=R/"figures";out.mkdir(exist_ok=True)
for suffix in ["png","svg"]:fig.savefig(out/("routing."+suffix),dpi=200,facecolor="white",bbox_inches="tight")
plt.close(fig)
print("Rendered actual routed centerlines; PG geometry and via polygons are omitted")
