import constants as c


class Grid:
    """a grid holds a dict of roles """
    def __init__(self):
        self.roles = {}

class Map:
    """a map holds a list of grids"""
    def __init__(self):
        self.grids = []

        # map's length in tiles
        self.x_tile_count = None
        self.y_tile_count = None

        # grid's length in tiles
        self.grid_tile_count = c.GRID_TILES_COUNT

        # map's length in grids
        self.x_grid_count = None
        self.y_grid_count = None

        self.total_num_of_grids = None

    def get_grid_id_by_x_and_y_tile_position(self, x_tile_pos, y_tile_pos):
        grid_x_pos = int(x_tile_pos / self.grid_tile_count)
        grid_y_pos = int(y_tile_pos / self.grid_tile_count)
        grid_id = grid_y_pos * self.x_grid_count + grid_x_pos
        return grid_id

class PortMap(Map):
    def __init__(self):
        Map.__init__(self)
        self.x_tile_count = c.PORT_TILES_COUNT
        self.y_tile_count = c.PORT_TILES_COUNT

        self.x_grid_count = int(self.x_tile_count / self.grid_tile_count) + 1
        self.y_grid_count = self.x_grid_count

        self.total_num_of_grids = self.x_grid_count * self.y_grid_count + 1

        self.grids = [None] * self.total_num_of_grids
        for i in range(0, self.total_num_of_grids):
            self.grids[i] = Grid()

class SeaMap(Map):
    def __init__(self):
        Map.__init__(self)
        self.x_tile_count = c.WORLD_MAP_COLUMNS
        self.y_tile_count = c.WORLD_MAP_ROWS

        self.x_grid_count = int(self.x_tile_count / self.grid_tile_count) + 1
        self.y_grid_count = int(self.y_tile_count / self.grid_tile_count) + 1

        self.total_num_of_grids = self.x_grid_count * self.y_grid_count + 1

        self.grids = [None] * self.total_num_of_grids
        for i in range(0, self.total_num_of_grids):
            self.grids[i] = Grid()


class BattleMap(Map):
    def __init__(self):
        Map.__init__(self)


class AOIManager:
    """Area of Interest Manager has many maps"""
    def __init__(self):
        # sea
        self.sea = SeaMap()

        # ports, map_id 0 - 130
        port_count = 131
        self.ports = [None] * port_count
        for i in range(port_count):
            self.ports[i] = PortMap()

        # keys are the names of initiators
        self.battle_fields = {
            'alex': BattleMap(),
        }

    def get_sea_map(self):
        return self.sea

    def get_port_map_by_id(self, map_id):
        return self.ports[map_id]

    def get_battle_map_player_name(self, name):
        return self.battle_fields[name]

if __name__ == '__main__':
    aoi_manager = AOIManager()
    sea_map = aoi_manager.get_sea_map()
    port_map = aoi_manager.get_port_map_by_id(0)
    battle_map = aoi_manager.get_battle_map_player_name('alex')

    print(port_map.grids[64])

    a = port_map.get_grid_id_by_x_and_y_tile_position(96, 96)
    print(a)

    print(sea_map.x_grid_count, sea_map.y_grid_count)
    print(len(sea_map.grids))

    print(sea_map.get_grid_id_by_x_and_y_tile_position(900, 262))