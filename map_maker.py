import numpy as np

class MapMaker():
    def __init__(self):
        pass

    def make_port_piddle(self, map_path='./assets/images/ports/PORTMAP.029'):
        """piddle is a 2D-array(matrix)"""
        with open(map_path, 'rb') as file:
            bytes = file.read()
            list_of_numbers = list(bytes)
            list_of_numbers = [number + 1 for number in list_of_numbers]

            piddle = np.array(list_of_numbers)
            piddle = piddle.reshape(96, 96)

            return piddle

    def make_port_map(self):
        pass

    def make_world_piddle(self):
        pass

    def make_world_map(self):
        pass

if __name__ == '__main__':
    map_maker = MapMaker()
    piddle = map_maker.make_port_piddle()
    print(piddle[0, 10])