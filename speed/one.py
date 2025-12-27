from pyaxidraw import axidraw


ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()

if not connected:
    print("Could not connect to plotter!")
    exit(1)

ad.pendown()

import numpy as np

for idx, speed in enumerate(np.linspace(100, 10, 10)):
    ad.options.speed_pendown = speed
    ad.options.speed_penup = speed
    ad.update()
    ad.penup()
    ad.goto(0, idx * 0.1)
    ad.pendown()
    ad.goto(3, idx * 0.1)
    ad.penup()

ad.penup()


ad.goto(0, 0)


ad.disconnect()
print("Done!")