from pathlib import Path
import hashlib
import base64
import paramiko

ROOT = Path(__file__).resolve().parent
def connect():
    client = paramiko.SSHClient()
    known = ROOT / 'known_hosts'
    if known.exists(): client.load_host_keys(str(known))
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.2.99', username='xilinx', password='xilinx',
                   timeout=8, auth_timeout=8, look_for_keys=False, allow_agent=False)
    client.save_host_keys(str(known))
    return client

if __name__ == '__main__':
    with connect() as client:
        key=client.get_transport().get_remote_server_key()
        print('SSH host SHA256:'+base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip('='))
        command="uname -a; python3 -c 'import pynq; print(\"PYNQ\",pynq.__version__); print(\"PYNQ path\",pynq.__file__)'; ls /usr/local/share/pynq-venv/bin/python* /usr/local/lib/python*/dist-packages/pynq/overlays/base/base.hwh /usr/local/share/pynq-venv/lib/python*/site-packages/pynq/overlays/base/base.hwh 2>/dev/null"
        _,out,err=client.exec_command(command,timeout=15)
        print(out.read().decode());print(err.read().decode())
