import os

try:
	import termcolor
except Exception:
	os.system('pip install termcolor')

try:
	import colorama
except Exception:
	os.system('pip install colorama')

try:
	import pygame
except Exception:
	os.system('pip install pygame')

import host, client

if input('Are you host? [Y/N] ').strip().upper() == 'Y':
	host.main()
else:
	client.main()