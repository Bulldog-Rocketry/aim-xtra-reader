
import time

import hid

dev = hid.device()
dev.open(987, 5)
dev.set_nonblocking(1)

# Wake up the AIM Base
dev.write([3, 3] + [0] * 62)
while True:
    d = dev.read(64)
    if d:
        print(d)
    else:
        break

