import json

from aim_parser import AimParser
from aim_parser import delimiter_packet_length as dpl

parser = AimParser()

with open("packets.json", "r") as f:
    packets = json.load(f)

for packet in packets:
    # print([(f"0x{x:x}: {dpl.get(x, '??')}" if 1 < x < 21 else str(x)) for x in packet])
    print(json.dumps([(f"0x{x:x}: {dpl.get(x, '??')}" if x in dpl else str(x)) for x in packet], indent=2))
    print(parser.parse_transmission(bytes(packet)))
