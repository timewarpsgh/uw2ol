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

PORT_MAP_SIZE = 96 * 3

# assets
HUD_WIDTH, HUD_HIGHT = 110, 400
BUILDING_PERSON_WIDTH, BUILDING_PERSON_HIGHT = 138, 114
BUILDING_CHAT_WIDTH, BUILDING_CHAT_HIGHT = 480, 129
BUILDING_BG_SIZE = 500


# daemon mode (print to STDOUT?)
DAEMON_MODE = False

# Database
SAVE_ON_CONNECTION_LOST = True
SET_ONLINE_TO_TRUE_ON_LOGIN = False

# network
REMOTE_ON = False
HOST = 'localhost'
PORT = 8082
REMOTE_HOST = '129.28.172.72'
REMOTE_PORT = 8082

HEADER_SIZE = 4
OBJECT_SIZE = 4

# color
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

# player data
PIXELS_COVERED_EACH_MOVE = 16
MOVE_TIME_INVERVAL = 0.01
DEVELOPER_MODE_ON = True
ALTERNATIVE_DIRECTIONS = {
    'up': ['ne', 'nw'],
    'down': ['se', 'sw'],
    'right': ['ne', 'se'],
    'left': ['nw', 'sw'],
    'ne': ['up', 'right'],
    'nw': ['up', 'left'],
    'se': ['right', 'down'],
    'sw': ['down', 'left'],
}
MOVE_DX_DY = {
    'up': [0, -1],
    'down': [0, 1],
    'right': [1, 0],
    'left': [-1, 0],
    'ne': [1, -1],
    'nw': [-1, -1],
    'se': [1, 1],
    'sw': [-1, 1],
}
SEA_MOVE_COLLISION_TILES = {
    'up': [[-1, 0], [-1, 1]],
    'down': [[2, 0], [2, 1]],
    'right': [[0, 2], [1, 2]],
    'left': [[0, -1], [1, -1]],
    'ne': [[-1, 1], [-1, 2], [0, 2]],
    'nw': [[0, -1], [-1, -1], [-1, 0]],
    'se': [[1, 2], [2, 2], [2, 1]],
    'sw': [[2, 0], [2, -1], [1, -1]],
}

NEW_AND_DELETE_GRIDS_AFTER_4_BASIC_MOVEMENTS = {
    'up': {
        'new':['-1', -1, 1],
        'delete':['2', -1, 1],
    },
    'down': {
        'new':['1', -1, 1],
        'delete':['-2', -1, 1],
    },
    'right': {
        'new':[1, '-1', '1'],
        'delete':[-2, '-1', '1'],
    },
    'left': {
        'new':[-1, '-1', '1'],
        'delete':[2, '-1', '1'],
    },
}

NEW_AND_DELETE_GRIDS_AFTER_4_ADDITIONAL_MOVEMENTS = {
    'ne': {
        'new':[['-1', -1], 1, 1, '1', '1'],
        'delete':[-2, '1', '1', 1, 1],
    },
    'nw': {
        'new':[[-1, '1'], '-1', '-1', 1, 1],
        'delete':['2', 1, 1, '-1', '-1'],
    },
    'se': {
        'new':[[-1, '1'], 1, 1, '-1', '-1'],
        'delete':[-2, '-1', '-1', 1, 1],
    },
    'sw': {
        'new':[[-1, '-1'], '1', '1', 1, 1],
        'delete':['-2', 1, 1, '1', '1'],
    },
}

MAX_ITEMS_IN_BAG = 30

# in battle
BATTLE_TILE_SIZE = 32
THINK_TIME_IN_BATTLE = 30
MAX_STEPS_IN_BATTLE = 6
SHOOT_RANGE_IN_BATTLE = 4
ENGAGE_DAMAGE = 1
SHOOT_DAMAGE = 100


# world constants
CREW_UNIT_COST = 100
SUPPLY_UNIT_COST = 5
SUPPLY_CONSUMPTION_PER_PERSON = 0.001 # 0.1
ONE_DAY_AT_SEA_IN_SECONDS = 3
TIME_OF_DAY_OPTIONS = ['dawn', 'day', 'dusk', 'night']
EXP_GOT_MODIFIER = 10
EXP_PER_DISCOVERY = 500
GOLD_REWARD_FOR_HANDING_IN_QUEST = 3000
MAX_LV = 60
PORT_COUNT = 130
PORTS_ALLIED_NATION_AND_PRICE_INDEX_CHANGE_INTERVAL_SECONDS = 60 * 120


# player image
SHIP_SIZE_IN_PIXEL = 32
PERSON_SIZE_IN_PIXEL = 32

FIGURE_WIDTH = 65
FIGURE_HIGHT = 81

ITEMS_IMAGE_SIZE = 49

# map data
WALKABLE_TILES = set(range(1, 40))
SAILABLE_TILES = set(range(1, 33))
# SAILABLE_TILES.add(90)

WALKABLE_TILES_FOR_ASIA = set(range(1, 47))
PARTIAL_WORLD_MAP_TILES = 73
PARTIAL_WORLD_MAP_TILES_IN_ONE_DIRECTION = 36
PORT_TILES_COUNT = 96
GRID_TILES_COUNT = 13
LIST_OF_NINE_NONES = [None] * 9
TILES_AROUND_PORTS = [[2, 0], [2, 1], [2, -1], [-2, 0], [-2, 1], [-2, -1],[0, 2], [1, 2], [-1, 2], [0, -2], [1, -2], [-1, -2]]
THREE_NEARBY_TILES_OF_UP_LEFT_TILE = [[1, 0], [0, 1], [1, 1]]

WORLD_MAP_COLUMNS = 12 * 2 * 30 * 3
WORLD_MAP_ROWS = 12 * 2 * 45
WORLD_MAP_TILE_SIZE = 16
WORLD_MAP_X_LENGTH = WORLD_MAP_COLUMNS * WORLD_MAP_TILE_SIZE


WORLD_MAP_EDGE_LENGTH = 40

WORLD_MAP_MAX_Y_TO_DRAW_NEW_PARTIAL_WORLD_MAP = WORLD_MAP_TILE_SIZE * (WORLD_MAP_ROWS - WORLD_MAP_EDGE_LENGTH)
WORLD_MAP_MIN_Y_TO_DRAW_NEW_PARTIAL_WORLD_MAP = WORLD_MAP_TILE_SIZE * WORLD_MAP_EDGE_LENGTH
WORLD_MAP_MIN_X_TO_DRAW_NEW_PARTIAL_WORLD_MAP = WORLD_MAP_TILE_SIZE * WORLD_MAP_EDGE_LENGTH
WORLD_MAP_MAX_X_TO_DRAW_NEW_PARTIAL_WORLD_MAP = WORLD_MAP_TILE_SIZE * (WORLD_MAP_COLUMNS - WORLD_MAP_EDGE_LENGTH)

# port npcs
DOG_FRAME_1_INDEX = 28
DOG_FRAME_2_INDEX = 29
DOG_BUILDING_ID = 2

OLD_MAN_FRAME_1_ID = 26
OLD_MAN_FRAME_2_ID = 27
OLD_MAN_BUILDING_ID = 5

AGENT_FRAME_1_ID = 24
AGENT_FRAME_2_ID = 25
AGENT_BUILDING_ID = 1

# sea npcs
FLEET_COUNT_PER_NATION = 6
NATION_COUNT = 6
NPC_COUNT = 36

# special ids
TAX_FREE_PERMIT_ID = 10


if __name__ == '__main__':
    print(SAILABLE_TILES)