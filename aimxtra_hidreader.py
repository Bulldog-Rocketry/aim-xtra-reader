import time

import hid
import aim_parser
# import packets

parser = aim_parser.AimParser()

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
        print([(hex(x) if 1 < x < 21 else str(x)) for x in d])
        packets = []
        packets = parser.parse_transmission(bytes(d))
        print(packets)
        # for packet in packets:
        #     print(packet.field_data[2])
        # print(d)
    oldData = d

