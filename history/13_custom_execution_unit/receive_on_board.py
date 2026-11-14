"""Run as root on PYNQ; output travels to the PC over SSH/Ethernet."""
import json
import time
from pathlib import Path
from pynq import Overlay, MMIO
from pynq.ps import Clocks

root=Path(__file__).resolve().parent
overlay=Overlay(str(root/'fault_v_custom.bit'))
clock=float(Clocks.fclk0_mhz)
if abs(clock-50.0)>0.01:
    raise RuntimeError('Unexpected FCLK0 frequency: '+str(clock))
uart=MMIO(0x42C00000,0x1000)
control=MMIO(0x41200000,0x1000)
expected=b'DSP OK\r\n'
print('ARM loaded Fault-V overlay; FCLK0='+str(clock)+' MHz',flush=True)
for round_id in range(1,4):
    control.write(0,0)
    time.sleep(0.03)
    uart.write(12,3)
    control.write(0,1)
    received=bytearray()
    errors=0
    deadline=time.monotonic()+5
    debug=0
    while time.monotonic()<deadline:
        status=uart.read(8)
        errors|=status&0xe0
        if status&1:
            received.append(uart.read(0)&255)
            if len(received)>len(expected):raise RuntimeError('Unexpected extra serial bytes')
        else:
            debug=control.read(8)
            if len(received)==len(expected) and (debug&4):break
            time.sleep(0.0002)
    status=uart.read(8)
    errors|=status&0xe0
    if status&1:raise RuntimeError('Extra byte left in receive FIFO')
    if bytes(received)!=expected or errors or (debug&3)!=1 or not(debug&4) or ((debug>>9)&15)!=9:
        raise RuntimeError('UART verification failed: '+json.dumps({'hex':received.hex(),'errors':errors,'debug':debug}))
    print('PASS CUSTOM FPGA UART run={} bytes={} text={!r} status={} halt_cause={}'.format(
        round_id,len(received),bytes(received).decode('ascii'),debug&3,(debug>>9)&15),flush=True)
print('ALL 3 CUSTOM FPGA UART RUNS PASSED; 24 RECEIVED BYTES',flush=True)
