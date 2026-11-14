"""Exact polygon-union areas in 70um tiles, aggregated into native 700um windows."""
from pathlib import Path
import hashlib,json,math,sys,pya

basefile,fillfile,reportfile=map(Path,sys.argv[1:4])
base=pya.Layout();fill=pya.Layout();base.read(str(basefile));fill.read(str(fillfile))
top=base.cell('fault_v_asic_top');ftop=fill.top_cell();assert top is not None and ftop is not None
assert base.dbu==fill.dbu
u=base.dbu;pitch=round(70/u);width=round(2500/u);height=round(3300/u)
nx,ny=math.ceil(width/pitch),math.ceil(height/pitch)
layers={'FOM':([(65,20),(65,44)],[(23,28),(65,99)],.33,.57),
        'POLY':([(66,20)],[(28,28),(66,99)],None,None),
        'LI':([(67,20)],[(56,28),(67,99)],.35,.60),
        'MET1':([(68,20)],[(36,28),(68,99)],.35,.60),
        'MET2':([(69,20)],[(41,28),(69,99)],.35,.60),
        'MET3':([(70,20)],[(34,28),(70,99)],.35,.60),
        'MET4':([(71,20)],[(51,28),(71,99)],.35,.60),
        'MET5':([(72,20)],[(59,28),(72,99)],.45,.76)}
def indices(layout,spec):return [i for a,b in spec if (i:=layout.find_layer(a,b)) is not None]
def region(cell,ids,box):
    r=pya.Region()
    for i in ids:r+=pya.Region(cell.begin_shapes_rec_overlapping(i,box))
    r&=pya.Region(box);r.merge();return r
def prefix(rows):
    p=[[0]*(len(rows[0])+1)]
    for row in rows:
        line=[0]
        for x,v in enumerate(row):line.append(line[-1]+p[-1][x+1]-p[-1][x]+v)
        p.append(line)
    return p
def area(p,x,y,w,h):return p[y+h][x+w]-p[y][x+w]-p[y+h][x]+p[y][x]
fixture=prefix([[1,2,3],[4,5,6]])
assert area(fixture,0,0,3,2)==21 and area(fixture,1,0,2,2)==16
cells=[[max(0,min(width,(x+1)*pitch)-x*pitch)*max(0,min(height,(y+1)*pitch)-y*pitch) for x in range(nx)] for y in range(ny)]
ap=prefix(cells);assert area(ap,0,0,nx,ny)==width*height
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'base_sha256':sha(basefile),'fill_sha256':sha(fillfile),'die_um':[2500,3300],'window_um':700,'step_um':70,'small_tiles':[nx,ny],'windows_per_layer':(nx-9)*(ny-9),'layers':{},'scope':'Exact area-weighted density screen using public PDK check_density thresholds, including clipped die-edge windows. POLY has no numeric limit in that checker. This is not an approved foundry density signoff deck.'}
for name,(base_spec,fill_spec,low,high) in layers.items():
    bi=indices(base,base_spec+fill_spec);fi=indices(fill,fill_spec);assert bi and fi,name
    before=[];after=[];overlap=0
    for y in range(ny):
        br=[];ar=[]
        for x in range(nx):
            box=pya.Box(x*pitch,y*pitch,min(width,(x+1)*pitch),min(height,(y+1)*pitch))
            a=region(top,bi,box);b=region(ftop,fi,box)
            overlap+=(a&b).area();br.append(a.area());ar.append((a|b).area())
        before.append(br);after.append(ar)
        if y%8==0:print('DENSITY_ROW',name,y,ny,flush=True)
    bp=prefix(before);fp=prefix(after);windows=[]
    for y in range(ny-9):
        for x in range(nx-9):
            denominator=area(ap,x,y,10,10);density=area(fp,x,y,10,10)/denominator
            windows.append({'x_um':x*70,'y_um':y*70,'density':density,'pass':None if low is None else low<=density<=high})
    assert len(windows)==record['windows_per_layer']
    vals=[w['density'] for w in windows];global_density=area(fp,0,0,nx,ny)/(width*height)
    result={'global_before':area(bp,0,0,nx,ny)/(width*height),'global_after':global_density,'window_min':min(vals),'window_max':max(vals),'limits':[low,high],'global_pass':None if low is None else low<=global_density<=high,'failed_windows':sum(w['pass'] is False for w in windows),'base_fill_overlap_um2':overlap*u*u,'windows':windows}
    record['layers'][name]=result;reportfile.write_text(json.dumps(record,indent=2)+'\n')
    print('DENSITY_LAYER',name,{k:v for k,v in result.items() if k!='windows'},flush=True)
record['all_numeric_density_checks_pass']=all(v['global_pass'] is not False and v['failed_windows']==0 for v in record['layers'].values())
reportfile.write_text(json.dumps(record,indent=2)+'\n')
print('SLIDING_DENSITY_COMPLETE',record['all_numeric_density_checks_pass'],flush=True)
