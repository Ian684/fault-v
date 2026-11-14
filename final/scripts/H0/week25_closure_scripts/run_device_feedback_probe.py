"""Compare the two warning-bearing cells against PDK SPICE, with wiring fault controls."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,tempfile,sys
C=Path('/work/week25_closure');pdk=C.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71'
library=pdk/'sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice'
tag=sys.argv[1] if len(sys.argv)>1 else 'pg_d_lvs_f';assert re.fullmatch('[a-z0-9_]+',tag)
extraction=C/'runs'/tag/'1-magic-spiceextraction/extraction'
output=C/'reports'/('device_feedback_'+tag);assert not output.exists();output.mkdir()
with tempfile.TemporaryDirectory(prefix='faultv-device-feedback-') as temporary:
    tmp=Path(temporary);cases={}
    for suffix,bad_from,bad_to in [('decap_3','X1 VGND VPWR VGND VNB','X1 VGND VGND VGND VNB'),('diode_2','XD0 VNB DIODE','XD0 VNB VGND')]:
        name='sky130_fd_sc_hd__'+suffix;ext=extraction/(name+'.ext');shutil.copyfile(ext,tmp/ext.name)
        matches=re.findall(r'(?ims)^\.subckt\s+'+re.escape(name)+r'\s+.*?^\.ends[^\n]*',library.read_text());assert len(matches)==1
        reference=matches[0]+'\n';assert reference.count(bad_from)==1
        (tmp/(suffix+'_reference.spice')).write_text(reference)
        (tmp/(suffix+'_bad.spice')).write_text(reference.replace(bad_from,bad_to))
        cases[suffix]={'cell':name,'input_ext_sha256':hashlib.sha256(ext.read_bytes()).hexdigest(),'fault_control':bad_from+' -> '+bad_to}
    tcl=tmp/'convert.tcl'
    tcl.write_text('drc off\ncd '+str(tmp)+'\npath search [list '+str(tmp)+']\next2spice lvs\n'+''.join(f'ext2spice -o {tmp/suffix}.spice {cases[suffix]["cell"]}.ext\n' for suffix in cases)+'quit -noprompt\n')
    env=dict(os.environ,PDK_ROOT=str(pdk))
    with (tmp/'magic.log').open('w') as log:subprocess.run(['magic','-dnull','-noconsole','-rcfile',str(pdk/'sky130A/libs.tech/magic/sky130A.magicrc'),str(tcl)],cwd=tmp,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    all_pass=True
    for suffix,case in cases.items():
        for condition,ref in [('positive',suffix+'_reference.spice'),('negative',suffix+'_bad.spice')]:
            log=tmp/(suffix+'_'+condition+'.log');report=tmp/(suffix+'_'+condition+'.rpt')
            with log.open('w') as f:subprocess.run(['netgen','-batch','lvs',str(tmp/(suffix+'.spice'))+' '+case['cell'],str(tmp/ref)+' '+case['cell'],str(pdk/'sky130A/libs.tech/netgen/sky130A_setup.tcl'),str(report),'-json'],cwd=tmp,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
            text=log.read_text();final=text.rsplit('Final result:',1)[-1]
            match='Circuits match uniquely.' in final
            rejected=not match and any(s in final.lower() for s in ('do not match','mismatch','failed pin matching'))
            case[condition]={'circuits_match_uniquely':match,'wiring_fault_rejected':rejected,'report':report.name}
            all_pass &= match if condition=='positive' else rejected
            print('DEVICE_FEEDBACK_CONTROL',suffix,condition,'match',match,flush=True)
    for p in tmp.iterdir():
        if p.is_file():shutil.copyfile(p,output/p.name)
record={'source_full_GDS_run':tag,'PDK_library_sha256':hashlib.sha256(library.read_bytes()).hexdigest(),'cases':cases,'all_two_positive_and_two_wiring_fault_controls_pass':bool(all_pass),'scope':'Per-cell topology/parameter validation of the actual full-GDS extraction for warning-bearing decap_3 and diode_2. Does not waive missing SRAM internal qualification or replace final core LVS.'}
(output/'result.json').write_text(json.dumps(record,indent=2)+'\n')
assert all_pass,'Cell topology or negative control failed; warning disposition remains open'
