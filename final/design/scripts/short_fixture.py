from pathlib import Path
import struct,zlib
R=Path(__file__).resolve().parent.parent
payload=struct.pack("<I",0x00100073)
packet=b"FV\x01\x00"+struct.pack("<H",1)+payload+struct.pack("<I",zlib.crc32(payload))
assert len(packet)==14
(R/"programs/short_packet.hex").write_text("".join(f"{v:02x}\n" for v in packet))
