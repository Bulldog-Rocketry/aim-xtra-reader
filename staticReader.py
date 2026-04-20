import packets
import aim_parser

parser = aim_parser.AimParser()

for packet in packets.packets:
    # print(packet)
    print([hex(item) for item in packet])
    parsed = parser.parse_transmission(bytes(packet))
    # print()
    # print(parsed)
    for item in parsed:
        print("item: ")
        print(item)
    print()

