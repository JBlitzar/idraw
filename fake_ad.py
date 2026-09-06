import math
import turtle


class FakeOptions:
    speed_pendown = 25; speed_penup = 75; accel = 75
    pen_pos_up = 60; pen_pos_down = 30; pen_rate_raise = 75
    pen_rate_lower = 50; pen_delay_up = 0; pen_delay_down = 0
    const_speed = False; resolution = 1; model = 1; clip_to_page = False


class FakeAD:
    SCALE = 100  # 100 pixels -> 1 inch

    def __init__(self, screensize=(1100, 1100), speed=0, instant=True):
        self.pen_is_down = False
        self.position = (0, 0)
        self.pup_travel_time = 0.0
        self.pd_travel_time = 0.0
        self.pen_op_time = 0.0
        self.updowns = 0
        self.options = FakeOptions()
        self._fake_ad_color = (0, 0, 0)
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

    @property
    def _color(self):
        return self._fake_ad_color

    @_color.setter
    def _color(self, value):
        turtle.pencolor(value)
        self._fake_ad_color = value

    def bbox(self, w, h):
        self.goto(0, 0, track=False)
        self.pendown()
        self.goto(w, 0, track=False)
        self.goto(w, h, track=False)
        self.goto(0, h, track=False)
        self.goto(0, 0, track=False)
        self.penup()

    def moveto(self, x, y):
        self.penup()
        self.goto(x, y)

    def connect(self):
        return True

    def update(self):
        return True

    def disconnect(self):
        self.screen.update()
        turtle.done()
        total = self.pup_travel_time + self.pd_travel_time + self.pen_op_time
        print(
            f"Done! \n  Pen up travel: {self.pup_travel_time:.2f} s, "
            f"Pen down travel: {self.pd_travel_time:.2f} s. \n"
            f"  Pen ops: {self.pen_op_time:.2f} s ({self.updowns}) \n"
            f"  Estimated time: {total:.2f} s"
        )

    def interactive(self):
        pass

    # Timing: mirrors pyaxidraw v3.9.6 motion.py + pen_handling.py

    def _va(self, pen_up):
        """(speed_limit in/s, accel in/s²) for pen state, matching enable_motors."""
        lim = 8.6979 if self.options.resolution == 1 else 15.0
        s = self.options.speed_penup if pen_up else self.options.speed_pendown
        s = max(1, min(200 if pen_up else 110, s))
        v = s * lim / 110
        if self.options.const_speed and not pen_up:
            v *= 0.4 if self.options.resolution == 1 else 0.25
        a = (60 if pen_up else 40) * max(1, min(110, self.options.accel)) / 100
        return v, a

    def _pen_time(self, raising):
        """Pen raise/lower time in seconds (PenLiftTiming 4th-power formula)."""
        vd = abs(self.options.pen_pos_up - self.options.pen_pos_down)
        if vd < 0.9:
            return 0
        rate = self.options.pen_rate_raise if raising else self.options.pen_rate_lower
        delay = self.options.pen_delay_up if raising else self.options.pen_delay_down
        t = int(((2.69 * vd + 45) ** 4 + (200 * vd / max(1, rate)) ** 4) ** 0.25) + delay
        return max(0, t) / 1000

    def _seg_time(self, d, vi=0, vf=0, pen_up=False):
        """Time (s) for one segment, matching compute_segment trapezoidal physics."""
        if d < 1e-12:
            return 0
        v, a = self._va(pen_up)
        if self.options.const_speed and not pen_up:
            return d / v
        vi, vf = min(vi, v), min(vf, v)
        t_acc = (v - vi) / a
        t_dec = (v - vf) / a
        d_acc = vi * t_acc + .5 * a * t_acc ** 2
        d_dec = vf * t_dec + .5 * a * t_dec ** 2
        if d > d_acc + d_dec + .025 * v and d / v > .1:
            return t_acc + (d - d_acc - d_dec) / v + t_dec  # trapezoid
        disc = 2 * vi ** 2 + 2 * vf ** 2 + 4 * a * d
        ta = (math.sqrt(max(0, disc)) - 2 * vi) / (2 * a)
        tri = ta + max(0, ta - (vf - vi) / a)  # triangle
        if vi == 0 and vf == 0 and tri < .125:
            vmax = math.sqrt(a * d)  # short-segment velocity boost (Case 3)
            t = 4 * d / vmax
            return t if t >= .0625 else d / vmax
        return tri

    def _plan_polyline(self, pts, pen_up=False):
        """[(dist, vi, vf)] per segment with GRBL cornering velocities."""
        if len(pts) < 2:
            return []
        v, a = self._va(pen_up)
        min_d = .000348 if self.options.resolution == 1 else .000696
        dists, vecs, last = [0.0], [], 0
        for i in range(1, len(pts)):
            dx, dy = pts[i][0] - pts[last][0], pts[i][1] - pts[last][1]
            d = math.sqrt(dx * dx + dy * dy)
            if d >= min_d:
                dists.append(d)
                vecs.append([dx / d, dy / d])
                last = i
        n = len(dists)
        if n < 2:
            return []
        if n < 3:
            return [(dists[1], 0, 0)]
        vels, accel_d = [0.0], v * v / (2 * a)
        for i in range(1, n - 1):
            vp = vels[-1]
            vm = v if dists[i] > accel_d else min(v, math.sqrt(vp * vp + 2 * a * dists[i]))
            cos = -(vecs[i - 1][0] * vecs[i][0] + vecs[i - 1][1] * vecs[i][1])
            rf = math.sqrt(max(0, (1 - cos) / 2))
            denom = 1 - rf
            vj = math.sqrt(a * (.002 * rf / denom if denom > .0001 else 100000))
            vels.append(min(vm, vj))
        vels.append(0.0)
        for j in range(1, n):
            i = n - j
            if vels[i - 1] > vels[i] and dists[i] > 0:
                vels[i - 1] = min(vels[i - 1], math.sqrt(vels[i] ** 2 + 2 * a * dists[i]))
        return [(dists[i + 1], vels[i], vels[i + 1]) for i in range(n - 1)]

    def goto(self, x, y, track=True):
        old = self.position
        self.position = (x, y)
        d = math.sqrt((x - old[0]) ** 2 + (y - old[1]) ** 2)
        if track:
            if self.pen_is_down:
                self.pd_travel_time += self._seg_time(d, pen_up=False)
            else:
                self.pup_travel_time += self._seg_time(d, pen_up=True)
        turtle.goto(x * self.SCALE, self.screensize[1] - y * self.SCALE)

    def draw_path(self, points):
        self.polyline(points)

    def polyline(self, points, *args, **kwargs):
        pen_down = kwargs.pop("pen_down", True)
        if not points:
            return
        self.penup()
        x0, y0 = points[0]
        self.goto(x0, y0)
        if pen_down:
            self.pendown()
        if pen_down and len(points) > 2:
            for dist, vi, vf in self._plan_polyline(points, pen_up=False):
                self.pd_travel_time += self._seg_time(dist, vi, vf, pen_up=False)
            for x, y in points[1:]:
                self.position = (x, y)
                turtle.goto(x * self.SCALE, self.screensize[1] - y * self.SCALE)
        else:
            for x, y in points[1:]:
                self.goto(x, y)

    def penup(self):
        if not self.pen_is_down:
            return
        self.pen_is_down = False
        turtle.penup()
        self.pen_op_time += self._pen_time(True)
        self.updowns += 1

    def pendown(self):
        if self.pen_is_down:
            return
        self.pen_is_down = True
        turtle.pendown()
        self.pen_op_time += self._pen_time(False)
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
