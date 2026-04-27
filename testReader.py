import testPackets
import parser


for packet in testPackets.packets:
    # print(packet)
    print([hex(item) for item in packet])
    parsed = parser.parse_transmission(bytes(packet))
    # print()
    # print(parsed)
    for item in parsed:
        print("item: ")
        print(item)
    print()

class reader():
    def __init__(self):
        self.parser = parser.AimParser()
        self.packetIndex: int = 0

    def getData(self) -> list[parser.Packet]:
        if self.packetIndex < len(testPackets.packets):
            data = testPackets.packets[self.packetIndex]
        else:
            data = []
        packets = self.parser.parse_transmission(bytes(data))
        return packets


