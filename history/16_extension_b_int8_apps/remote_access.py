from pathlib import Path
import os,getpass,paramiko
ROOT=Path(__file__).resolve().parent
def connect():
 client=paramiko.SSHClient()
 client.load_host_keys(str(ROOT/'known_hosts'))
 client.set_missing_host_key_policy(paramiko.RejectPolicy())
 password=os.environ.get('FAULT_V_SSH_PASSWORD') or getpass.getpass('Z2 SSH password: ')
 client.connect(os.environ.get('FAULT_V_SSH_HOST','192.168.2.99'),username=os.environ.get('FAULT_V_SSH_USER','xilinx'),password=password,timeout=8,look_for_keys=False,allow_agent=False)
 return client
