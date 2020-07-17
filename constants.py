"""constants"""

# pygame graphics
CAPTION = 'uncharted waters 2'
WINDOW_WIDTH = 400 + 110*2
WINDOW_HIGHT = 400
FPS = 30.0
FONT_SIZE = 18

# gui graphics
BUTTON_WIDTH, BUTTON_HIGHT = 60, 30
SELECTION_LIST_WIDTH, SELECTION_LIST_HIGHT = 225 , 250
SELECTION_LIST_X, SELECTION_LIST_Y = WINDOW_WIDTH - SELECTION_LIST_WIDTH, 120

# assets
HUD_WIDTH, HUD_HIGHT = 110, 400
BUILDING_PERSON_WIDTH, BUILDING_PERSON_HIGHT = 138, 114
BUILDING_CHAT_WIDTH, BUILDING_CHAT_HIGHT = 480, 129

# daemon mode (print to STDOUT?)
DAEMON_MODE = False

# Database
SAVE_ON_CONNECTION_LOST = False
SET_ONLINE_TO_TRUE_ON_LOGIN = False

# network
REMOTE_ON = False
HOST = 'localhost'
PORT = 8082
REMOTE_HOST = '129.28.172.72'
REMOTE_PORT = 8082

HEADER_SIZE = 4

# color
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# player data
PIXELS_COVERED_EACH_MOVE = 16
MOVE_TIME_INVERVAL = 0.15
DEVELOPER_MODE_ON = True

# world constants
SUPPLY_UNIT_COST = 0.5
ONE_DAY_AT_SEA_IN_SECONDS = 3

# player image
SHIP_SIZE_IN_PIXEL = 32
PERSON_SIZE_IN_PIXEL = 32

# map data
WALKABLE_TILES = SAILABLE_TILES = set(range(1, 32))
PARTIAL_WORLD_MAP_TILES = 73
PARTIAL_WORLD_MAP_TILES_IN_ONE_DIRECTION = 36
