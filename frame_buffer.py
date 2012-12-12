
from pygame import Surface, Rect, display, time, transform
from pygame import FULLSCREEN, DOUBLEBUF, HWSURFACE, OPENGL, RESIZABLE, NOFRAME

class FrameBuffer(Surface):
    instance = None

    def __init__(self, disp_res, fb_res, flags=HWSURFACE|DOUBLEBUF|RESIZABLE,
                 fps=60, scale_method='pixelperfect', scale_smooth=False):
        screen = display.set_mode(disp_res, flags)
        Surface.__init__(self, fb_res, flags)
        self._scale_method = scale_method
        self._scale_smooth = scale_smooth
        self.compute_target_subsurf()
        self._update_rects = []

        self._clock = time.Clock()
        self._fps = fps
        self._lag = 0
        self._tdelta = 0

        if FrameBuffer.instance is None:
            FrameBuffer.instance = self

    def compute_target_subsurf(self):
        screen = display.get_surface()
        self_rect = self.get_rect()
        disp_rect = screen.get_rect()

        if self._scale_method == 'pixelperfect':
            factor = min( float(disp_rect.w)/self_rect.w,
                          float(disp_rect.h)/self_rect.h )
            if factor >= 1.0:  factor = int(factor)
            w = int(factor*self_rect.w)
            h = int(factor*self_rect.h)
            r = Rect(0,0,w,h)
            r.center = disp_rect.center
            self._target = screen.subsurface(r)
        elif self._scale_method == 'scale2x':
            factor = min( disp_rect.w//self_rect.w, disp_rect.h//self_rect.h )
            pow2 = 0
            while (2<<pow2) <= factor:  pow2 += 1  # yes, 2<<pow2.
            factor = (1<<pow2)
            w = factor*self_rect.w
            h = factor*self_rect.h
            r = Rect(0,0,w,h)
            r.center = disp_rect.center
            if disp_rect.contains(r):
                self._target = screen.subsurface(r)
            else:
                self._target = screen
        elif self._scale_method == 'proportional':
            self._target = screen.subsurface(self_rect.fit(disp_rect))
        elif self._scale_method == 'stretch':
            self._target = screen
        else: #elif self._scale_method == 'centered':
            self_rect.center = disp_rect.center
            if disp_rect.contains(self_rect):
                self._target = screen.subsurface(self_rect)
            else:
                self._target = screen.subsurface(self_rect.fit(disp_rect))
        self.flip(delay=False)

    def blit(self, *args):
        r = Surface.blit(self, *args)
        r = self.rect_fb_to_window( r )
        self._update_rects.append( r )

    def flip(self, delay=True):
        self.scale_to_screen()
        if delay:  self.limit_fps()
        display.flip()

    def update(self, rectangle_list=None):
        if rectangle_list is None:
            display.update(self._update_rects)
            self._update_rects = []
        else:
            display.update(rectangle_list)

    def scale_to_screen(self):
        if self._scale_method == 'scale2x':
            tmpsurf = self
            target_width = self._target.get_width()
            while tmpsurf.get_width() < target_width:
                tmpsurf = transform.scale2x(tmpsurf)
            self._target.blit(tmpsurf, (0,0))
        else:
            f = transform.smoothscale if self._scale_smooth else transform.scale
            f(self, self._target.get_size(), self._target)

    def rect_fb_to_window(self, r):
        xfactor = float(self._target.get_width())  / self.get_width()
        yfactor = float(self._target.get_height()) / self.get_height()
        offset_x, offset_y = self._target.get_abs_offset()

        x = int((r.left * xfactor) + offset_x)
        y = int((r.top  * yfactor) + offset_y)
        w = int(r.w * xfactor)
        h = int(r.h * yfactor)
        return Rect(x,y,w,h)

    def rect_window_to_fb(self, r):
        xfactor = float(self._target.get_width())  / self.get_width()
        yfactor = float(self._target.get_height()) / self.get_height()
        offset_x, offset_y = self._target.get_abs_offset()

        x = int((r.left - offset_x) / xfactor)
        y = int((r.top  - offset_y) / yfactor)
        w = int(r.w / xfactor)
        h = int(r.h / yfactor)
        return Rect(x,y,w,h)




    def limit_fps(self):
        Tdelta = self._clock.tick(self._fps)
        Traw = self._clock.get_rawtime()
        realfps = int( self._clock.get_fps() )
        # too much less than 15 FPS and the brain stops pretending it's motion
        if realfps < self._fps-3 and self._fps > 15:
            self._lag += 1
            if self._lag > 100:
                self._fps /= 2
                self._lag = 0
        else:
            if self._lag >= 0:
                self._lag -= 1
            # no sense in going over 60 FPS (that i'm aware, anyway)
            elif Traw*2 < Tdelta and self._fps < 60:
                self._lag -= 1
            else:
                self._lag += 1

            if self._lag < -100:
                self._fps *= 2
                self._lag = 0
        display.set_caption('{} fps, targeting {} (lag: {})'.format(
            realfps, self._fps, (self._lag+5)//10
        ))
        self._tdelta = Tdelta
        return Tdelta

    def time_elapsed(self):  return self._tdelta

