from pathlib import Path
import hashlib,json,struct,zlib,sys
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/"scripts"))
from encode_image import encode
h=json.loads((R/"source_identity.json").read_text(encoding="utf8"))
for p,digest in h.items():
 assert hashlib.sha256((R/p).read_bytes()).hexdigest()==digest,p
for data in [b"",b"\x00",bytes(16388)]:
 try:encode(data)
 except ValueError:pass
 else:raise AssertionError("invalid image accepted")
for n in [1,4096]:
 data=bytes((k&255 for k in range(n*4)))
 packet=encode(data)
 assert packet[:4]==b"FV\x01\x00"
 assert struct.unpack("<H",packet[4:6])[0]==n
 assert packet[6:-4]==data
 assert struct.unpack("<I",packet[-4:])[0]==zlib.crc32(data)
words=[int(s,16) for s in (R/"programs/gate_program.mem").read_text().split()]
packet=encode(b"".join(struct.pack("<I",v) for v in words))
assert packet==bytes(int(s,16) for s in (R/"programs/gate_packet.hex").read_text().split())
assert b"readmemh" not in (R/"rtl/fault_v_memory.sv").read_bytes()
net=(R/"mapped_top.v").read_text()
assert net.count("sky130_sram_2kbyte_1rw1r_32x512_8 ")==18
assert all(x not in net for x in ["RAMB18E1","DSP48E1"])
assert len(list((R/"programs").glob("stream_*.expected")))==124
print("PASS source hashes, packet boundaries/CRC, gate fixture, 18 macros and 124 integration fixtures.")
