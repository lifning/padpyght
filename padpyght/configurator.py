import collections
import json
import os
import pkg_resources
import sys


class ButtonConfig(object):
    def __init__(self, name, position, size):
        self.name = str(name)
        assert len(position) == 2
        assert len(size) == 2
        self.position = tuple(position)
        self.size = tuple(size)


class StickConfig(ButtonConfig):
    def __init__(self, name, position, size, radius):
        super(StickConfig, self).__init__(name, position, size)
        self.radius = int(radius)


class TriggerConfig(ButtonConfig):
    def __init__(self, name, position, size, depth):
        super(TriggerConfig, self).__init__(name, position, size)
        self.depth = int(depth)


class PadConfig:
    def __init__(self, skin_name):
        self.name = skin_name
        self.path = pkg_resources.resource_filename('padpyght',
                                                    'skins/%s' % skin_name)

        cfg = os.path.join(self.path, 'skin.json')
        with open(cfg, 'r') as f:
            parsed = json.load(f)
        assert isinstance(parsed, dict)
        general = parsed.get('general', dict())
        assert isinstance(general, dict)

        self.size = None
        self.background = None
        self.background_color = None
        self.anti_aliasing = None
        for js_key in ('background', 'background-color',
                       'size', 'anti-aliasing'):
            py_key = js_key.replace('-', '_')
            self.__dict__[py_key] = general.get(js_key, None)

        def component_parser(key, factory):
            result = collections.OrderedDict()
            group = parsed.get(key, dict())
            assert isinstance(group, dict)
            for name, data in sorted(group.iteritems()):
                assert isinstance(data, dict)
                result[str(name)] = factory(name, **data)
            return result

        self.sticks = component_parser('sticks', StickConfig)
        self.triggers = component_parser('triggers', TriggerConfig)
        self.buttons = component_parser('buttons', ButtonConfig)


def _mappings_path():
    path = os.path.expanduser('~/.config')
    if sys.platform == 'win32':
        path = os.path.expandvars('%AppData%')
    elif sys.platform == 'darwin':
        path = os.path.expanduser('~/Library/Application Support')
    return os.path.join(path, 'padpyght', 'mappings')


def load_mappings(skin):
    path = _mappings_path()
    map_filename = os.path.join(path, '%s.json' % skin)
    if os.path.exists(map_filename):
        with open(map_filename, 'r') as f:
            return json.load(f)
    return dict()


def save_mappings(skin, data):
    path = _mappings_path()
    if not os.path.exists(path):
        os.makedirs(path)
    map_filename = os.path.join(path, '%s.json' % skin)
    with open(map_filename, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)
