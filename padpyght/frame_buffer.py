import pygame


class FrameBuffer(pygame.Surface):
    instance = None

    def __init__(self, display_res, fb_res,
                 flags=pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE,
                 fps=60, scale_type='pixelperfect', scale_smooth=False,
                 background_color=(0, 0, 0)):
        pygame.display.set_mode(display_res, flags)
        pygame.Surface.__init__(self, fb_res, flags)

        self._base_size = display_res
        self._scale_factor = 1.0
        self._scale_type = scale_type
        self._scale_function = pygame.transform.scale
        if scale_smooth:
            self._scale_function = pygame.transform.smoothscale
        self.background_color = background_color
        self._target = self._compute_target_subsurface()

        self._update_rectangles = []

        self._clock = pygame.time.Clock()
        self._fps = fps
        self._lag = 0
        self._t_delta = 0

        if FrameBuffer.instance is None:
            FrameBuffer.instance = self

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            flags = pygame.display.get_surface().get_flags()
            pygame.display.set_mode(event.size, flags)
            self.recompute_target_subsurface()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_KP_MINUS:
                self._scale_factor -= 0.1
            elif event.key == pygame.K_KP_PLUS:
                self._scale_factor += 0.1
            self._scale_factor = max(0.1, self._scale_factor)
            w, h = self._base_size
            flags = pygame.display.get_surface().get_flags()
            pygame.display.set_mode((int(w * self._scale_factor),
                                    int(h * self._scale_factor)), flags)
            self.recompute_target_subsurface()

    def recompute_target_subsurface(self):
        self._target = self._compute_target_subsurface()
        self.flip(delay=False)

    def _compute_target_subsurface(self):
        screen = pygame.display.get_surface()
        screen.fill(self.background_color)
        self_rect = self.get_rect()
        display_rect = screen.get_rect()

        if self._scale_type == 'pixelperfect':
            factor = min(float(display_rect.w) / self_rect.w,
                         float(display_rect.h) / self_rect.h)
            if factor >= 1.0:
                factor = int(factor)
            w = int(factor * self_rect.w)
            h = int(factor * self_rect.h)
            r = pygame.Rect(0, 0, w, h)
            r.center = display_rect.center
            target = screen.subsurface(r)
        elif self._scale_type == 'scale2x':
            factor = min(display_rect.w // self_rect.w,
                         display_rect.h // self_rect.h)
            pow2 = 0
            while (2 << pow2) <= factor:  # yes, 2<<pow2.
                pow2 += 1
            factor = (1 << pow2)
            w = factor * self_rect.w
            h = factor * self_rect.h
            r = pygame.Rect(0, 0, w, h)
            r.center = display_rect.center
            if display_rect.contains(r):
                target = screen.subsurface(r)
            else:
                target = screen
        elif self._scale_type == 'proportional':
            target = screen.subsurface(self_rect.fit(display_rect))
        elif self._scale_type == 'stretch':
            target = screen
        else:  # elif self._scale_type == 'centered':
            self_rect.center = display_rect.center
            if display_rect.contains(self_rect):
                target = screen.subsurface(self_rect)
            else:
                target = screen.subsurface(self_rect.fit(display_rect))
        return target

    def blit(self, *args, **kwargs):
        self._update_rectangles.append(pygame.Surface.blit(self, *args, **kwargs))

    def flip(self, delay=True):
        if self._scale_type == 'scale2x':
            tmp_surf = self
            target_width = self._target.get_width()
            while tmp_surf.get_width() < target_width:
                tmp_surf = pygame.transform.scale2x(tmp_surf)
            self._target.blit(tmp_surf, (0, 0))
        else:
            self._scale_function(self, self._target.get_size(), self._target)
        if delay:
            self.limit_fps(set_caption=False)
        pygame.display.flip()
        self._update_rectangles = []

    def update(self):
        window_rectangles = []
        screen = self._target.get_abs_parent()
        for r in self._update_rectangles:
            wr = self.rect_fb_to_window(r)
            tmp_surf = self._scale_function(self.subsurface(r), wr.size)
            screen.blit(tmp_surf, wr)
            wr.inflate_ip(4, 4)
            window_rectangles.append(wr)
        pygame.display.update(window_rectangles)
        self._update_rectangles = []

    def rect_fb_to_window(self, r):
        x_factor = float(self._target.get_width()) / self.get_width()
        y_factor = float(self._target.get_height()) / self.get_height()
        offset_x, offset_y = self._target.get_abs_offset()

        x = int((r.left * x_factor) + offset_x + 0.5)
        y = int((r.top * y_factor) + offset_y + 0.5)
        w = int(r.w * x_factor + 0.5)
        h = int(r.h * y_factor + 0.5)
        return pygame.Rect(x, y, w, h)

    def rect_window_to_fb(self, r):
        x_factor = float(self._target.get_width()) / self.get_width()
        y_factor = float(self._target.get_height()) / self.get_height()
        offset_x, offset_y = self._target.get_abs_offset()

        x = int((r.left - offset_x) / x_factor + 0.5)
        y = int((r.top - offset_y) / y_factor + 0.5)
        w = int(r.w / x_factor + 0.5)
        h = int(r.h / y_factor + 0.5)
        return pygame.Rect(x, y, w, h)

    def limit_fps(self, set_caption=True):
        t_delta = self._clock.tick(self._fps)
        t_raw = self._clock.get_rawtime()
        real_fps = int(self._clock.get_fps())
        # too much less than 15 FPS and the brain stops pretending it's motion
        if real_fps < self._fps - 3 and self._fps > 15:
            self._lag += 1
            if self._lag > 100:
                self._fps /= 2
                self._lag = 0
        else:
            if self._lag >= 0:
                self._lag -= 1
            # no sense in going over 60 FPS (that i'm aware, anyway)
            elif t_raw * 2 < t_delta and self._fps < 60:
                self._lag -= 1
            else:
                self._lag += 1

            if self._lag < -100:
                self._fps *= 2
                self._lag = 0
        if set_caption:
            pygame.display.set_caption('{} fps, targeting {} (lag: {})'.format(
                real_fps, self._fps, (self._lag + 5) // 10
            ))
        self._t_delta = t_delta
        return t_delta

    def time_elapsed(self):
        return self._t_delta
