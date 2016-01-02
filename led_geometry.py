# from functools import lru_cache
from math import sin, cos, pi
import yaml

# source: http://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/
def memoize(f):
  class memodict(dict):
      __slots__ = ()
      def __missing__(self, key):
          self[key] = ret = f(key)
          return ret
  return memodict().__getitem__

with open('geometry.yaml') as f:
    CONFIG = yaml.safe_load(f)

class Pixel(object):
    def __init__(self, index):
        self.index = index

    @property
    def angle(self):
        return PixelAngle.angle(self.index)

    @property
    def radius(self):
        return PixelStrip.radius(self.index)

    def angle_from(self, angle):
        d = abs(self.angle - angle)
        return min(d % 360, -d % 360)

class PixelStrip(object):
    count = CONFIG['pixels']['count']

    # Iterates over pixels, returning the same Flyweight each time.
    @staticmethod
    def pixels():
        pixel = Pixel(0)
        while pixel.index < PixelStrip.count:
            yield pixel
            pixel.index += 1

    @staticmethod
    def pixels_near_angle(angle):
        a0 = None
        da0 = None
        for pixel in PixelStrip.pixels():
            a = pixel.angle_from(angle)
            if a0 is not None:
                da = a - a0
                if da0 is not None and da0 <= 0 and da >= 0:
                    ix = pixel.index
                    if a0 < a: ix -= 1
                    yield Pixel(ix)
                da0 = da
            a0 = a

    @staticmethod
    def pixels_within_angles(angle, band_width=0):
        half_band = band_width / 2.0
        for pixel in PixelStrip.iter():
            if abs(pixel.angle_from(angle)) < half_band:
                yield pixel

    @staticmethod
    def angle(index):
        return PixelAngle.angle(index)

    @staticmethod
    def radius(index):
        return 1 - index / float(PixelStrip.count)

    @staticmethod
    def pos(index):
        angle = PixelStrip.angle(index) * pi / 180
        radius = PixelStrip.radius(index)
        x = 0.5 + radius * cos(angle) / 2.0
        y = 0.5 + radius * sin(angle) / 2.0
        return (x, y)

class PixelAngle(object):
    # Map from pixel indices to angles in degrees.
    # The front face of the tree is 0.
    # Angles increase CCW looking from the heavens.
    REF_ANGLES = {}
    for angle, indices in CONFIG['pixels']['angles'].items():
        angle = float(angle)
        for index in indices:
            REF_ANGLES[index] = angle

    @staticmethod
    @memoize
    def angle(i):
        """Get the angle of a pixel.
        Estimate by linear approximation between two closest known neighbors.
        """
        angle = PixelAngle.REF_ANGLES.get(i)
        if angle is not None:
            return angle

        keys = PixelAngle.REF_ANGLES.keys()
        left_i = max(x for x in keys if x < i)
        right_i = min(x for x in keys if i < x)
        left_a, right_a = PixelAngle.REF_ANGLES[left_i], PixelAngle.REF_ANGLES[right_i]
        if right_a <= left_a:
            right_a += 360
        ratio = (i - left_i) / float(right_i - left_i)
        return (left_a * (1 - ratio) + right_a * ratio) % 360