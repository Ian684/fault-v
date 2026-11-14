"""PYNQ Python 3.6 compatible; run as root. Validate identity before PL load."""
import hashlib,json,time
from pathlib import Path
from pynq import Overlay,MMIO
from pynq.ps import Clocks
root=Path(__file__).resolve().parent
identity=json.loads((root/'fpga_identity.json').read_text())
for name in ['fault_v_extension_a.bit','fault_v_extension_a.hwh']:
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=identity[name]:raise RuntimeError('Image identity mismatch')
overlay=Overlay(str(root/'fault_v_extension_a.bit'))
clock=float(Clocks.fclk0_mhz)
if abs(clock-50)>0.01:raise RuntimeError('Unexpected clock')
uart=MMIO(0x42C00000,0x1000);control=MMIO(0x41200000,0x1000)
expected=b'DSP OK\r\n';runs=[]
print('ARM loaded extension A overlay; FCLK0={} MHz'.format(clock),flush=True)
for round_id in range(1,4):
 control.write(0,0);time.sleep(0.03);uart.write(12,3);control.write(0,1)
 received=bytearray();errors=0;deadline=time.monotonic()+5;debug=0
 while time.monotonic()<deadline:
  status=uart.read(8);errors|=status&0xe0
  if status&1:
   received.append(uart.read(0)&255)
   if len(received)>len(expected):raise RuntimeError('Extra UART bytes')
  else:
   debug=control.read(8)
   if len(received)==len(expected) and debug&4:break
   time.sleep(0.0002)
 status=uart.read(8);errors|=status&0xe0
 if status&1:raise RuntimeError('FIFO not drained')
 if bytes(received)!=expected or errors or debug!=0x1205:raise RuntimeError('Board result mismatch')
 runs.append(dict(run=round_id,uart_hex=received.hex(),uart_errors=errors,debug=debug,status=debug&3,halt_cause=(debug>>9)&15))
 print('PASS EXTENSION A FPGA run={} bytes={} status={} halt_cause={}'.format(round_id,len(received),debug&3,(debug>>9)&15),flush=True)
result=dict(clock_mhz=clock,runs=runs,image_sha256={k:identity[k] for k in ['fault_v_extension_a.bit','fault_v_extension_a.hwh']},
 physical_led_observation=None,physical_btn0_observation=None,physical_benchmark_run=False)
(root/'board_result.json').write_text(json.dumps(result,indent=2))
print('ALL 3 EXTENSION A FPGA RUNS PASSED; 24 RECEIVED BYTES',flush=True)
