# https://www.desmos.com/calculator/gt04uezfsk
# https://discord.com/channels/655972529030037504/1454513949302063308/1454548531565035738

# https://www.desmos.com/calculator/ghip0elykl


from pyaxidraw import axidraw
import numpy as np

ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()

if not connected:
    print("Could not connect to plotter!")
    exit(1)




def param(t, a, scale=1, offset=(0,0)):
    # .15\sin\left(70t+\tau a\right)\cos t-2^{a-.5\tanh\left(10-20\operatorname{mod}\left(\frac{t}{\pi},1\right)\right)\coth10+\operatorname{floor}\left(\frac{t}{\pi}\right)}
    cos = np.cos
    sin = np.sin
    pi = np.pi
    tau = 2 * pi
    floor = np.floor
    mod = np.mod
    coth = lambda x: 1 / np.tanh(x)
    tanh = np.tanh


    k = 0.15 * sin(70*t + tau * a) * cos(t) - 2 ** (a - 0.5 * tanh(10-20 * mod(t / pi, 1)) * coth(10) + floor(t / pi))
    x = k * (cos(70*t+tau * a)*cos(t))
    y = sin(t) * k
    return scale * x + offset[0], scale * y + offset[1]

ad.goto(5.5, 4.25)
ad.pendown()
ad.options.speed_pendown = 100


steps = 1_000_000
a = 1.52
t_values = np.linspace(-np.pi * a - 2 * np.pi, -np.pi * a + 3 * 2 * np.pi, steps)

ad.pendown()
px, py = 0, 0
for t in t_values:
    # print(t, k, f(t, k))
    x, y = param(t, a, scale=0.5, offset=(5.5, 4.25))
    if (px - x)**2 + (py - y)**2 > (0.01) ** 2:
        ad.goto(x, y)
        px, py = x, y


ad.penup()


ad.goto(0, 0)


ad.disconnect()
print("Done!")