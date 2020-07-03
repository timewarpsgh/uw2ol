"""constants"""

# pygame graphics
CAPTION = 'uncharted waters 2'
WINDOW_WIDTH = 600
WINDOW_HIGHT = 400
FPS = 30.0

# gui graphics
BUTTON_WIDTH, BUTTON_HIGHT = 60, 30

# Database
SAVE_ON_CONNECTION_LOST = False

# network
REMOTE_ON = True
HOST = 'localhost'
PORT = 8082
REMOTE_HOST = 'a2z3673391.51mypc.cn'
REMOTE_PORT = 24241

HEADER_SIZE = 4

# color
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)


# player data
PIXELS_COVERED_EACH_MOVE = 16


# player image
SHIP_SIZE_IN_PIXEL = 32
PERSON_SIZE_IN_PIXEL = 32

# map data
WALKABLE_TILES = SAILABLE_TILES = set(range(1, 32))

