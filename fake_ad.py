import math
import turtle


class FakeOptions:
    pass


class FakeAD:
    SCALE = 100  # 100 pixels -> 1 inch

    PEN_UPDOWN_TIME = 0.1318  # seconds per action

    def __init__(self, screensize=(1100, 1100), speed=0, instant=True):
        self.pen_is_down = False
        self.position = (0, 0)

        self.pup_travel_time = 0
        self.pd_travel_time = 0



        self.updowns = 0

        self.options = FakeOptions()  # dummy options object

        screen = turtle.Screen()
        screen.screensize(*screensize)
        screen.setworldcoordinates(0, 0, screensize[0], screensize[1])
        self.screen = screen
        self.screensize = screensize
        turtle.penup()
        turtle.speed(speed)
        self.goto(0, 0, track=False)
        if instant:
            screen.tracer(0, 0)
            turtle.hideturtle()

        self.bbox(11, 8.5)
        self.bbox(8.5, 11)

    def bbox(self, w, h):
        self.goto(0, 0, track=False)
        self.pendown()
        self.goto(w, 0, track=False)
        self.goto(w, h, track=False)
        self.goto(0, h, track=False)
        self.goto(0, 0, track=False)
        self.penup()

    def connect(self):
        return True

    def update(self):
        return True

    def disconnect(self):
        self.screen.update()
        turtle.done()
        total_time = self.pup_travel_time + self.pd_travel_time
        time_est = total_time + self.updowns * self.PEN_UPDOWN_TIME
        print(
            f"Done! \n  Pen up travel: {self.pup_travel_time:.2f} s, Pen down travel: {self.pd_travel_time:.2f} s. \n  Pen up/downs: {self.updowns} \n  Estimated time: {time_est} s"
        )

    def _dst2time(self, distance):
        # see https://www.desmos.com/calculator/ntddi7okrk
        # The cutoffs at the magic numbers 0.25 and 1 are in fact baked in to the firmware
        # Other parameters are obtained empricially through regression
        if distance < 0.25:
            # there is a physics-based justification for using a square root curve here
            return 2 * math.sqrt(distance / 11.2686403048)
        elif distance < 1:
            # linear fit for mid distances, seems to work
            return 0.193114285714 * distance + 0.0836923809524
        else:
            # there is a physics-based justification for using a linear fit (+ a constant) here
            return 0.132666839038 * distance + 0.134487621013

    def interactive(self):
        pass

    def goto(self, x, y, track=True):
        old = self.position
        self.position = (x, y)

        distance = ((x - old[0]) ** 2 + (y - old[1]) ** 2) ** 0.5
        if track:
            if self.pen_is_down:
                self.pd_travel_time += self._dst2time(distance)
            else:
                self.pup_travel_time += self._dst2time(distance)
        # print(self.screensize[1] - y * self.SCALE)
        turtle.goto(x * self.SCALE, self.screensize[1] - y * self.SCALE)

    def penup(self):
        self.pen_is_down = False
        turtle.penup()
        self.updowns += 1

    def pendown(self):
        self.pen_is_down = True
        turtle.pendown()
        self.updowns += 1


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
