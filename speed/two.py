from pyaxidraw import axidraw


ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()

if not connected:
    print("Could not connect to plotter!")
    exit(1)

ad.pendown()

import numpy as np
import time

for idx, wait in enumerate(np.arange(0, 2, 0.1)):
    ad.penup()
    ad.goto(0,1)
    ad.pendown()
    ad.goto(0.1,1)
    ad.penup()
    ad.goto(idx * 0.1, 0)
    ad.pendown()
    time.sleep(wait)

    ad.penup()

ad.penup()


ad.goto(0, 0)


ad.disconnect()
print("Done!")