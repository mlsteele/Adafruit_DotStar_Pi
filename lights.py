#!/usr/bin/python

import time
import colorsys
import random
from math import sin, cos
import apa102

NUMPIXELS = 900 # Number of LEDs in strip

strip = apa102.APA102(NUMPIXELS)

RED   = 0xff0000
GREEN = 0x00ff00
BLUE  = 0x0000ff
BLACK = 0x000000
WHITE = 0xffffff

class PixelAngle(object):
    # Map from pixel indices to angles in degrees.
    # The front face of the tree is 0.
    # Angles increase CCW looking from the heavens.
    REF_ANGLES = {
        0: 180,
        120: 0,
        336: 0,
        527: 0,
        648: 0,
        737: 0,
        814: 0,
        862: 0,
        876: 0,
        886: 0,
        NUMPIXELS: 180,
    }

    cache = {}

    @staticmethod
    def angle(i):
        """Get the angle of a pixel.
        Estimate by linear approximation between two closest known neighbors.
        """
        if i in PixelAngle.cache:
            return PixelAngle.cache[i]

        if i in PixelAngle.REF_ANGLES.keys():
            return float(PixelAngle.REF_ANGLES[i])

        left_i, right_i = PixelAngle.closest(i)
        left_a, right_a = PixelAngle.REF_ANGLES[left_i], PixelAngle.REF_ANGLES[right_i]
        if right_a <= left_a:
            right_a += 360
        ratio = (i - left_i) / float(right_i - left_i)
        predicted = (left_a * (1 - ratio) + right_a * ratio)
        predicted %= 360

        PixelAngle.cache[i] = predicted
        return predicted

    @staticmethod
    def closest(i):
        """Get the closest known neighbor(s) of a pixel."""
        items = PixelAngle.REF_ANGLES.keys()
        assert i not in items
        lesser = [x for x in items if x < i]
        greater = [x for x in items if x > i]
        left_i = sorted(lesser, key=lambda x: abs(x - i))[0]
        right_i = sorted(greater, key=lambda x: abs(x - i))[0]
        return (left_i, right_i)

def angdist(x, y):
    """Minimum distance between two angles (in degrees)."""
    x = (x + 360) % 360
    y = (y + 360) % 360
    return min([abs((x - y) % 360), abs((y - x) % 360)])

def bound(x):
    return x % NUMPIXELS

class Profiler:
    def __init__(self, name="_"):
        self.name = name

    # Thanks to:
    # http://preshing.com/20110924/timing-your-code-using-pythons-with-statement/
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start
        print "profiled {}: {:.0f} (ms)".format(self.name, self.interval * 1000)

class Color(object):
    @staticmethod
    def hex_to_rgb(hex_color):
        return ((hex_color & 0xff0000) >> 16,
            (hex_color & 0x00ff00) >> 8,
            (hex_color & 0x0000ff))

    @staticmethod
    def rgb_to_hex(r, g, b):
        r, g, b = (int(255 * c) for c in (r, g, b))
        return (r << 16) | (g << 8) | b

    @staticmethod
    def hex_to_hsv(hex_color):
        return colorsys.rgb_to_hsv(*Color.hex_to_rgb(hex_color))

    @staticmethod
    def hsv_to_hex(h, s, v):
        return Color.rgb_to_hex(*colorsys.hsv_to_rgb(h, s, v))

class Snake(object):
    def __init__(self, head=0, speed=1):
        self.head = int(head)
        self.head_f = float(int(head))
        self.length = 10
        self.speed = speed
        self.hue_offset = head

    def step(self):
        self.head_f = bound(self.head_f + self.speed)
        self.head = bound(int(self.head_f))

    def show(self):
        for i in xrange(self.length):
            h, s, v = ((self.hue_offset+self.head+i)/float(NUMPIXELS)*2.), 1, i / float(self.length) / 2
            strip.setPixelRGB(bound(self.head + i), Color.hsv_to_hex(h, s, v))

class EveryNth(object):
    def __init__(self, speed=1, factor=0.02):
        self.num = int(NUMPIXELS * factor)
        self.skip = int(NUMPIXELS / self.num)
        self.speed = speed
        self.offset = 0

    def step(self):
        self.offset += self.speed
        self.offset %= self.skip

    def show(self):
        for i in xrange(self.num):
            x = bound(int(self.offset + self.skip * i))
            strip.setPixelRGB(x, Color.hsv_to_hex(0, 0, 1))

class Sparkle(object):
    def step(self):
        pass

    def show(self):
        for i in xrange(NUMPIXELS):
            if random.random() > 0.999:
                strip.setPixelRGB(i, Color.hsv_to_hex(random.random(), 0.3, random.random()))

class Predicate(object):
    def __init__(self, predicate):
        self.f = predicate

    def step(self):
        pass

    def show(self):
        for i in xrange(NUMPIXELS):
            if self.f(i):
                strip.setPixelRGB(i, Color.hsv_to_hex(0, 0, 0.04))

N_SNAKES = 15

sprites = []
sprites.extend(Snake(head=i*(NUMPIXELS / float(N_SNAKES)), speed=(1+(0.3*i))*random.choice([1, -1])) for i in xrange(N_SNAKES))
sprites.append(EveryNth(factor=0.1))
sprites.append(EveryNth(factor=0.1, speed=-0.2))
sprites.append(Sparkle())

# Playing with angles.
# angle_offset = lambda: time.time() * 45 % 360
# angle_offset = lambda: sin(time.time()) * 55
# angle_width = lambda: 10
# sprites.append(Predicate(lambda x: angdist(PixelAngle.angle(x), angle_offset()) <= angle_width()))

print "Starting."
try:
    last_frame_t = time.time()
    ideal_frame_delta_t = 1.0 / 60
    while True:
        frame_t = time.time()
        delta_t = frame_t - last_frame_t
        if delta_t < ideal_frame_delta_t:
            time.sleep(ideal_frame_delta_t - delta_t)
        # else:
        #     print "Frame lagging. Time to optimize."
        last_frame_t = time.time()

        strip.clear()

        for sprite in sprites:
            sprite.show()
            sprite.step()

        strip.show()

finally:
    strip.cleanup()
