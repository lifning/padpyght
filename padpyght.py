import pygame
from ConfigParser import ConfigParser

from frame_buffer import FrameBuffer

DPAD = ('Up', 'Down', 'Left', 'Right')
prefix = 'gamecube/'
joy = None

class StickImage:
	def __init__(self, screen, bg, position, size, file_stick, axes, radius):
		self.file_stick = pygame.image.load('{}/{}'.format(prefix, file_stick))
		self.position = tuple(int(x) for x in position.split(','))
		#self.size = tuple(int(x) for x in size.split(','))
		self.radius = int(radius)
		self.rect = self.file_stick.get_rect(center=self.position)
		self.domainrect = self.rect.inflate(self.radius*2, self.radius*2)
		self.file_free = bg.subsurface(self.domainrect).copy()
		self.axes = tuple(int(x) for x in axes.split(','))
		self.jx = joy.get_axis(self.axes[0])
		self.jy = joy.get_axis(self.axes[1])
		self.target = screen
		self.dirty = True

	def move(self, axis, val):
		if axis == self.axes[0]:
			self.jx = val
		else:
			self.jy = val
		self.dirty = True

	def draw(self):
		if self.dirty:
			pos = self.rect.move(int(self.jx*self.radius), int(self.jy*self.radius))
			self.target.blit(self.file_free, self.domainrect)
			self.target.blit(self.file_stick, pos)
			self.dirty = False

class ButtonImage:
	all = list()
	def __init__(self, screen, bg, position, size, file_push, file_free=None):
		self.file_push = pygame.image.load('{}/{}'.format(prefix, file_push))
		self.position = tuple(int(x) for x in position.split(','))
		#self.size = tuple(int(x) for x in size.split(','))
		#self.rect = pygame.Rect(self.position, self.size)
		self.rect = self.file_push.get_rect(center=self.position)
		self.target = screen.subsurface(self.rect)
		if file_free:
			self.file_free = pygame.image.load('{}/{}'.format(prefix, file_free))
		else:
			self.file_free = bg.subsurface(self.rect).copy()
		self.pressed = False
		ButtonImage.all.append(self)

	def press(self):
		self.target.blit(self.file_push, (0,0))
		self.pressed = True

	def release(self):
		self.target.blit(self.file_free, (0,0))
		self.pressed = False

	def draw(self):
		if self.pressed: self.press()
		else: self.release()

class TriggerImage:
	all = list()
	def __init__(self, screen, bg, position, size, file_trigger, axis, sign, depth):
		self.file_trigger = pygame.image.load('{}/{}'.format(prefix, file_trigger))
		self.position = tuple(int(x) for x in position.split(','))
		self.size = tuple(int(x) for x in size.split(','))
		self.depth = int(depth)
		self.rect = pygame.Rect(self.position, self.size)
		self.foreground = bg.subsurface(self.rect).copy()
		self.background = screen.subsurface(self.rect).copy()
		self.axis = int(axis)
		self.sign = int(sign)
		self.target = screen.subsurface(self.rect)
		self.val = 0.0
		self.dirty = True
		self.redraws = set()
		TriggerImage.all.append(self)

	def move(self, axis, val):
		if self.sign == 0:
			val = (val+1.0)/2
		if val*self.sign >= 0: # if signs agree
			self.val = abs(val)
			self.dirty = True

	def update_redraws(self):
		self.redraws = set(
			ButtonImage.all[bi] for bi in self.rect.collidelistall(
				[b.rect for b in ButtonImage.all]
			)
		)

	def draw(self):
		if self.dirty:
			self.target.blit(self.background, (0,0))
			self.target.blit(self.file_trigger, (0, int(self.val*self.depth)))
			self.target.blit(self.foreground, (0,0))
			for b in self.redraws: b.draw()
			self.dirty = False

def main(argv):
	global prefix, joy
	if len(argv) > 1: prefix = argv[1]

	cfg = ConfigParser()
	cfg.read('{}/skin.ini'.format(prefix))

	buttons = dict()
	sticks = dict()
	screen = None

	data = dict(cfg.items('General'))
	winsize = (int(data['width']), int(data['height']))
	bg = pygame.image.load('{}/{}'.format(prefix, data['file_background']))
	screen = FrameBuffer(winsize, bg.get_size(),
						 scale_method='pixelperfect', scale_smooth=int(data.get('aa', 1)))
	screen.fill(tuple(int(x) for x in data['backgroundcolor'].split(',')))
	screen.blit(bg, (0,0))

	pygame.joystick.init()
	joy = pygame.joystick.Joystick(0)
	joy.init()

	btn_listeners = [None] * joy.get_numbuttons()
	axis_listeners = [set() for i in xrange(joy.get_numaxes())]

	for sec in cfg.sections():
		data = dict(cfg.items(sec))
		if sec in DPAD:
			buttons[sec] = ButtonImage(screen, bg, **data)
		elif sec[:5] == 'Stick':
			tmpobj = StickImage(screen, bg, **data)
			for n in tmpobj.axes:
				axis_listeners[n].add(tmpobj)
		elif sec[:6] == 'Button':
			n = int(sec[6:])-1
			btn_listeners[n] = ButtonImage(screen, bg, **data)
		elif sec[:7] == 'Trigger':
			tmpobj = TriggerImage(screen, bg, **data)
			axis_listeners[tmpobj.axis].add(tmpobj)
		elif sec != 'General':
			print sec, data

	for t in TriggerImage.all:
		t.update_redraws()

	while True:
		for e in pygame.event.get():
			if e.type == pygame.VIDEORESIZE:
				pygame.display.set_mode(e.size, pygame.display.get_surface().get_flags())
				screen.compute_target_subsurf()
			elif e.type == pygame.QUIT:
				raise SystemExit
			elif e.type == pygame.JOYAXISMOTION:
				for al in axis_listeners[e.axis]:
					al.move(e.axis, e.value)
			elif e.type == pygame.JOYHATMOTION:
				x,y = e.value
				for d in DPAD: buttons[d].release()
				if   y > 0: buttons['Up'].press()
				elif y < 0: buttons['Down'].press()
				if   x < 0: buttons['Left'].press()
				elif x > 0: buttons['Right'].press()
			elif e.type == pygame.JOYBUTTONUP and btn_listeners[e.button]:
				btn_listeners[e.button].release()
			elif e.type == pygame.JOYBUTTONDOWN and btn_listeners[e.button]:
				btn_listeners[e.button].press()
		for al_set in axis_listeners:
			for al in al_set:
				al.draw()
		screen.flip()

if __name__ == "__main__":
	import sys
	main(sys.argv)
