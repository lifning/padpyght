
from pygame import Surface, Rect, display, time, transform
from pygame import FULLSCREEN, DOUBLEBUF, HWSURFACE, OPENGL, RESIZABLE, NOFRAME

class FrameBuffer(Surface):
    instance = None

    def __init__(self, disp_res, fb_res, flags=HWSURFACE|DOUBLEBUF|RESIZABLE,
                 fps=60, scale_type='pixelperfect', scale_smooth=False, bgcolor=(0,0,0)):
        screen = display.set_mode(disp_res, flags)
        Surface.__init__(self, fb_res, flags)

        self._scale_type = scale_type
        self._scale_function = transform.smoothscale if scale_smooth else transform.scale
        self.bgcolor = bgcolor
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
        screen.fill(self.bgcolor)
        self_rect = self.get_rect()
        disp_rect = screen.get_rect()

        if self._scale_type == 'pixelperfect':
            factor = min( float(disp_rect.w)/self_rect.w,
                          float(disp_rect.h)/self_rect.h )
            if factor >= 1.0:  factor = int(factor)
            w = int(factor*self_rect.w)
            h = int(factor*self_rect.h)
            r = Rect(0,0,w,h)
            r.center = disp_rect.center
            self._target = screen.subsurface(r)
        elif self._scale_type == 'scale2x':
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
        elif self._scale_type == 'proportional':
            self._target = screen.subsurface(self_rect.fit(disp_rect))
        elif self._scale_type == 'stretch':
            self._target = screen
        else: #elif self._scale_type == 'centered':
            self_rect.center = disp_rect.center
            if disp_rect.contains(self_rect):
                self._target = screen.subsurface(self_rect)
            else:
                self._target = screen.subsurface(self_rect.fit(disp_rect))
        self.flip(delay=False)

    def blit(self, *args, **kwargs):
        self._update_rects.append( Surface.blit(self, *args, **kwargs) )

    def flip(self, delay=True):
        if self._scale_type == 'scale2x':
            tmpsurf = self
            target_width = self._target.get_width()
            while tmpsurf.get_width() < target_width:
                tmpsurf = transform.scale2x(tmpsurf)
            self._target.blit(tmpsurf, (0,0))
        else:
            self._scale_function(self, self._target.get_size(), self._target)
        if delay:  self.limit_fps()
        display.flip()
        self._update_rects = []

    def update(self):
        window_rects = []
        screen = self._target.get_abs_parent()
        for r in self._update_rects:
            wr = self.rect_fb_to_window( r )
            tmpsurf = self._scale_function( self.subsurface(r), wr.size )
            screen.blit( tmpsurf, wr )
            wr.inflate_ip( 4, 4 )
            window_rects.append( wr )
        display.update( window_rects )
        self._update_rects = []

    def rect_fb_to_window(self, r):
        xfactor = float(self._target.get_width())  / self.get_width()
        yfactor = float(self._target.get_height()) / self.get_height()
        offset_x, offset_y = self._target.get_abs_offset()

        x = int((r.left * xfactor) + offset_x + 0.5)
        y = int((r.top  * yfactor) + offset_y + 0.5)
        w = int(r.w * xfactor + 0.5)
        h = int(r.h * yfactor + 0.5)
        return Rect(x,y,w,h)

    def rect_window_to_fb(self, r):
        xfactor = float(self._target.get_width())  / self.get_width()
        yfactor = float(self._target.get_height()) / self.get_height()
        offset_x, offset_y = self._target.get_abs_offset()

        x = int((r.left - offset_x) / xfactor + 0.5)
        y = int((r.top  - offset_y) / yfactor + 0.5)
        w = int(r.w / xfactor + 0.5)
        h = int(r.h / yfactor + 0.5)
        return Rect(x,y,w,h)




    def limit_fps(self, set_caption=True):
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
        if set_caption:
            display.set_caption('{} fps, targeting {} (lag: {})'.format(
                realfps, self._fps, (self._lag+5)//10
            ))
        self._tdelta = Tdelta
        return Tdelta

    def time_elapsed(self):  return self._tdelta

