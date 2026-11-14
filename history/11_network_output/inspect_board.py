from remote_access import connect, ROOT
with connect() as client:
    command="cd /tmp && sudo -S -p '' python3 -c 'import pynq; print(\"PYNQ\",pynq.__version__); print(pynq.__file__)'"
    stdin,out,err=client.exec_command(command,timeout=15)
    stdin.write('xilinx\n');stdin.flush();stdin.channel.shutdown_write()
    print(out.read().decode());print(err.read().decode())
    with client.open_sftp() as sftp:
        sftp.get('/usr/local/lib/python3.6/dist-packages/pynq/overlays/base/base.hwh', str(ROOT/'base_reference.hwh'))
import xml.etree.ElementTree as ET
tree=ET.parse(ROOT/'base_reference.hwh')
ps=[node for node in tree.iter('MODULE') if node.get('MODTYPE')=='processing_system7']
if len(ps)!=1:raise RuntimeError('Expected one processing_system7 in board reference')
params={p.get('NAME'):p.get('VALUE') for p in ps[0].iter('PARAMETER') if p.get('NAME','').startswith('PCW_')}
print('PS preset parameters:',len(params))
(ROOT/'ps_preset.tcl').write_text('set ps_preset [list \\\n'+''.join(' CONFIG.'+k+' {'+v+'} \\\n' for k,v in sorted(params.items()))+']\n')
