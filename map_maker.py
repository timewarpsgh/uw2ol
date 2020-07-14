import numpy as np
from PIL import Image
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data

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

    def make_port_map(self, port_piddle, port_index):
        """make port image"""
        # port_id to port_chip_file_num
        port_tile_set = 2 * hash_ports_meta_data[port_index+1]['tileset']
        port_chip_file_num = str(port_tile_set).zfill(3)

        # read img
        img = Image.open(f"./assets/images/ports/PORTCHIP.{port_chip_file_num}  dawn.png")
        CHIP_TILES_COUNT = 16

        # cut to tiles
        port_tiles = ['']
        for k in range(CHIP_TILES_COUNT):
            for i in range(CHIP_TILES_COUNT):
                left = i * c.PIXELS_COVERED_EACH_MOVE
                upper = k * c.PIXELS_COVERED_EACH_MOVE
                width = height = c.PIXELS_COVERED_EACH_MOVE
                right = left + width
                lower = upper + height

                region = (left, upper, right, lower)
                img_cropped = img.crop(region)
                port_tiles.append(img_cropped)

        # make port map image
        MAP_TILES_COUNT = 96
        MAP_SIZE = MAP_TILES_COUNT * CHIP_TILES_COUNT
        port_img = Image.new('RGB', (MAP_SIZE, MAP_SIZE), 'red')

        for r in range(MAP_TILES_COUNT):
            for i in range(MAP_TILES_COUNT):
                left = i * 16
                upper = r * 16
                position = (left, upper)
                img = port_tiles[port_piddle[r, i]]
                port_img.paste(img, position)

        port_img.save('out.png')

    def make_world_piddle(self):
        pass

    def make_world_map(self):
        pass

if __name__ == '__main__':
    map_maker = MapMaker()
    piddle = map_maker.make_port_piddle()
    # print(piddle[0, 10])

    map_maker.make_port_map(piddle, 29)