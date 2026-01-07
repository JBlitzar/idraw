from pyaxidraw import axidraw
import time

ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()

if not connected:
    print("Could not connect to plotter!")
    exit(1)

ad.penup()


def time_harness(fn, n=10):
    times = []
    for _ in range(n):
        start = time.time()
        fn()
        end = time.time()
        times.append(end - start)
        ad.penup()
        ad.goto(0, 0)

    avg_time = sum(times) / n
    return avg_time


print("Going ten inches 10x to the right...")


def go_right():
    ad.goto(10, 0)


avg_time = time_harness(go_right) / 10
print(f"Average time/inch: {avg_time:.4f} s")


print("Going ten inches diagonally 10x...")


def go_diag():
    ad.goto(10, 10)


avg_time = time_harness(go_diag) / (10 * (2**0.5))
print(f"Average time/inch: {avg_time:.4f} s")

print("Going ten inches 10x down...")


def go_down():
    ad.goto(0, -10)


avg_time = time_harness(go_down) / 10
print(f"Average time/inch: {avg_time:.4f} s")

print("Pen down/up 10x")


def pen_down_up():
    ad.pendown()
    ad.penup()


avg_time = time_harness(pen_down_up) / 2
print(f"Average time/motion: {avg_time:.4f} s")


ad.penup()
ad.goto(0, 0)


ad.disconnect()
print("Done!")
