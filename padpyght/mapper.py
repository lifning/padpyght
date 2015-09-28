import math
import pygame

import configurator
import frame_buffer
import visualizer
import util


class PadMapper:
    def __init__(self, skin, joy_index):
        self.cfg = configurator.PadConfig(skin)

        self.js = pygame.joystick.Joystick(joy_index)
        self.js.init()

        self.fb = frame_buffer.FrameBuffer(
            self.cfg.size, self.cfg.size, scale_smooth=self.cfg.anti_aliasing,
            background_color=self.cfg.background_color)

        self.gfx = visualizer.PadImage(self.cfg, self.fb)

    @staticmethod
    def display_message(msg):
        print msg
        pygame.display.set_caption(msg)

    def get_all_mappings(self):
        new_config = util.recursive_default_dict()
        data = new_config[self.js.get_name()]

        def update_data(output_type, result, target, stick_direction=None):
            input_type = result[0]
            input_index = result[1]
            subsection = data[input_type][str(input_index)]
            if input_type != 'button':
                movement = result[2]
                if input_type == 'axis':
                    movement = str(int(movement))
                    if movement[0] != '-':
                        movement = '+%s' % movement
                subsection = subsection[movement]
            subsection['name'] = target
            subsection['type'] = output_type
            if output_type == 'stick':
                assert stick_direction is not None
                subsection['direction'] = stick_direction

        for name in self.cfg.buttons:
            update_data('button', self.request_button(name), name)

        for name in self.cfg.sticks:
            stick_result = self.request_stick(name)
            for direction, direction_result in stick_result.iteritems():
                update_data('stick', direction_result, name, direction)

        for name in self.cfg.triggers:
            update_data('trigger', self.request_trigger(name), name)

        return new_config

    def get_next_joy_action(self, element):
        resting_position = [None] * self.js.get_numaxes()

        assert hasattr(element, 'push')

        def diff(axis, val):
            return val - float(resting_position[axis])

        axis_lock = False
        axis_result = None
        final_result = None
        while final_result is None:
            event = pygame.event.poll()
            if event.type == pygame.JOYAXISMOTION:
                value = round(event.value)
                if axis_result is None:
                    if resting_position[event.axis] is None:
                        # HACK: workaround for 'digital axes' (such as d-pads)
                        # not having in-between values near their resting pos
                        if abs(round(event.value, 3)) == 1.0:
                            resting_position[event.axis] = 0.0
                            axis_lock = True
                            axis_result = ['axis', int(event.axis),
                                           diff(event.axis, value)]
                        else:
                            resting_position[event.axis] = value
                    elif resting_position[event.axis] != value:
                        axis_lock = True
                        axis_result = ['axis', int(event.axis),
                                       diff(event.axis, value)]
                elif axis_result[1] == event.axis:
                    distance = diff(event.axis, value)
                    if abs(distance) > abs(axis_result[-1]):
                        axis_result[-1] = distance
                    elif distance == 0:
                        final_result = tuple(axis_result)
            elif not axis_lock:
                if event.type == pygame.JOYHATMOTION:
                    hat_values = {(0, 1): 'up', (0, -1): 'down',
                                  (-1, 0): 'left', (1, 0): 'right'}
                    direction = hat_values.get(tuple(event.value))
                    if direction is not None:
                        final_result = ('hat', int(event.hat), direction)
                elif event.type == pygame.JOYBUTTONDOWN:
                    final_result = ('button', int(event.button))
            self.fb.handle_event(event)
            sine = (math.sin(pygame.time.get_ticks() * math.pi / 250) + 1) / 2
            element.push(sine)
            self.gfx.draw()
            self.fb.flip(delay=True)

        pygame.event.pump()
        return final_result

    def request_button(self, button_name):
        self.display_message('Press %s' % button_name)
        element = self.gfx.buttons[button_name]
        result = self.get_next_joy_action(element)
        element.push(0)
        return result

    def request_stick(self, stick_name):
        result = dict()

        for direction in ('up', 'down', 'left', 'right'):
            self.display_message('Move %s %s, then release' % (stick_name,
                                                               direction))
            element = self.gfx.sticks[stick_name].directions[direction]
            result[direction] = self.get_next_joy_action(element)
            element.push(0)
        self.gfx.sticks[stick_name].reset()
        return result

    def request_trigger(self, trigger_name):
        self.display_message('Pull %s all the way, then release' % trigger_name)
        element = self.gfx.triggers[trigger_name]
        result = self.get_next_joy_action(element)
        element.push(0)
        return result


def main(skin, joy_index):
    all_maps = configurator.load_mappings(skin)

    pygame.display.init()
    pygame.joystick.init()
    new_map = PadMapper(skin, joy_index).get_all_mappings()
    all_maps.update(new_map)

    configurator.save_mappings(skin, all_maps)


if __name__ == '__main__':
    main('gamecube', 0)
