import hid
import parser

class reader():
    def __init__(self):
        self.dev = hid.device()
        self.dev.open(987, 5)
        self.dev.set_nonblocking(1)

        # Wake up the AIM Base
        self.dev.write([3, 3] + [0] * 62)
        self.dev.close()
        self.dev.open(987, 6)
        self.dev.set_nonblocking(1)

        self.parser = parser.AimParser()

    def getData(self) -> list[parser.Packet]:
        self.dev.write([0x03, 0x12] + [0] * 62)
        data = self.dev.read(64)
        packets = self.parser.parse_transmission(bytes(data))
        return packets

