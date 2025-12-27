# https://www.desmos.com/calculator/ghip0elykl


from pyaxidraw import axidraw
import numpy as np

ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()

if not connected:
    print("Could not connect to plotter!")
    exit(1)


def f(t, k):
    return  k * ((1 + np.sin(5*t) * np.cos(np.e * t) / 4) ** k)

def param(t, k, scale=1, offset=(0,0)):
    r = f(t, k)
    x = scale * r * np.cos(t) / 11 + offset[0]
    y = scale * r * np.sin(t) / 11 + offset[1]
    return x, y

ad.goto(5.5, 4.25)
ad.pendown()
k_values = np.arange(0.1, 3, 0.1)
for k in k_values:
    steps = 500
    t_values = np.linspace(0, 2 * np.pi, steps)
    flag = False
    ad.penup()
    for t in t_values:
        # print(t, k, f(t, k))
        x, y = param(t, k, 8, (5.5, 4.25))

        ad.goto(x, y)
        if not flag:
            ad.pendown()
            flag = True


ad.penup()


ad.goto(0, 0)


ad.disconnect()
print("Done!")