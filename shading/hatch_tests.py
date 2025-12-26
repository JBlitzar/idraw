from pyaxidraw import axidraw
import math

ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()

ad.penup()

if not connected:
    print("Could not connect to plotter!")
    exit(1)

# https://stackoverflow.com/questions/7267226/range-for-floats/67053708#67053708
def drange(start, end, increment, round_decimal_places=None):
    result = []
    if start < end:
        # Counting up, e.g. 0 to 0.4 in 0.1 increments.
        if increment < 0:
            raise Exception("Error: When counting up, increment must be positive.")
        while start <= end:
            result.append(start)
            start += increment
            if round_decimal_places is not None:
                start = round(start, round_decimal_places)
    else:
        # Counting down, e.g. 0 to -0.4 in -0.1 increments.
        if increment > 0:
            raise Exception("Error: When counting down, increment must be negative.")
        while start >= end:
            result.append(start)
            start += increment
            if round_decimal_places is not None:
                start = round(start, round_decimal_places)
    return result


def rectangle(x,y,w,h):
    ad.goto(x,y)
    ad.pendown()
    ad.goto(x+w,y)
    ad.goto(x+w,y+h)
    ad.goto(x,y+h)
    ad.goto(x,y)
    ad.penup()

def line(x1,y1,x2,y2):
    ad.goto(x1,y1)
    ad.pendown()
    ad.goto(x2,y2)
    ad.penup()

def hatch_rect(x,y,w,h,spacing):
    rectangle(x,y,w,h)
    for x1 in drange(x+spacing, x+w, spacing):
        line(x1,y,x1,y+h)
    for y1 in drange(y+spacing, y+h, spacing):
        line(x,y1,x+w,y1)


ad.penup()


ad.goto(0, 0)
for i in range(10):
    hatch_rect(0, 0 + i * 0.55, 0.5, 0.5, 0.5 / (i + 2))


ad.disconnect()
import os
os.system("axi off")
print("Done!")