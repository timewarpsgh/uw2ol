import numpy as np
from PIL import Image
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data
import pygame

class MapMaker():
    def __init__(self):
        pass

    def make_port_piddle_and_map(self, port_index):
        """make a port's tile matrix and image"""
        # make piddle
        port_piddle = self.make_port_piddle(port_index)

        # make map
        port_map_pil_img = self.make_port_map(port_piddle, port_index)
        mode = port_map_pil_img.mode
        size = port_map_pil_img.size
        data = port_map_pil_img.tobytes()

        port_map = pygame.image.fromstring(data, size, mode)

        # ret
        return (port_piddle, port_map)

    def make_port_piddle(self, port_index):
        """piddle is a 2D-array(matrix)"""
        # get path
        port_index_with_leading_zeros = str(port_index).zfill(3)
        map_path = f"./assets/images/ports/PORTMAP.{port_index_with_leading_zeros}"

        # get piddle
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
                left = i * c.PIXELS_COVERED_EACH_MOVE
                upper = r * c.PIXELS_COVERED_EACH_MOVE
                position = (left, upper)
                img = port_tiles[port_piddle[r, i]]
                port_img.paste(img, position)

        # ret
        return port_img

    def set_world_map_tiles(self):
        # read img
        img = Image.open(f"./assets/images/world_map/w_map regular tileset.png")

        # cut to tiles
        world_map_tiles = ['']
        for k in range(8):
            for i in range(16):
                left = i * c.PIXELS_COVERED_EACH_MOVE
                upper = k * c.PIXELS_COVERED_EACH_MOVE
                width = height = c.PIXELS_COVERED_EACH_MOVE
                right = left + width
                lower = upper + height

                region = (left, upper, right, lower)
                img_cropped = img.crop(region)
                world_map_tiles.append(img_cropped)

        # set
        self.world_map_tiles = world_map_tiles

    def set_world_piddle(self):
        """world map(sea) matrix"""
        # columns and rows
        COLUMNS = 12 * 2 * 30 * 3;
        ROWS = 12 * 2 * 45;

        # get piddle from txt
        num_array = ''
        with open("./assets/images/world_map/w_map_piddle_array.txt", 'r') as myfile:
            num_array = myfile.read()

        nums_list = num_array.split(',')
        piddle = np.array(nums_list)
        piddle = piddle.reshape(ROWS, COLUMNS)

        # set
        self.world_map_piddle = piddle

    def make_partial_world_map(self, x_tile, y_tile):
        """a small rectangular part of the world map.
            can be used after setting world_map_tiles and world_map_piddle.
        """
        # set partial_map_center
        self.x_tile = x_tile
        self.y_tile = y_tile

        # sea image with size 73 * 73
        COLUMNS = ROWS = c.PARTIAL_WORLD_MAP_TILES
        sea_img = Image.new('RGB', (COLUMNS * c.PIXELS_COVERED_EACH_MOVE, ROWS * c.PIXELS_COVERED_EACH_MOVE), 'red')
        HALF_TILES = c.PARTIAL_WORLD_MAP_TILES_IN_ONE_DIRECTION
        sea_piddle = self.world_map_piddle[y_tile-HALF_TILES:y_tile+HALF_TILES+1, x_tile-HALF_TILES:x_tile+HALF_TILES+1]
        print(sea_piddle.shape)

        # small piddle to image
        for r in range(ROWS):
            for i in range(COLUMNS):
                left = i * c.PIXELS_COVERED_EACH_MOVE
                upper = r * c.PIXELS_COVERED_EACH_MOVE
                position = (left, upper)
                img = self.world_map_tiles[int(sea_piddle[r, i])]
                sea_img.paste(img, position)

        # PIL image to pygame image
        mode = sea_img.mode
        size = sea_img.size
        data = sea_img.tobytes()
        sea_img = pygame.image.fromstring(data, size, mode)

        # set to not drawing
        self.drawing_partial_map = False

        # ret
        return sea_img

        # sea_img.save("sea_img.png")

    def make_world_map(self):
        pass

if __name__ == '__main__':
    map_maker = MapMaker()
    map_maker.set_world_map_tiles()
    map_maker.set_world_piddle()
    map_maker.make_partial_world_map(900, 262)

