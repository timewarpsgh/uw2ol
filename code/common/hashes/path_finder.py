import numpy
import pickle

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder


# add relative directory to python_path
# import sys, os
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from hash_ports_meta_data import hash_ports_meta_data
from hash_paths import hash_paths

class PathFinder:
    def __init__(self):
        # init map
        map_matrix = pickle.load(open('map_0_1_matrix', "rb"))
        self.map_2d_list = map_matrix.tolist()

        # init finder
        self.finder = AStarFinder(diagonal_movement=DiagonalMovement.always)

    def find_path(self, start_port_id, end_port_id):
        grid = Grid(matrix=self.map_2d_list)

        # get end points' x and y
        start_x = hash_ports_meta_data[start_port_id]['x']
        start_y = hash_ports_meta_data[start_port_id]['y']

        end_x = hash_ports_meta_data[end_port_id]['x']
        end_y = hash_ports_meta_data[end_port_id]['y']

        # find
        start = grid.node(start_x, start_y)
        end = grid.node(end_x, end_y)
        path, runs = self.finder.find_path(start, end, grid)

        # print('operations:', runs, 'path length:', len(path))
        # print('from port ', str(start_port_id))
        print(end_port_id, ': ', path, ',')
        return path


if __name__ == '__main__':
    finder = PathFinder()

    for i in range(31, 34):
        finder.find_path(30, i)


