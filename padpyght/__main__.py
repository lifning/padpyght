# An open source gamepad visualizer inspired by PadLight.
# By Darren 'lifning' Alton

import os
import pkg_resources
import sys

import pygame

import configurator
import mapper
import visualizer


def main(skin, joy_index):
    pygame.display.init()
    pygame.joystick.init()

    joy = pygame.joystick.Joystick(joy_index)
    joy.init()
    mappings = configurator.load_mappings(skin)
    if joy.get_name() not in mappings:
        mapper.main(skin, joy_index)
    visualizer.main(skin, joy_index)


_skin = 'gamecube'
_joy_index = 0

try:
    if len(sys.argv) > 1:
        # HACK, since fallback for not having pgu is console mode, we can just
        # raise ImportError to simulate not having pgu.
        raise ImportError
    import pgu.gui
except ImportError:
    pgu = None
    if len(sys.argv) > 1:
        _skin = sys.argv[1]
    if len(sys.argv) > 2:
        _joy_index = int(sys.argv[2])
    main(_skin, _joy_index)
    sys.exit()

app = pgu.gui.Desktop()
app.connect(pgu.gui.QUIT, app.quit, None)
box = pgu.gui.Container(width=320, height=400)
joy_list = pgu.gui.List(width=320, height=160)
skin_list = pgu.gui.List(width=320, height=160)
run_btn = pgu.gui.Button('run', width=200, height=40)
remap_btn = pgu.gui.Button('remap', width=80, height=40)
box.add(joy_list, 4, 10)
box.add(skin_list, 4, 180)
box.add(run_btn, 4, 350)
box.add(remap_btn, 225, 350)

pygame.joystick.init()
for i in xrange(pygame.joystick.get_count()):
    name = pygame.joystick.Joystick(i).get_name()
    joy_list.add('{}: {}'.format(i, name), value=i)


def list_skin_paths():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.join(sys._MEIPASS, 'padpyght', 'skins')
        for dir_name in os.listdir(base_dir):
            path = os.path.join(base_dir, dir_name)
            yield dir_name, path
    else:
        for dir_name in pkg_resources.resource_listdir('padpyght', 'skins'):
            path = pkg_resources.resource_filename('padpyght',
                                                   'skins/%s' % dir_name)
            yield dir_name, path

for dir_name, path in list_skin_paths():
    cfg = os.path.join(path, 'skin.json')
    if os.path.exists(cfg):
        skin_list.add(dir_name, value=dir_name)
    else:
        print 'skin.json missing from', path


def main_wrapper():
    if skin_list.value is not None and joy_list.value is not None:
        screen = pygame.display.get_surface()
        size, flags = screen.get_size(), screen.get_flags()
        main(skin_list.value, joy_list.value)
        pygame.display.set_mode(size, flags)
        app.repaint()


def remap_wrapper():
    if skin_list.value is not None and joy_list.value is not None:
        screen = pygame.display.get_surface()
        size, flags = screen.get_size(), screen.get_flags()
        mapper.main(skin_list.value, joy_list.value)
        pygame.display.set_mode(size, flags)
        app.repaint()


run_btn.connect(pgu.gui.CLICK, main_wrapper)
remap_btn.connect(pgu.gui.CLICK, remap_wrapper)

app.run(box)
