from pathlib import Path
import hashlib,json,shlex,time
import xml.etree.ElementTree as ET
from remote_access import connect,ROOT
identity=json.loads((ROOT/'fpga_identity.json').read_text())
for name in ['fault_v_extension_b.bit','fault_v_extension_b.hwh']:
 if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=identity[name]:raise RuntimeError('Wrong local image')
for name,expected in identity['sources'].items():
 if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('Build sources changed')
hwh=ET.parse(ROOT/'fault_v_extension_b.hwh')
rx=next(m for m in hwh.iter('MODULE') if m.get('INSTANCE')=='serial_rx')
params={p.get('NAME'):p.get('VALUE') for p in rx.iter('PARAMETER')}
if params.get('C_BAUDRATE')!='115200' or params.get('C_S_AXI_ACLK_FREQ_HZ')!='50000000':raise RuntimeError('UART configuration')
remote='/home/xilinx/jupyter_notebooks/fault_v_extension_b_'+time.strftime('%Y%m%d_%H%M%S')
with connect() as client:
 with client.open_sftp() as sftp:
  sftp.mkdir(remote)
  for name in ['fault_v_extension_b.bit','fault_v_extension_b.hwh','fpga_identity.json','receive_on_board.py']:
   sftp.put(str(ROOT/name),remote+'/'+name)
 command='cd /tmp && sudo -S -p "" python3 '+shlex.quote(remote+'/receive_on_board.py')
 stdin,out,err=client.exec_command(command,timeout=60)
 stdin.write('xilinx\n');stdin.flush();stdin.channel.shutdown_write()
 output=out.read().decode('utf-8',errors='replace');error=err.read().decode('utf-8',errors='replace')
 code=out.channel.recv_exit_status();print(output);print(error)
 (ROOT/'logs/extension_b_fpga_uart.log').write_text(output+'\n'+error+'\nexit_code='+str(code)+'\n')
 (ROOT/'logs/deployed_directory.txt').write_text(remote+'\n')
 if code or 'ALL 3 EXTENSION B FPGA RUNS PASSED; 24 RECEIVED BYTES' not in output:raise RuntimeError('Board acceptance failed')
 with client.open_sftp() as sftp:sftp.get(remote+'/board_result.json',str(ROOT/'logs/board_verification.json'))
print('HOST RECEIVED EXTENSION B RESULTS VIA SSH/ETHERNET')
