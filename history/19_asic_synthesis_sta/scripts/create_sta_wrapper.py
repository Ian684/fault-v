from pathlib import Path
import subprocess,re,json
r=Path(__file__).resolve().parents[2]
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trace=subprocess.check_output(['docker','run','--rm',image,'env','LD_TRACE_LOADED_OBJECTS=1','sta'],text=True)
paths=re.findall(r'/nix/store/[^\s()]+',trace)
loader=next(p for p in paths if Path(p).name.startswith('ld-linux'))
dirs=list(dict.fromkeys(str(Path(p).parent) for p in paths))
dest=r/'tools/sta_fixed_bin';(dest/'lib').mkdir(parents=True,exist_ok=True)
tcl=next(p for p in paths if Path(p).name=='libtcl.so')
alias=dest/'lib/libtcl8.6.so'
if alias.is_symlink():alias.unlink()
assert not alias.exists()
alias.symlink_to(tcl)
script="#!/bin/sh\nexec '"+loader+"' --library-path '/work/tools/sta_fixed_bin/lib:"+":".join(dirs)+"' /work/tools/opensta_fixed/build/sta \"$@\"\n"
(dest/'sta').write_text(script);(dest/'sta').chmod(0o755)
(r/'logs/sta_fixed_runtime.json').write_text(json.dumps({'image':image,'loader':loader,'libraries':paths},indent=2))
print("Prepared isolated STA wrapper using the pinned image runtime.")

