from svgpathtools import svg2paths
import numpy as np

from pyaxidraw import axidraw
import math
import time
#from fake_ad import FakeAD
import os

INK_POS = (12, 2)


ad = axidraw.AxiDraw() # FakeAD(speed=5, instant=False)

ad.interactive()

connected = ad.connect()
ad.options.model = 2
ad.options.clip_to_page = False
ad.options.pen_pos_up = 100
ad.options.pen_pos_down = 0
ad.update()


def dip():
    ad.goto(INK_POS[0], INK_POS[1])
    ad.pendown()
    ad.penup()


if not connected:
    print("Could not connect to plotter!")
    exit(1)

ad.penup()


ad.options.clip_to_page = False


ad.penup()
ad.goto(INK_POS[0], INK_POS[1])
time.sleep(1)
ad.pendown()

ad.penup()
ad.goto(0,0)
ad.disconnect()


os.system("axi off")
print("Done!")
# os.system('curl -d "done!!" ntfy.sh/jb_pp_109188f37776d45aee070634901e480c')
