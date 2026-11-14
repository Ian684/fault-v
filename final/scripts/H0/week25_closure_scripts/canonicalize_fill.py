"""Translate only documented alternate dummy-fill purpose pairs; preserve every other byte."""
from collections import Counter
from pathlib import Path
import gzip, hashlib, io, json, struct, sys

PAIRS={65:23,66:28,67:56,68:36,69:41,70:34,71:51,72:59}
START={8,9,10,11,12,21,45}
def convert(source,target):
    assert source.is_file() and not target.exists()
    counts=Counter();same_in=hashlib.sha256();same_out=hashlib.sha256()
    opener=gzip.open if source.name.endswith('.gz') else open
    element=None;layer=None;dtype=None;seen_end=False
    with opener(source,'rb') as inp,gzip.open(target,'wb',compresslevel=6) as out:
        while True:
            head=inp.read(4)
            if not head:break
            assert len(head)==4
            length,kind,data=struct.unpack('>HBB',head);assert length>=4 and length%2==0
            payload=inp.read(length-4);assert len(payload)==length-4
            record=head+payload
            if kind not in (13,14):same_in.update(record)
            if kind in START:
                assert element is None;element=[];layer=dtype=None
            if element is not None:element.append(record)
            else:
                out.write(record)
                if kind not in (13,14):same_out.update(record)
            if kind==13:
                assert element is not None and length==6;layer=struct.unpack('>h',payload)[0]
            if kind==14:
                assert element is not None and length==6;dtype=struct.unpack('>h',payload)[0]
            if kind==17:
                assert element is not None
                if layer is not None:
                    assert layer in PAIRS and dtype==99,(layer,dtype)
                    counts[layer]+=1
                for rec in element:
                    k=rec[2]
                    if k==13:rec=rec[:4]+struct.pack('>h',PAIRS[layer])
                    elif k==14:rec=rec[:4]+struct.pack('>h',28)
                    out.write(rec)
                    if k not in (13,14):same_out.update(rec)
                element=None
            if kind==4:seen_end=True
    assert seen_end and element is None and counts and same_in.digest()==same_out.digest()
    return {'source':str(source),'target':str(target),'alternate_layer_element_counts':dict(counts),'mapping':{f'{a}/99':f'{b}/28' for a,b in PAIRS.items()},'all_non_layer_datatype_records_sha256':same_in.hexdigest(),'all_coordinates_properties_names_and_transforms_byte_exact':True}

if __name__=='__main__':
    src,dst=map(Path,sys.argv[1:3]);result=convert(src,dst)
    dst.with_suffix(dst.suffix+'.json').write_text(json.dumps(result,indent=2)+'\n')
    print('FILL_PURPOSE_CONVERSION',sum(result['alternate_layer_element_counts'].values()),flush=True)
