from pyaxidraw import axidraw
import math


ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()


def rect(x, y, width, height):
    ad.goto(x, y)
    ad.pendown()
    ad.goto(x + width, y)
    ad.goto(x + width, y + height)
    ad.goto(x, y + height)
    ad.goto(x, y)
    ad.penup()


if not connected:
    print("Could not connect to plotter!")
    exit(1)

ad.penup()

rect(1, 2, 3, 4)


ad.penup()
ad.goto(0, 0)


ad.disconnect()
print("Done!")
