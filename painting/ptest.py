from pyaxidraw import axidraw
import math
import time
INK_POS = (12, 2)



ad = axidraw.AxiDraw()

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
    
        

def circle(x,y,r=2,steps=50):
    ad.goto(x + r, y)
    ad.pendown()

    for i in range(steps + 1):
        angle = 2 * math.pi * i / steps
        px = x + r * math.cos(angle)
        py = y + r * math.sin(angle)
        ad.goto(px, py)
    ad.penup()

def vert(x,y,length=2):
    ad.goto(x,y)
    ad.pendown()
    ad.goto(x,y+length)
    ad.penup()

def vert_rev(x,y,length=2):
    ad.goto(x,y+length)
    ad.pendown()
    ad.goto(x,y)
    ad.penup()




if not connected:
    print("Could not connect to plotter!")
    exit(1)

ad.penup()



ad.options.clip_to_page = False

# ad.goto(2, 2)
# ad.pendown()

# for i in range(4):
#     dip()

#     vert(i+1.7,4.1,i+1)
#     dip()
#     vert_rev(i+1.7,4.1,i+1)
#     time.sleep(1)

dip()
for i in range(5):
    vert(i+6, 6, 1)


ad.penup()
ad.goto(0, 0)
ad.disconnect()
import os

os.system("axi off")
print("Done!")
os.system('curl -d "done!!" ntfy.sh/jb_pp_109188f37776d45aee070634901e480c')
