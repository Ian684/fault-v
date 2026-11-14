"""Encode a little-endian raw instruction image as the Fault-V UART boot packet."""
from pathlib import Path
import struct,zlib,argparse
def encode(payload):
 if not payload or len(payload)%4 or len(payload)>16384:
  raise ValueError("Image must contain 1..4096 whole 32-bit words")
 return b"FV\x01\x00"+struct.pack("<H",len(payload)//4)+payload+struct.pack("<I",zlib.crc32(payload))
if __name__=="__main__":
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("image",type=Path);p.add_argument("packet",type=Path)
 a=p.parse_args()
 a.packet.write_bytes(encode(a.image.read_bytes()))
