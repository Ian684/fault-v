"""Use the pinned PDK's native tiled fill scripts with bounded concurrency."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, tempfile, time

source=Path(sys.argv[1]).resolve();destination=Path(sys.argv[2]).resolve()
assert source.is_file() and not destination.exists()
destination.mkdir(parents=True)
# Native temporary storage avoids long 9P stalls; every result is copied back and hash checked.
folder=Path(tempfile.mkdtemp(prefix='faultv-native-fill-'))
def sha(path):
    with path.open('rb') as inp:return hashlib.file_digest(inp,'sha256').hexdigest()
def copy_verified(a,z):
    assert not z.exists();partial=z.with_name(z.name+'.part');assert not partial.exists()
    with a.open('rb') as inp,partial.open('wb') as out:shutil.copyfileobj(inp,out,1024*1024)
    assert sha(a)==sha(partial);partial.rename(z)
copy_verified(source,folder/'fault_v_asic_top.gds')
pdk=Path('/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71')
helper=pdk/'sky130A/libs.tech/magic/generate_fill.py'
original_tech=pdk/'sky130A/libs.tech/magic/sky130A-GDS.tech'
tech=Path(os.environ.get('FILL_TECH_FILE',str(original_tech)));assert tech.is_file()
env=dict(os.environ,PDK_ROOT=str(pdk),PDK='sky130A',MAGTYPE='mag')
report={'source_sha256':sha(source),'native_generator_sha256':sha(helper),'generation_tech_sha256':sha(tech),'original_PDK_tech_sha256':sha(original_tech),'orchestrator_sha256':sha(Path(__file__)),'workers':2,'native_temporary_storage':True,'all_outputs_hash_verified_in_E':True,'scope':'Native tiled fill generation only. Final candidate acceptance depends on separate geometry, density and post-route/model gates.','started_unix':time.time(),'tiles':{}}
def run(args,log):
    with (destination/log).open('w') as out:
        subprocess.run(args,cwd=folder,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,check=True)
    assert (destination/log).stat().st_size>0
run(['python3',str(helper),'fault_v_asic_top.gds','-dist','-keep','-test'],'prepare.log')
def magic(script,*args):return ['magic','-dnull','-noconsole','-T',str(tech),script,*args]
run(magic('generate_fill.tcl'),'flatten.log')
info=(folder/'fill_gen_info.txt').read_text().splitlines();assert len(info)==6
nx,ny=int(info[2]),int(info[3]);assert 0<nx*ny<=100
tiles=sorted(folder.glob('fault_v_asic_top_fill_pattern_*_*.mag'));assert len(tiles)==nx*ny
def fill(tile):
    start=time.time();run(magic('generate_fill_dist.tcl',tile.name+'x'),tile.stem+'.log')
    gds=tile.with_suffix('.gds');assert gds.stat().st_size>1000
    copy_verified(gds,destination/gds.name)
    return tile.stem,{'elapsed_s':time.time()-start,'bytes':gds.stat().st_size,'sha256':sha(gds)}
with ThreadPoolExecutor(max_workers=2) as pool:
    for name,result in pool.map(fill,tiles):
        report['tiles'][name]=result
        (destination/'generation.json').write_text(json.dumps(report,indent=2)+'\n')
        print('NATIVE_FILL_TILE',name,result['elapsed_s'],flush=True)
# Preserve flattened evidence; hide .mag names so native final uses its documented GDS references.
for tile in tiles:tile.rename(tile.with_suffix('.mag.evidence'))
run(magic('generate_fill_final.tcl'),'merge.log')
output=folder/'fault_v_asic_top_fill_pattern.gds.gz';assert output.stat().st_size>1000
assert sha(folder/'fault_v_asic_top.gds')==report['source_sha256']
report.update(completed_unix=time.time(),fill_sha256=sha(output),expected_tiles=nx*ny)
copy_verified(output,destination/output.name)
for name in ('generate_fill.tcl','generate_fill_dist.tcl','generate_fill_final.tcl','fill_gen_info.txt'):copy_verified(folder/name,destination/name)
(destination/'generation.json').write_text(json.dumps(report,indent=2)+'\n')
print('NATIVE_FILL_COMPLETE',nx*ny,report['fill_sha256'],flush=True)
