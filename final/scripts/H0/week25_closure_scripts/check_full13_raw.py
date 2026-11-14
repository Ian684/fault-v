"""Raw marker distribution only, to diagnose the long-running native route."""
from pathlib import Path
from openroad import Tech,Design
from collections import Counter
import hashlib,json,re,sys
C=Path('/work/week25_closure');source=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/runtime/timing_probe50.odb')
out=C/(sys.argv[2] if len(sys.argv)>2 else 'reports/full13_raw')
t=Tech();d=Design(t);d.readDb(str(source));d.evalTclString('set_thread_count 2')
report=out.with_suffix('.rpt');assert not report.exists()
d.evalTclString(f'drt::check_drc -output_file {report} -marker_name W25_Raw_Diagnostic')
text=report.read_text()
pattern=r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = \(([-0-9.]+), ([-0-9.]+)\) - \(([-0-9.]+), ([-0-9.]+)\) on Layer ([^\n]+)'
rows=[{'type':m[0],'srcs':m[1],'bbox_um':list(map(float,m[2:6])),'layer':m[6]} for m in re.findall(pattern,text)]
assert len(rows)==text.count('violation type:')
hist=Counter((round((r['bbox_um'][0]+r['bbox_um'][2])/2)//100,round((r['bbox_um'][1]+r['bbox_um'][3])/2)//100) for r in rows)
record={'raw_marker_count':len(rows),'types':dict(Counter(r['type'] for r in rows)),'layers':dict(Counter(r['layer'] for r in rows)),'top_100um_regions':hist.most_common(12),'markers':rows,'accepted':False,'scope':'Raw marker distribution on stable completed iteration 13 only. No centered-context partition classification and no signoff inference.'}
with source.open('rb') as f:record['source_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
record['source']=str(source);record['scope']='Raw marker distribution on a completed fixed checkpoint only. No centered-context partition classification and no signoff inference.'
out.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='markers'},indent=2),flush=True)
