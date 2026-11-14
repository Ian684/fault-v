"""Draw the accepted OpenDB geometry; this is not a placed-cell layout."""
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch

R=Path(__file__).resolve().parents[1]
d=json.loads((R/"reports/floorplan_accepted/floorplan_checks.json").read_text())
fig, axes=plt.subplots(1,2,figsize=(11,8.5),layout="constrained")
colors={"imem":"#79c9bf","dmem":"#90bce6","scratch":"#f3bd76"}
for ax in axes:
    ax.set_aspect("equal")
    ax.set_xlim(-110,2610);ax.set_ylim(-100,3400)
    ax.add_patch(Rectangle((0,0),2500,3300,fill=False,lw=1.4,color="#243247"))
    a,b,c,e=d["core_um"]
    ax.add_patch(Rectangle((a,b),c-a,e-b,fill=False,ls="--",lw=.7,color="#718096"))
    ax.set_xlabel("x (um)");ax.set_ylabel("y (um)")
    ax.spines[["top","right"]].set_visible(False)
for name,m in d["macros"].items():
    kind=next(k for k in colors if "u_"+k+"." in name)
    bank=name.split("banks[")[1].split("]")[0]
    x,y,x1,y1=m["bbox"];hx,hy,hx1,hy1=m["halo"]
    axes[0].add_patch(Rectangle((hx,hy),hx1-hx,hy1-hy,facecolor="#e7ebf0",lw=0))
    axes[0].add_patch(Rectangle((x,y),x1-x,y1-y,facecolor=colors[kind],edgecolor="#334155",lw=.6))
    axes[0].text((x+x1)/2,(y+y1)/2,f"{kind.upper()} {bank}\n2 KiB",ha="center",va="center",fontsize=9,color="#18263a")
    axes[1].add_patch(Rectangle((x,y),x1-x,y1-y,facecolor="#e4e8ee",edgecolor="#a7afbb",lw=.3))
for s in d["plot_shapes"]:
    x,y,x1,y1=s["bbox"]
    axes[1].add_patch(Rectangle((x,y),x1-x,y1-y,facecolor="#d84545" if s["net"]=="VPWR" else "#376fbd",lw=0))
for p, boxes in d["signal_pins"].items():
    for box in boxes:
        x,y,x1,y1=box["bbox"]
        axes[0].plot((x+x1)/2,(y+y1)/2,marker=".",ms=2,color="#18263a")
axes[0].set_title("SRAM floorplan and signal pins",loc="left",fontsize=12,fontweight="bold")
axes[1].set_title("Actual met4 / met5 power shapes",loc="left",fontsize=12,fontweight="bold")
axes[0].legend(handles=[Patch(color=colors[k],label=k.upper()) for k in colors],loc="upper center",bbox_to_anchor=(.5,-.12),ncol=3,frameon=False,fontsize=9)
axes[1].legend(handles=[Patch(color="#d84545",label="VPWR"),Patch(color="#376fbd",label="VGND")],loc="upper center",bbox_to_anchor=(.5,-.12),ncol=2,frameon=False,fontsize=9)
fig.suptitle("Fault-V | 2500 x 3300 um floorplan",fontsize=16,fontweight="bold")
fig.supxlabel("Extracted from accepted OpenDB. Functional standard cells are unplaced; no CTS or signal routing.",fontsize=9)
(R/"figures").mkdir(exist_ok=True)
fig.savefig(R/"figures/Floorplan_PDN.png",dpi=180)
fig.savefig(R/"figures/Floorplan_PDN.svg")
print("Rendered actual macro / PDN geometry")
