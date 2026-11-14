from remote_access import connect, ROOT
import shlex
import time
import xml.etree.ElementTree as ET
hwh=ET.parse(ROOT/"fault_v_network.hwh")
rx=next(m for m in hwh.iter("MODULE") if m.get("INSTANCE")=="serial_rx")
params={p.get("NAME"):p.get("VALUE") for p in rx.iter("PARAMETER")}
if params.get("C_BAUDRATE")!="115200" or params.get("C_S_AXI_ACLK_FREQ_HZ")!="50000000":
    raise RuntimeError("The bitstream/HWH must be the verified 50 MHz UART version")

remote='/home/xilinx/jupyter_notebooks/fault_v_network_'+time.strftime('%Y%m%d_%H%M%S')
with connect() as client:
    with client.open_sftp() as sftp:
        sftp.mkdir(remote)
        for name in ['fault_v_network.bit','fault_v_network.hwh','receive_on_board.py','Fault_V_Network.ipynb']:
            sftp.put(str(ROOT/name),remote+'/'+name)
    command='cd /tmp && sudo -S -p "" python3 '+shlex.quote(remote+'/receive_on_board.py')
    stdin,out,err=client.exec_command(command,timeout=60)
    stdin.write('xilinx\n');stdin.flush();stdin.channel.shutdown_write()
    output=out.read().decode('utf-8',errors='replace')
    error=err.read().decode('utf-8',errors='replace')
    code=out.channel.recv_exit_status()
    print(output);print(error)
    (ROOT/'logs/network_uart.log').write_text(output+'\n'+error+'\nexit_code='+str(code)+'\n')
    (ROOT/'logs/deployed_directory.txt').write_text(remote+'\n')
    if code or 'ALL 3 NETWORK UART RUNS PASSED; 36 RECEIVED BYTES' not in output:
        raise RuntimeError('Board UART/network verification did not pass')
    print('HOST RECEIVED BOARD OUTPUT VIA SSH/ETHERNET')

