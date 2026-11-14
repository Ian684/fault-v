"""Verify diagnostic checkpoint identities and compare both native counters together."""
from pathlib import Path
import hashlib,json,re,sys

def verified_pair(stage,proof):
    a=json.loads(proof.read_text())
    assert a['accepted'] is False
    assert all(type(a[k]) is int and a[k]>=0 for k in ['native_DRC','antenna_nets','stage'])
    assert re.fullmatch(r'guarded_stage_[0-9]+\.odb',a['odb_file'])
    assert a['odb_file']==f"guarded_stage_{a['stage']}.odb" and proof.name==f"guarded_stage_{a['stage']}.json"
    odb=stage/a['odb_file']
    assert hashlib.sha256(odb.read_bytes()).hexdigest()==a['odb_sha256'],'Checkpoint hash mismatch'
    return a

def frontier(pairs):
    return [p for p in pairs if not any(q['native_DRC']<=p['native_DRC'] and q['antenna_nets']<=p['antenna_nets'] and (q['native_DRC'],q['antenna_nets'])!=(p['native_DRC'],p['antenna_nets']) for q in pairs)]

def collect(root,tag):
    assert re.fullmatch(r'[A-Za-z0-9_]+',tag)
    stage=root/'runs'/tag/'1-openroad-detailedrouting'
    pairs=sorted([verified_pair(stage,p) for p in stage.glob('guarded_stage_*.json')],key=lambda a:a['stage'])
    zero=[p for p in pairs if p['antenna_nets']==0]
    return {'run':tag,'accepted':False,'checkpoints':pairs,'nondominated_checkpoints':frontier(pairs),
            'best_zero_antenna_checkpoint':min(zero,key=lambda p:p['native_DRC']) if zero else None,
            'scope':'Each pair is measured after native route commit and bound to the same ODB SHA256. Native diagnostic counters do not establish physical/RC/TT/independent-DRC acceptance.'}

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];tag=sys.argv[1]
    result=collect(root,tag);out=root/'reports'/tag;out.mkdir(parents=True,exist_ok=True)
    (out/'paired_checkpoints.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
