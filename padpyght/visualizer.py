import os
import pygame

import configurator
import frame_buffer


class ButtonImage:
    all = list()

    def __init__(self, screen, background, position, size, image_push=None,
                 image_free=None, margin=0, auto_rect=True, copy_bg=False,
                 copy_fg=False):
        self.target = screen
        self.image_push = image_push
        self.image_free = image_free
        self.image = self.image_free or self.image_push
        if self.image is None:
            raise ValueError
        self.position = tuple(position)
        self.size = pygame.Rect((0, 0), tuple(size))
        self.rect = self.size.copy()
        self.rect.center = self.position  # TODO: is centering this correct?
        if auto_rect:
            self.rect = self.image.get_rect(center=self.position)
        self.position = self.rect.topleft
        self.domain_rect = self.rect.inflate(margin * 2, margin * 2).clip(
            self.target.get_rect())
        self.foreground = None
        self.background = None
        if background is not None:
            if copy_fg:
                self.foreground = background.subsurface(self.domain_rect).copy()
            if copy_bg:
                self.background = screen.subsurface(self.domain_rect).copy()
            if self.image_push is None:
                self.image_push = background.subsurface(self.rect).copy()
            if self.image_free is None:
                self.image_free = background.subsurface(self.rect).copy()
        self.image = self.image_free
        ButtonImage.all.append(self)
        self.dirty = True

    def push(self, value):
        if value > 0.5:
            self._press()
        else:
            self._release()

    def _press(self):
        if self.image is not self.image_push:
            self.image = self.image_push
            self.dirty = True

    def _release(self):
        if self.image is not self.image_free:
            self.image = self.image_free
            self.dirty = True

    def draw(self, force=False):
        if self.dirty or force:
            if self.background:
                self.target.blit(self.background, self.domain_rect)
            self.target.blit(self.image, self.position, area=self.size)
            if self.foreground:
                self.target.blit(self.foreground, self.domain_rect)
            self.dirty = False


class StickImage(ButtonImage):
    class Direction:
        def __init__(self, parent):
            self.value = 0
            self.parent = parent

        def push(self, value):
            if self.value != value:
                self.value = min(1, max(0, value))
                self.parent.dirty = True

    def __init__(self, screen, background, position, size, radius, image_stick,
                 image_push=None):
        self.radius = int(radius)
        self.directions = {'up': StickImage.Direction(self),
                           'down': StickImage.Direction(self),
                           'left': StickImage.Direction(self),
                           'right': StickImage.Direction(self)}
        ButtonImage.__init__(self, screen, background, position, size,
                             image_push, image_stick, margin=self.radius,
                             copy_bg=True)

    def reset(self):
        for direction in self.directions.itervalues():
            direction.push(0)

    def draw(self, force=False):
        if self.dirty or force:
            x = self.directions['right'].value - self.directions['left'].value
            y = self.directions['down'].value - self.directions['up'].value
            dist = ((x * x) + (y * y)) ** .5
            if dist > 1.0:
                x /= dist
                y /= dist
            self.position = self.rect.move(int(x * self.radius),
                                           int(y * self.radius))
            ButtonImage.draw(self)


class TriggerImage(ButtonImage):
    def __init__(self, screen, background, position, size, depth,
                 image_trigger):
        self.depth = int(depth)
        self.value = 0.0
        self.redraws = set()
        ButtonImage.__init__(self, screen, background, position, size,
                             image_trigger, image_trigger, margin=self.depth,
                             auto_rect=False, copy_bg=True, copy_fg=True)

    def push(self, value):
        if self.value != value:
            self.value = min(1, max(0, value))
            self.dirty = True

    def update_redraws(self):
        self.redraws = set(
            ButtonImage.all[bi] for bi in self.domain_rect.collidelistall(
                [b.domain_rect for b in ButtonImage.all]
            ) if ButtonImage.all[bi] is not self
        )

    def draw(self, force=False):
        if self.dirty or force:
            self.position = self.rect.move(0, int(self.value * self.depth))
            ButtonImage.draw(self)
            for b in self.redraws:
                b.draw(force=True)


class PadImage:
    def __init__(self, cfg, screen):
        assert isinstance(cfg, configurator.PadConfig)
        self.buttons = dict()
        self.triggers = dict()
        self.sticks = dict()

        def load_image(name):
            return pygame.image.load(os.path.join(cfg.path, '%s.png' % name))

        self.target = screen
        self.target.fill(cfg.background_color)
        self.background = load_image(cfg.background)
        self.target.blit(self.background, (0, 0))

        for button_cfg in cfg.buttons.itervalues():
            assert isinstance(button_cfg, configurator.ButtonConfig)
            image_push = load_image(button_cfg.name)
            obj = ButtonImage(self.target, self.background,
                              button_cfg.position, button_cfg.size, image_push)
            self.buttons[button_cfg.name] = obj

        for stick_cfg in cfg.sticks.itervalues():
            assert isinstance(stick_cfg, configurator.StickConfig)
            image_stick = load_image(stick_cfg.name)
            obj = StickImage(self.target, self.background,
                             stick_cfg.position, stick_cfg.size,
                             stick_cfg.radius, image_stick)
            self.sticks[stick_cfg.name] = obj

        for trigger_cfg in cfg.triggers.itervalues():
            assert isinstance(trigger_cfg, configurator.TriggerConfig)
            image_trigger = load_image(trigger_cfg.name)
            obj = TriggerImage(self.target, self.background,
                               trigger_cfg.position, trigger_cfg.size,
                               trigger_cfg.depth, image_trigger)
            self.triggers[trigger_cfg.name] = obj

        for trigger in self.triggers.itervalues():
            trigger.update_redraws()

    def draw(self):
        for button in self.buttons.itervalues():
            assert isinstance(button, ButtonImage)
            button.draw()
        for stick in self.sticks.itervalues():
            assert isinstance(stick, StickImage)
            stick.draw()
        for trigger in self.triggers.itervalues():
            assert isinstance(trigger, TriggerImage)
            trigger.draw()


def _get_target(pad_gfx, map_element):
    elt_type = map_element['type']
    elt_name = map_element['name']
    target = None
    if elt_type == 'button':
        target = pad_gfx.buttons[elt_name]
    elif elt_type == 'trigger':
        target = pad_gfx.triggers[elt_name]
    elif elt_type == 'stick':
        which = map_element['direction']
        target = pad_gfx.sticks[elt_name].directions[which]
    assert target is not None
    return target


def main(skin, joy_index):
    pygame.display.init()
    pygame.joystick.init()

    joy = pygame.joystick.Joystick(joy_index)
    joy.init()
    mappings = configurator.load_mappings(skin)
    if joy.get_name() not in mappings:
        print 'Please run the mapper on', joy.get_name(), 'with', skin, 'skin.'
        return

    mappings = mappings[joy.get_name()]

    button_map = mappings.get('button', dict())
    axis_map = mappings.get('axis', dict())
    hat_map = mappings.get('hat', dict())

    pad_cfg = configurator.PadConfig(skin)

    fb = frame_buffer.FrameBuffer(pad_cfg.size, pad_cfg.size,
                                  scale_smooth=pad_cfg.anti_aliasing,
                                  background_color=pad_cfg.background_color)
    pad_gfx = PadImage(pad_cfg, fb)

    while not pygame.event.peek(pygame.QUIT):
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if str(event.button) in button_map:
                    elt = button_map[str(event.button)]
                    _get_target(pad_gfx, elt).push(1)
            elif event.type == pygame.JOYBUTTONUP:
                if str(event.button) in button_map:
                    elt = button_map[str(event.button)]
                    _get_target(pad_gfx, elt).push(0)
            elif event.type == pygame.JOYAXISMOTION:
                if str(event.axis) in axis_map:
                    for change, elt in axis_map[str(event.axis)].iteritems():
                        change = int(change)
                        value = event.value
                        if abs(change) == 2:
                            value += change / abs(change)
                        value /= change
                        value = max(0, value)
                        _get_target(pad_gfx, elt).push(value)
            elif event.type == pygame.JOYHATMOTION:
                if str(event.hat) in hat_map:
                    direction_map = hat_map[str(event.hat)]
                    x, y = event.value
                    if 'up' in direction_map:
                        _get_target(pad_gfx, direction_map['up']).push(y)
                    if 'down' in direction_map:
                        _get_target(pad_gfx, direction_map['down']).push(-y)
                    if 'left' in direction_map:
                        _get_target(pad_gfx, direction_map['left']).push(-x)
                    if 'right' in direction_map:
                        _get_target(pad_gfx, direction_map['right']).push(x)
            fb.handle_event(event)

        pad_gfx.draw()
        fb.flip()
        fb.limit_fps(set_caption=True)


if __name__ == '__main__':
    main('gamecube', 0)
