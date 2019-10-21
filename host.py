import os, sys, socket, json, colorama, copy, math, time
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


def getEntityData(bullets, players):
	data = ''
	for bullet in bullets:
		# bullets[i] = [(x, y), (vx, vy), bounces]
		(x, y), vel, bounces = bullet
		data += str(x) + ' ' + str(y) + ' ' + str(bounces) + '\n'

	data = data.strip('\n') + '|'

	for name in players:
		# players[name] = [(x, y), (vx, vy), angle, mana, hp, image, socket]
		(x, y), vel, angle, mana, hp, image = players[name][:6]
		# data = 'name image x y vx vy angle mana\n'
		data += name + ' ' + image + ' ' + str(x) + ' ' + str(y) + ' ' + str(angle) + ' ' + str(mana) + ' ' + str(hp) + '\n'

	return data.strip('\n')


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
	hitboxes['dirtball'] = 25, 25, 55, 55

	print('Opening socket...')
	host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host_socket.bind((socket.gethostname(), settings['port']))
	host_socket.listen(5)

	clear()

	spawnpoints = [tuple(settings['spawnpoints'][str(i + 1)]) for i in range(6)]

	my_name = input("What's your name? (16 characters max) ").strip()

	# players[name] = [(x, y), (vx, vy), angle, mana, hp, image, socket]
	players = {my_name: [spawnpoints[0], (0, 0), 0, 0, settings['health'], 'flowerpot1', None]}
	
	# bullets[i] = [(x, y), (vx, vy), bounces]
	bullets = []

	players_count = int(input('How many players? (max 6) ').strip())
	print('\nYour ip is: ' + colored(socket.gethostbyname(socket.gethostname()) + ':' + str(settings['port']), 'green') + '\nCopy it and send it to other players.\n')
	print(colored(my_name, 'green'), 'joined the game')

	for i in range(1, players_count):
		player_socket, address = host_socket.accept()
		name = receive(player_socket).strip()
		players[name] = [spawnpoints[i], (0, 0), 0, 0, settings['health'], 'flowerpot' + str((i)%3 + 1), player_socket]
		print(colored(name, 'cyan'), 'joined the game')

	time.sleep(1)

	print('')

	for name in players:
		player_socket = players[name][-1]
		if player_socket is not None:
			print('send start signal to', colored(name, 'cyan'))
			send(player_socket, '\nStarting game...')

	print('\nStarting game...') # ------------------------------

	size = width, height = settings['size']
	win = pg.display.set_mode(size)

	game_loop = True
	while game_loop:
		for event in pg.event.get():
			if event.type == pg.QUIT:
				game_loop = False
				continue
		
		win.blit(images['bg'], (0, 0))

		game_data = getEntityData(bullets, players)

		for bullet in bullets:
			(x, y), (vx, vy), bounces = bullet

			critic_bounce_number = settings['critic bounce number']


			if bounces < critic_bounce_number:
				dhx1, dhy1, dhx2, dhy2 = hitboxes['dirtball']

				wall_colision = False

				if x + dhx1 <= 0:
					x = -dhx1
					vx = abs(vx)
					wall_colision = True

				if x + dhx2 >= width:
					x = width - dhx2
					vx = -abs(vx)
					wall_colision = True

				if y + dhy1 <= 0:
					y = -dhy1
					vy = abs(vy)
					wall_colision = True

				if y + dhy2 >= height:
					y = height - dhy2
					vy = -abs(vy)
					wall_colision = True

				if wall_colision:
					bounces += 1

				x += vx
				y += vy

				bullet[0] = x, y
				bullet[1] = vx, vy
				bullet[2] = bounces

				rect1 = pg.Rect(x + dhx1, y + dhy1, dhx2 - dhx1, dhy2 - dhy1)
				for name in players:
					player = players[name]
					px, py = player[0]
					phx1, phy1, phx2, phy2 = hitboxes[player[5]]
					rect2 = pg.Rect(px + phx1, py + phy1, phx2 - phx1, phy2 - phy1)
					if rect1.colliderect(rect2):
						bounces = bullet[2] = critic_bounce_number
						player[4] -= 1

				win.blit(images['dirtball1'], (x, y))

			else:
				if bounces >= critic_bounce_number:
					bounces += 1
					img = 'dirtball2'

				frames = settings['dirt die frames']

				if bounces >= critic_bounce_number + frames:
					bounces += 1
					img = 'dirtball3'

				win.blit(images[img], (x, y))
				bullet[2] = bounces

				if bounces >= critic_bounce_number + frames * 2:
					bullets.remove(bullet)
					

		new_players = {}
		for name in players:
			player = copy.deepcopy(players[name][:-1]) + [players[name][-1]]
			# players[name] = [(x, y), (vx, vy), angle, mana, image, socket]
			(x, y), (vx, vy), angle, mana, hp, image, player_socket = player
			if player_socket is not None:
				send(player_socket, game_data)
				mp, mx, my, z, s, q, d = [int(i) for i in receive(player_socket).split()]
			else:
				mp = pg.mouse.get_pressed()[0]
				mx, my = pg.mouse.get_pos()
				keys = pg.key.get_pressed()
				z = keys[pg.K_w]
				s = keys[pg.K_s]
				q = keys[pg.K_a]
				d = keys[pg.K_d]

			# --- logic --- #

			a = 1
			max_v = 8
			min_v = 0.1

			# key inputs

			if hp > 0:
				if q:
					vx -= a

				if d:
					vx += a

				if z:
					vy -= a

				if s:
					vy += a

			# settings limits

			if vx > max_v:
				vx = max_v

			if vx < -max_v:
				vx = -max_v

			if vy > max_v:
				vy = max_v

			if vy < -max_v:
				vy = -max_v

			# colisions with hitbox

			hx1, hy1, hx2, hy2 = hitboxes[image]

			if x + hx1 <= 0:
				x = -hx1
				vx = abs(vx)

			if x + hx2 >= width:
				x = width - hx2
				vx = -abs(vx)

			if y + hy1 <= 0:
				y = -hy1
				vy = abs(vy)

			if y + hy2 >= height:
				y = height - hy2
				vy = -abs(vy)

			vx *= 0.9
			vy *= 0.9

			if abs(vx) < min_v:
				vx = 0

			if abs(vy) < min_v:
				vy = 0

			x += vx
			y += vy

			player[0] = x, y
			player[1] = vx, vy

			cx = (2 * x + hx1 + hx2) / 2
			cy = (2 * y + hy1 + hy2) / 2
			angle = player[2] = math.atan2(mx - cx, my - cy) - math.pi / 2

			# shooting

			mana = player[3] = mana + 1
			if mana > 30 and mp and hp > 0:
				mana = player[3] = 0
				speed = 10

				bw, bh = images['dirtball1'].get_rect().size
				bx, by = rotate((cx + 54, cy), (cx, cy), -angle)
				bullets.append([(bx - bw / 2, by - bh / 2), (math.cos(-angle) * speed, math.sin(-angle) * speed), 0])

			# pointer

			blit_pointer = False
			if player_socket is None:
				blit_pointer = True
				pointer_image = pg.transform.rotate(images['pointer'], angle * 180 / math.pi)
				pw, ph = pointer_image.get_rect().size
				px, py = rotate((cx + 54, cy), (cx, cy), -angle)
				px, py = px - pw / 2, py - ph / 2

			new_players[name] = player

			# --- graphics --- #

			if hp < 1:
				image = 'dead' + image
			win.blit(images[image], (x, y))
			if blit_pointer:
				win.blit(pointer_image, (px, py))

		players = new_players

		pg.display.update()

	print('')

	for name in players:
		player_socket = players[name][-1]
		if player_socket is not None:
			print('send stop signal to', colored(name, 'cyan'))
			send(player_socket, 'stop')

	print('\nend')



if __name__ == '__main__':
	input('Please use "Gardenwar.exe" to lunch the game.')