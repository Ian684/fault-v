from pathlib import Path
import sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load
db,b=load('/runtime/signal_closed.odb')
for name in ('_30389_','ANTENNA_7502'):
    i=b.findInst(name);print(name,i.getMaster().getName(),i.getLocation(),str(i.getOrient()))
    for p in i.getITerms():
        print('PIN',p.getMTerm().getName(),p.getNet().getName() if p.getNet() else None,[(l.getName(),[q.xMin(),q.yMin(),q.xMax(),q.yMax()]) for l,q in p.getGeometries()])
        if p.getMTerm().getName()=='DIODE':print('NATIVE_AP',[(a.getLayer().getName(),list(a.getPoint())) for a in p.getPrefAccessPoints()])
