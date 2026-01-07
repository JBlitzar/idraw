import turtle


class FakeAD:
    SCALE = 100  # 100 pixels -> 1 inch

    def __init__(self, screensize=(1100, 1100), speed=0, instant=True):
        self.pen_is_down = False
        self.position = (0, 0)

        screen = turtle.Screen()
        screen.screensize(*screensize)
        screen.setworldcoordinates(0, 0, screensize[0], screensize[1])
        self.screen = screen
        self.screensize = screensize
        turtle.penup()
        turtle.speed(speed)
        self.goto(0, 0)
        if instant:
            screen.tracer(0, 0)
            turtle.hideturtle()

        self.bbox(11, 8.5)
        self.bbox(8.5, 11)

    def bbox(self, w, h):
        self.goto(0, 0)
        self.pendown()
        self.goto(w, 0)
        self.goto(w, h)
        self.goto(0, h)
        self.goto(0, 0)
        self.penup()

    def connect(self):
        return True

    def disconnect(self):
        self.screen.update()
        turtle.done()

    def interactive(self):
        pass

    def goto(self, x, y):
        self.position = (x, y)
        # print(self.screensize[1] - y * self.SCALE)
        turtle.goto(x * self.SCALE, self.screensize[1] - y * self.SCALE)

    def penup(self):
        self.pen_is_down = False
        turtle.penup()

    def pendown(self):
        self.pen_is_down = True
        turtle.pendown()


def main():
    ad = FakeAD()
    ad.interactive()
    connected = ad.connect()

    if not connected:
        print("Could not connect to plotter!")
        exit(1)

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


if __name__ == "__main__":
    main()
