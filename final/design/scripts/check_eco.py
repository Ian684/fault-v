from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[1]
E=R/'eco'
def partition(path):
 rows=[line.split('\t') for line in path.read_text().splitlines()]
 parent={}
 def find(n):
  parent.setdefault(n,n)
  while parent[n]!=n:
   parent[n]=parent[parent[n]];n=parent[n]
  return n
 def union(a,b):
  parent[find(a)]=find(b)
 buffers={}
 endpoints={}
 for inst,ref,pin,net in rows:
  if re.fullmatch(r'sky130_fd_sc_hd__buf_\d+',ref):
   buffers.setdefault(inst,{})[pin.rsplit('/',1)[1]]=net
  else:
   key=(inst,ref,pin)
   assert key not in endpoints,key
   endpoints[key]=net
 for inst,pins in buffers.items():
  assert set(pins)=={'A','X'},(inst,pins)
  union(pins['A'],pins['X'])
 groups={}
 for key,net in endpoints.items():groups.setdefault(find(net),set()).add(key)
 return set(frozenset(v) for v in groups.values()),len(buffers),len(endpoints)
before,nb,ne=partition(E/'before.tsv')
after,na,nea=partition(E/'after.tsv')
assert before==after,('connectivity differs',len(before-after),len(after-before))
assert na-nb==468 and ne==nea
proof={'pass':True,'scope':'Exact non-buffer pin and top-port connectivity after collapsing positive identity buffers; not RTL formal equivalence.',
       'added_identity_buffers':na-nb,'compared_nonbuffer_endpoints':ne,'connected_components':len(before),
       'netlist_sha256':hashlib.sha256((E/'fault_v_asic_top.nl.v').read_bytes()).hexdigest()}
(E/'connectivity_proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print('PASS buffer-transparent connectivity:',proof)
