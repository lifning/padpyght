# A simple open source padlight clone, with custom extensions for analog sticks and triggers.
# By Darren Alton

import pygame
import itertools
import sys, os
from ConfigParser import ConfigParser

from frame_buffer import FrameBuffer

class ButtonImage:
	all = list()
	def __init__(
		self, skin, joy, screen, bg, position, size, file_push=None, file_free=None, button=None,
		margin=0, auto_rect=True, copybg=False, copyfg=False
	):
		self.joy = joy
		self.target = screen
		self.image_push = None
		self.image_free = None
		try:   self.image_push = pygame.image.load('{}/{}'.format(skin, file_push))
		except pygame.error: pass
		try:   self.image_free = pygame.image.load('{}/{}'.format(skin, file_free))
		except pygame.error: pass
		self.image = self.image_free or self.image_push
		if self.image is None:  raise ValueError
		self.position = tuple(int(x) for x in position.split(','))
		self.size = pygame.Rect( (0,0), tuple(int(x) for x in size.split(',')) )
		self.rect = self.size.copy()
		self.rect.center = self.position # TODO: is centering this correct?
		if auto_rect:
			self.rect = self.image.get_rect(center=self.position)
		self.position = self.rect.topleft
		self.domainrect = self.rect.inflate(margin*2, margin*2).clip(self.target.get_rect())
		self.foreground = None if not copyfg else bg.subsurface(self.domainrect).copy()
		self.background = None if not copybg else screen.subsurface(self.domainrect).copy()
		if self.image_push is None:  self.image_push = bg.subsurface(self.rect).copy()
		if self.image_free is None:  self.image_free = bg.subsurface(self.rect).copy()
		self.image = self.image_free # maybe joy.get_button
		self.__class__.all.append(self)
		self.button = int(button) if button else None
		self.dirty = True

	def press(self):
		self.image = self.image_push
		self.dirty = True

	def release(self):
		self.image = self.image_free
		self.dirty = True

	def draw(self, force=False):
		if self.dirty or force:
			if self.background:  self.target.blit(self.background, self.domainrect)
			self.target.blit(self.image, self.position, area=self.size)
			if self.foreground:  self.target.blit(self.foreground, self.domainrect)
			self.dirty = False

class StickImage(ButtonImage):
	all = list()
	def __init__(self, skin, joy, screen, bg, position, size, file_stick, axes, radius, button=None, file_push=None):
		self.radius = int(radius)
		self.axes = tuple(int(x) for x in axes.split(','))
		ButtonImage.__init__(
			self, skin, joy, screen, bg, position, size, file_push, file_stick, button=button,
			margin=self.radius, copybg=True
		)
		self.jx, self.jy = (self.joy.get_axis(a) for a in self.axes)

	def move(self, axis, val):
		if axis == self.axes[0]:
			self.jx = val
		else:
			self.jy = val
		self.dirty = True

	def draw(self):
		x,y = self.jx, self.jy
		dist = (x*x + y*y)**.5
		if dist > 1.0:
			x /= dist
			y /= dist
		self.position = self.rect.move(int(x*self.radius), int(y*self.radius))
		ButtonImage.draw(self)

class TriggerImage(ButtonImage):
	all = list()
	def __init__(self, skin, joy, screen, bg, position, size, file_trigger, axis, sign, depth):
		self.depth = int(depth)
		self.axis = int(axis)
		self.sign = int(sign)
		self.val = 0.0
		self.redraws = set()
		ButtonImage.__init__(
			self, skin, joy, screen, bg, position, size, file_trigger, file_trigger,
			margin=self.depth, auto_rect=False, copybg=True, copyfg=True
		)

	def move(self, axis, val):
		if self.sign == 0:
			val = (val+1.0)/2
		if val*self.sign >= 0: # if signs agree
			self.val = abs(val)
			self.dirty = True

	def update_redraws(self):
		self.redraws = set(
			ButtonImage.all[bi] for bi in self.domainrect.collidelistall(
				[b.domainrect for b in ButtonImage.all]
			)
		)

	def draw(self):
		if self.dirty:
			self.position = self.rect.move(0, int(self.val*self.depth))
			ButtonImage.draw(self)
			for b in self.redraws: b.draw(force=True)

def main(skin, joyindex):
	cfg = ConfigParser()
	cfg.read('{}/skin.ini'.format(skin))

	data = dict(cfg.items('General'))
	winsize = (int(data['width']), int(data['height']))
	try:
		bg = pygame.image.load('{}/{}'.format(skin, data['file_background']))
	except pygame.error:
		bg = pygame.Surface(winsize)
	bgcolor = tuple(int(x) for x in data['backgroundcolor'].split(','))
	screen = FrameBuffer(winsize, bg.get_size(),
						 scale_type='pixelperfect', scale_smooth=int(data.get('aa', 1)),
						 bgcolor=bgcolor)
	screen.fill(bgcolor)
	screen.blit(bg, (0,0))

	pygame.joystick.init()
	joy = pygame.joystick.Joystick(joyindex)
	joy.init()

	dpad_buttons = dict()
	btn_listeners = [set() for i in xrange(joy.get_numbuttons())]
	axis_listeners = [set() for i in xrange(joy.get_numaxes())]

	for sec in cfg.sections():
		data = dict(cfg.items(sec))
		if sec in ('Up', 'Down', 'Left', 'Right'):
			dpad_buttons[sec] = ButtonImage(skin, joy, screen, bg, **data)
		elif sec[:5] == 'Stick':
			tmpobj = StickImage(skin, joy, screen, bg, **data)
			for n in tmpobj.axes:
				axis_listeners[n].add(tmpobj)
			if tmpobj.button is not None:
				btn_listeners[int(tmpobj.button)-1].add(tmpobj)
		elif sec[:6] == 'Button':
			n = int(sec[6:])-1
			btn_listeners[n].add(ButtonImage(skin, joy, screen, bg, **data))
		elif sec[:7] == 'Trigger':
			tmpobj = TriggerImage(skin, joy, screen, bg, **data)
			axis_listeners[tmpobj.axis].add(tmpobj)
		elif sec != 'General':
			print sec, data

	for t in TriggerImage.all:
		t.update_redraws()

	dirtyscreen = True
	running = True
	while running:
		for e in pygame.event.get():
			if e.type == pygame.VIDEORESIZE:
				pygame.display.set_mode(e.size, pygame.display.get_surface().get_flags())
				screen.compute_target_subsurf()
			elif e.type == pygame.QUIT:
				running = False
				break
			elif e.type == pygame.JOYAXISMOTION:
				for al in axis_listeners[e.axis]:
					al.move(e.axis, e.value)
					dirtyscreen = True
			elif e.type == pygame.JOYHATMOTION:
				x,y = e.value
				for d in dpad_buttons.itervalues():
					d.release()
					d.draw()
				if   y > 0: dpad_buttons['Up'].press()
				elif y < 0: dpad_buttons['Down'].press()
				if   x < 0: dpad_buttons['Left'].press()
				elif x > 0: dpad_buttons['Right'].press()
				dirtyscreen = True
			elif e.type == pygame.JOYBUTTONUP and btn_listeners[e.button]:
				for bl in btn_listeners[e.button]:
					bl.release()
					dirtyscreen = True
			elif e.type == pygame.JOYBUTTONDOWN and btn_listeners[e.button]:
				for bl in btn_listeners[e.button]:
					bl.press()
					dirtyscreen = True
		for img_set in itertools.chain(axis_listeners, btn_listeners):
			for img in img_set:
				img.draw()
		for d in dpad_buttons.itervalues():
			d.draw()
		#screen.flip()
		screen.limit_fps()
		if dirtyscreen:
			screen.update()
			dirtyscreen = False

if __name__ == "__main__":
	try:
		if len(sys.argv) > 1: raise ImportError # hack
		from pgu import gui
	except ImportError:
		skin = 'gamecube'
		joyindex = 0
		if len(sys.argv) > 1: skin = sys.argv[1]
		if len(sys.argv) > 2: joyindex = int(sys.argv[2])
		main(skin, joyindex)
		sys.exit()

	app = gui.Desktop()
	app.connect(gui.QUIT, app.quit, None)
	box = gui.Container(width=320, height=400)
	joy_list = gui.List(width=320, height=160)
	skin_list = gui.List(width=320, height=160)
	btn = gui.Button("run", width=300, height=40)
	box.add(joy_list, 4, 10)
	box.add(skin_list, 4, 180)
	box.add(btn, 4, 350)

	pygame.joystick.init()
	for i in xrange(pygame.joystick.get_count()):
		joy_list.add('{}: {}'.format(i, pygame.joystick.Joystick(i).get_name()), value=i)

	for fname in os.listdir('.'):
		if os.path.exists('{}/skin.ini'.format(fname)):
			skin_list.add(fname, value=fname)

	def main_wrapper():
		if skin_list.value is None or joy_list.value is None: return
		screen = pygame.display.get_surface()
		size, flags = screen.get_size(), screen.get_flags()
		main(skin_list.value, joy_list.value)
		pygame.display.set_mode(size, flags)
		app.repaint()

	btn.connect(gui.CLICK, main_wrapper)
	app.run(box)
