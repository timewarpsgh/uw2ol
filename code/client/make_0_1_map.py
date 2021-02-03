from map_maker import MapMaker
import numpy

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
import constants as c

map_maker = MapMaker()
map_maker.set_world_piddle()

matrix = map_maker.world_map_piddle

matrix = matrix.astype('int')

size = 5
x = 900
y = 262

print(matrix[(y-size):(y+size), (x-size):(x+size)])



list_2d = matrix.tolist()


last_collumn_id = c.WORLD_MAP_COLUMNS - 1
last_row_id = c.WORLD_MAP_ROWS - 1


for collumn in range(0,c.WORLD_MAP_COLUMNS):
    for row in range(0,c.WORLD_MAP_ROWS):
        # last row or collumn
        if collumn == last_collumn_id or row == last_row_id:
            list_2d[row][collumn] = 0

        # others
        else:
            # 4 tiles covering ship image
            v = list_2d[row][collumn]
            v_right = list_2d[row][(collumn+1)]
            v_right_down = list_2d[(row + 1)][(collumn + 1)]
            v_down = list_2d[(row + 1)][collumn]

            # all 4 tiles must be sailable
            can_sail_index = 1
            for value in [v, v_right, v_right_down, v_down]:
                if value in c.SAILABLE_TILES or (value >= 117 and value <= 120):
                    pass
                else:
                    can_sail_index = 0
                    break

            list_2d[row][collumn] = can_sail_index

new_matrix = numpy.array(list_2d)

print(new_matrix[(y-size):(y+size), (x-size):(x+size)])

