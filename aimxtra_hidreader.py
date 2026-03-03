import time

import hid
import aim_parser

parser = aim_parser.AimParser(aim_parser.PacketStructureManager())

dev = hid.device()
# for some reason the info changes so
time.sleep(0.5)
dev.close()
dev.open(987, 6)
dev.set_nonblocking(1)
oldData = []
# for some reason we have to wake it up again! yay
dev.write([3, 3] + [0] * 62)
while True:
    dev.write([0x03, 0x12] + [0] * 62)
    d = dev.read(64)
    if d != oldData:
        packets = []
        # packets = parser.parse_transmission(bytes(d))
        # print(packets)
        print(d)
    oldData = d

