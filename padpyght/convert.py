from ConfigParser import ConfigParser
import json
import os
from padpyght import util


def integer_list(string):
    return [int(x) for x in string.split(',')]


def strip_ext(path):
    return os.path.splitext(path)[0]


def convert_pad_light_ini(skin_ini_path):
    cfg = ConfigParser()
    cfg.read(skin_ini_path)

    result = util.recursive_default_dict()

    data = dict(cfg.items('General'))
    general = result['general']
    general['background'] = strip_ext(data['file_background'])
    general['background-color'] = integer_list(data['backgroundcolor'])
    general['size'] = [int(data['width']), int(data['height'])]
    general['anti-aliasing'] = bool(int(data.get('aa', 1)))

    for sec in cfg.sections():
        data = dict(cfg.items(sec))
        if sec in ('Up', 'Down', 'Left', 'Right') or sec[:6] == 'Button':
            button_name = strip_ext(data['file_push'])
            if button_name in result['buttons']:
                raise KeyError('Duplicate key: %s %s' % (sec, button_name))
            button = result['buttons'][button_name]
            button['position'] = integer_list(data['position'])
            button['size'] = integer_list(data['size'])
        elif sec[:5] == 'Stick':
            stick_name = strip_ext(data['file_stick'])
            if stick_name in result['sticks']:
                raise KeyError('Duplicate key: %s %s' % (sec, stick_name))
            stick = result['sticks'][stick_name]
            stick['position'] = integer_list(data['position'])
            stick['size'] = integer_list(data['size'])
            stick['radius'] = int(data['radius'])
            # TODO: clicks
        elif sec[:7] == 'Trigger':
            trigger_name = strip_ext(data['file_trigger'])
            if trigger_name in result['triggers']:
                raise KeyError('Duplicate key: %s %s' % (sec, trigger_name))
            trigger = result['sticks'][trigger_name]
            trigger['position'] = integer_list(data['position'])
            trigger['size'] = integer_list(data['size'])
            trigger['depth'] = int(data['depth'])
            # TODO: clicks
        elif sec != 'General':
            print 'Unrecognized skin.ini section:', sec, data
    with open('%s.json' % strip_ext(skin_ini_path), 'w') as f:
        json.dump(result, f, indent=2, sort_keys=True)


if __name__ == '__main__':
    convert_pad_light_ini('skins/sfc2/skin.ini')
