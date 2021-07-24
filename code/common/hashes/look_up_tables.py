# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from helpers import Point


id_2_building_type = {
    1: 'market',
    2: 'bar',
    3: 'dry_dock',
    4: 'harbor',
    5: 'inn',
    6: 'palace',
    7: 'job_house',
    8: 'msc',
    9: 'bank',
    10: 'item_shop',
    11: 'church',
    12: 'fortune_house',
}

nation_2_tax_permit_id = {
    'England': 10,
    'Holland': 11,

    'Portugal': 13,
    'Spain': 14,

    'Italy': 12,
    'Turkey': 15,
}

capital_map_id_2_nation = {
    29: 'England',
    33: 'Holland',

    0: 'Portugal',
    1: 'Spain',

    8: 'Italy',
    2: 'Turkey',
}

capital_map_id_2_ruler_image = {
    29: [12, 2],
    33: [13, 2],

    0: [3, 2],
    1: [5, 2],

    8: [7, 2],
    2: [14, 2],
}

capital_2_port_id = {
    'london': 30,
    'amsterdam': 34,

    'lisbon': 1,
    'seville': 2,

    'genoa': 9,
    'istanbul': 3,
}

nation_2_nation_id = {
    'England': 1,
    'Holland': 2,
    'Portugal': 3,
    'Spain': 4,
    'Italy': 5,
    'Turkey': 6,
}

nation_2_capital = {
    'England': 'london',
    'Holland': 'amsterdam',
    'Portugal': 'lisbon',
    'Spain': 'seville',
    'Italy': 'genoa',
    'Turkey': 'istanbul',
}

lv_2_exp_needed_to_next_lv = {
    1: 400,
    2: 800,
    3: 1400,
    4: 2000,
    5: 2800,
    6: 3600,
    7: 4400,
    8: 5400,
    9: 6400,
    10: 7600,
    11:	8700,
    12:	9800,
    13:	11000,
    14:	12300,
    15:	13600,
    16:	15000,
    17:	16400,
    18:	17800,
    19:	19300,
    20:	20800,
    21:	22400,
    22:	24000,
    23:	25600,
    24:	27200,
    25:	28900,
    26:	30500,
    27:	32200,
    28:	33900,
    29:	36300,
    30:	38800,
    31:	41600,
    32:	44700,
    33:	48000,
    34:	51400,
    35:	55000,
    36:	58600,
    37:	62400,
    38:	66200,
    39:	70200,
    40:	74300,
    41:	78500,
    42:	82800,
    43:	87100,
    44:	91700,
    45:	96300,
    46:	101000,
    47:	105800,
    48:	110700,
    49:	115800,
    50:	120900,
    51:	126100,
    52:	131500,
    53:	137000,
    54:	142500,
    55:	148200,
    56:	154000,
    57:	159900,
    58:	165900,
    59:	172000,
}

now_direction_to_next_left_move = {
    'right': 'ne',
    'left': 'sw',
    'up': 'nw',
    'down': 'se',

    'ne': 'up',
    'sw': 'down',
    'nw': 'left',
    'se': 'right',
}

now_direction_to_next_right_move = {
    'right': 'se',
    'left': 'nw',
    'up': 'ne',
    'down': 'sw',

    'ne': 'right',
    'sw': 'left',
    'nw': 'up',
    'se': 'down',
}

ship_direction_2_vector = {
    'up': [Point(0, 0), Point(0, 1)],
    'down': [Point(0, 0), Point(0, -1)],
    'left': [Point(0, 0), Point(-1, 0)],
    'right': [Point(0, 0), Point(1, 0)],
    'ne': [Point(0, 0), Point(1, 1)],
    'sw': [Point(0, 0), Point(-1, -1)],
    'nw': [Point(0, 0), Point(-1, 1)],
    'se': [Point(0, 0), Point(1, -1)]
}

ship_direction_2_next_pos_delta = {
    # basic 4
    'up': {
        'continue': [0, -1],
        'left': [-1, -1],
        'right': [1, -1],
    },
    'down': {
        'continue': [0, 1],
        'left': [1, 1],
        'right': [-1, 1],
    },
    'left': {
        'continue': [-1, 0],
        'left': [-1, 1],
        'right': [-1, -1],
    },
    'right': {
        'continue': [1, 0],
        'left': [1, -1],
        'right': [1, 1],
    },

    # more 4
    'ne': {
        'continue': [1, -1],
        'left': [0, -1],
        'right': [1, 0],
    },
    'sw': {
        'continue': [-1, 1],
        'left': [0, 1],
        'right': [-1, 0],
    },
    'nw': {
        'continue': [-1, -1],
        'left': [-1, 0],
        'right': [0, -1],
    },
    'se': {
        'continue': [1, 1],
        'left': [1, 0],
        'right': [0, 1],
    },
}

now_direct_2_alternative_directs = {
    'up': ['ne', 'nw'],
    'down': ['se', 'sw'],
    'right': ['ne', 'se'],
    'left': ['nw', 'sw'],
    'ne': ['up', 'right'],
    'nw': ['up', 'left'],
    'se': ['right', 'down'],
    'sw': ['down', 'left'],
}

direct_2_dx_and_dy = {
    'up': [0, -1],
    'down': [0, 1],
    'right': [1, 0],
    'left': [-1, 0],
    'ne': [1, -1],
    'nw': [-1, -1],
    'se': [1, 1],
    'sw': [-1, 1],
}

direct_2_sea_move_collision_tiles = {
    'up': [[-1, 0], [-1, 1]],
    'down': [[2, 0], [2, 1]],
    'right': [[0, 2], [1, 2]],
    'left': [[0, -1], [1, -1]],
    'ne': [[-1, 1], [-1, 2], [0, 2]],
    'nw': [[0, -1], [-1, -1], [-1, 0]],
    'se': [[1, 2], [2, 2], [2, 1]],
    'sw': [[2, 0], [2, -1], [1, -1]],
}

done_basic_movements_2_new_and_delete_grids = {
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

done_additional_movements_2_new_and_delete_grids = {
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

ship_direction_2_wind_direction = {
    'right': 'e',
    'left': 'w',
    'up': 'n',
    'down': 's',
    'ne': 'ne',
    'nw': 'nw',
    'se': 'se',
    'sw': 'sw',
}

ship_direction_2_wind_or_wave_direction_effect = {

    # 4 basics
    'n': {
        'n': 1,
        'nw': 0.5,
        'ne': 0.5,
        'w': 0,
        'e': 0,
        'sw': -0.5,
        'se': -0.5,
        's': -1,
    },

    's': {
        'n': -1,
        'nw': -0.5,
        'ne': -0.5,
        'w': 0,
        'e': 0,
        'sw': 0.5,
        'se': 0.5,
        's': 1,
    },

    'e': {
        'e': 1,
        'ne': 0.5,
        'se': 0.5,
        'n': 0,
        's': 0,
        'nw': -0.5,
        'sw': -0.5,
        'w': -1,
    },

    'w': {
        'e': -1,
        'ne': -0.5,
        'se': -0.5,
        'n': 0,
        's': 0,
        'nw': 0.5,
        'sw': 0.5,
        'w': 1,
    },

    # 4 additionals
    'ne': {
        'ne': 1,
        'n': 0.5,
        'e': 0.5,
        'nw': 0,
        'se': 0,
        'w': -0.5,
        's': -0.5,
        'sw': -1,
    },

    'sw': {
        'ne': -1,
        'n': -0.5,
        'e': -0.5,
        'nw': 0,
        'se': 0,
        'w': 0.5,
        's': 0.5,
        'sw': 1,
    },

    'se': {
        'se': 1,
        's': 0.5,
        'e': 0.5,
        'ne': 0,
        'sw': 0,
        'n': -0.5,
        'w': -0.5,
        'nw': -1,
    },

    'nw': {
        'se': -1,
        's': -0.5,
        'e': -0.5,
        'ne': 0,
        'sw': 0,
        'n': 0.5,
        'w': 0.5,
        'nw': 1,
    },
}