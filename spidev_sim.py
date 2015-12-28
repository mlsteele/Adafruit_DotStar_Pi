import sys, pygame
from math import sin, cos, pi
from light_geometry import Pixels

class SpiDev:
    def open(self, port, slave):
        pygame.init()
        self.width = 600
        self.screen = pygame.display.set_mode((self.width, self.width))
        self.screen.fill((0, 0, 0))
        self.ix = 0 # next pixel index

    def close(self):
        pass

    def xfer2(self, values):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()

        spacing = 10
        led_size = 5
        dotsPerRow = self.width // spacing
        windings = 9
        pixelCount = Pixels.count
        i = 0
        while i < len(values):
            frame = values[i]; i += 1
            g = values[i]; i += 1
            b = values[i]; i += 1
            r = values[i]; i += 1
            
            if frame == 0x0:
                self.ix = 0
                continue

            assert (frame & 0xe0) == 0xe0
            brightness = frame & 0x1f
            r, g, b = (c * brightness / 0x1f for c in (r, g, b))
            ix = self.ix
            self.ix += 1
            x, y = Pixels.pos(ix)
            x = x * (self.width - led_size)
            y = y * (self.width - led_size)
            pygame.draw.circle(self.screen, (r, g, b), (int(round(x)), int(round(y))), led_size)
        pygame.display.update()
