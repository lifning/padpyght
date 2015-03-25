import pygame
import sys


def get_next_joy_action(js):
    resting_position = [None] * js.get_numaxes()

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

    pygame.event.pump()
    return final_result


def main(joy_index='0'):
    joy_index = int(joy_index)
    pygame.display.init()
    pygame.joystick.init()
    joy = pygame.joystick.Joystick(joy_index)
    joy.init()
    joy_name = joy.get_name()
    print joy_name, 'initialized'

    def request_input(js, message):
        sys.stdout.write('%s ... ' % message)
        sys.stdout.flush()
        result = get_next_joy_action(js)
        return result

    for name in ('main stick', 'C stick'):
        print request_input(joy, 'Move %s upward, then release' % name)
        print request_input(joy, 'Move %s downward, then release' % name)
        print request_input(joy, 'Move %s to the left, then release' % name)
        print request_input(joy, 'Move %s to the right, then release' % name)

    for name in ('A', 'B', 'X', 'Y', 'Z', 'Start',
                 'D-Up', 'D-Down', 'D-Left', 'D-Right'):
        print request_input(joy, 'Press %s' % name)

    for name in ('L', 'R'):
        print request_input(joy, 'Completely press and release %s' % name)


if __name__ == '__main__':
    main(*sys.argv[1:])
