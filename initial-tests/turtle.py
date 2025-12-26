from pyaxidraw import axidraw


ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()

if not connected:
    print("Could not connect to plotter!")
    exit(1)

print("Drawing a circle...")
ad.goto(2, 2)
ad.pendown()

import math
radius = 1.5
steps = 36
for i in range(steps + 1):
    angle = 2 * math.pi * i / steps
    x = 2 + radius * math.cos(angle)
    y = 2 + radius * math.sin(angle)
    ad.goto(x, y)

ad.penup()


ad.goto(0, 0)


ad.disconnect()
print("Done!")