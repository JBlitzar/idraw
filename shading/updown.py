from pyaxidraw import axidraw
import numpy as np
from tqdm import trange, tqdm

ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()

if not connected:
    print("Could not connect to plotter!")
    exit(1)

def downSet(d):
    ad.options.pen_pos_down = d
    ad.update()
def rectangle(x,y,w,h):
    ad.goto(x,y)
    ad.pendown()
    ad.goto(x+w,y)
    ad.goto(x+w,y+h)
    ad.goto(x,y+h)
    ad.goto(x,y)
    ad.penup()

def line(x1,y1,x2,y2):
    ad.penup()
    ad.goto(x1,y1)
    ad.pendown()
    ad.goto(x2,y2)
    ad.penup()


ad.penup()


ad.goto(0, 0)

ad.goto(0, 0)
ad.penup()

for idx, amt in enumerate(tqdm(np.arange(50, 0, -5))):
    downSet(amt)
    line(idx * 0.2, 0, idx * 0.2, 4)

downSet(30)

ad.disconnect()
print("Done!")
import os
os.system("axi off")