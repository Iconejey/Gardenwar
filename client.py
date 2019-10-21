import os, sys, socket, json, colorama, math
from termcolor import colored
import pygame as pg

colorama.init()
pg.init()


# parce que sinon sur windows c'est flou
if sys.platform == 'win32':
	from ctypes import windll
	windll.shcore.SetProcessDpiAwareness(1)
	clear = lambda: os.system('cls')
else:
	clear = lambda: os.system('clear')


def receive(sock):
	data = ''
	while len(data) is 0 or data[-1] != '\t':
		data += sock.recv(1).decode('utf-8')
	return data.strip('\t')


def send(sock, data):
	sock.send((data + '\t').encode('utf-8'))


def rotate(point, origin, angle):
	if angle != 0:
		ox, oy = origin
		px, py = point

		return (
			ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy),
			oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy),
			)

	return point


def getEntities(data):
	players = {}
	bullets = []
	try:
		bullets_data, players_data = data.split('|')

		if len(bullets_data) is not 0:
			for line in bullets_data.split('\n'):
				x, y, bounces = [float(i) for i in line.split()]
				bullets.append([(x, y), bounces])

		if len(players_data) is not 0:
			for line in players_data.split('\n'):
				name, image = line.split()[:2]
				x, y, angle, mana, hp = [float(i) for i in line.split()[2:]]
				players[name] = [(x, y), angle, mana, hp, image]

	except Exception as e:
		print(data)
		raise e
	return bullets, players


def main():
	print('Reading settings...')
	with open('settings.json', 'r') as f:
		settings = json.load(f)

	print('loading images...')
	files = 'bg', 'flowerpot1', 'flowerpot2', 'flowerpot3', 'deadflowerpot1', 'deadflowerpot2', 'deadflowerpot3', 'dirtball1', 'dirtball2', 'dirtball3', 'cursor', 'pointer'
	images = {file: pg.image.load('images/' + file + '.png') for file in files}

	hitboxes = {}
	hitboxes['flowerpot1'] = 10, 95, 50, 140
	hitboxes['flowerpot2'] = 15, 65, 55, 110
	hitboxes['flowerpot3'] = 15, 35, 60, 80

	print('Opening socket...')
	host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket.setdefaulttimeout(1)

	connected = False
	while not connected:
		try:
			clear()
			sock = input('enter host ip: ').strip().split(':')
			if len(sock) is not 2:
				input("Please enter a valid ip address (example: 192.168.48.2:52200)\nPress [Enter] to try again.")
				continue
			address, port = sock
			host_socket.connect((address, int(port)))
			connected = True

		except TimeoutError:
			input(colored('Could not connect to server.', 'red') + colored('\nCheck the ip address and press [Enter] to try again.', 'magenta'))

		except ConnectionAbortedError:
			input(colored('The server whent through a problem.', 'red') + colored('Retry later. \nPress [Enter] to try again.', 'magenta'))

		except ConnectionRefusedError:
			input(colored('Connection refused.', 'red') + colored('\nThe server may be closed. Press [Enter] to try again.', 'magenta'))

	my_name = input(colored('Connected', 'green') + ". What's your name? (16 characters max) ").strip()
	send(host_socket, my_name)

	print(receive(host_socket)) # 'Starting game...' ------------------------------

	size = width, height = settings['size']
	win = pg.display.set_mode(size)

	game_loop = True
	while game_loop:
		for event in pg.event.get():
			if event.type == pg.QUIT:
				game_loop = False
				continue
		
		win.blit(images['bg'], (0, 0))

		data = receive(host_socket)
		if data == 'stop':
			game_loop = False
			continue
		bullets, players = getEntities(data)

		for (x, y), bounces in bullets:
			critic_bounce_number = settings['critic bounce number']
			frames = settings['dirt die frames']

			img = 'dirtball1'

			if bounces >= critic_bounce_number + frames:
				img = 'dirtball2'

			if bounces >= critic_bounce_number + frames * 2:
				img = 'dirtball3'

			win.blit(images[img], (x, y))

		mp = pg.mouse.get_pressed()[0]
		mx, my = pg.mouse.get_pos()
		keys = pg.key.get_pressed()
		z = keys[pg.K_w]
		s = keys[pg.K_s]
		q = keys[pg.K_a]
		d = keys[pg.K_d]
		controls_data = str(mp) + ' ' + str(mx) + ' ' + str(my) + ' ' + str(z) + ' ' + str(s) + ' ' + str(q) + ' ' + str(d)
		send(host_socket, controls_data)

		for name in players:
			pos, angle, mana, hp, image = players[name]

			if hp < 1:
				win.blit(images['dead' + image], pos)
			else:
				win.blit(images[image], pos)

			if name == my_name:
				x, y = pos
				hx1, hy1, hx2, hy2 = hitboxes[image]

				cx = (2 * x + hx1 + hx2) / 2
				cy = (2 * y + hy1 + hy2) / 2

				pointer_image = pg.transform.rotate(images['pointer'], angle * 180 / math.pi)
				pw, ph = pointer_image.get_rect().size

				px, py = rotate((cx + 54, cy), (cx, cy), -angle)
				px, py = px - pw / 2, py - ph / 2

				win.blit(pointer_image, (px, py))
		pg.display.update()
	print('\nend')


if __name__ == '__main__':
	input('Please use "Gardenwar.exe" to lunch the game.')