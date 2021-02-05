# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

import constants as c


class Grid:
    """a grid holds a dict of roles """
    def __init__(self):
        self.roles = {}

    def add(self, player_conn):
        name = player_conn.my_role.name
        self.roles[name] = player_conn

    def remove(self, name):
        del self.roles[name]

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

    def get_grid_by_id(self, grid_id):
        return self.grids[grid_id]

    def get_grid_id_by_x_and_y_tile_position(self, x_tile_pos, y_tile_pos):
        grid_x_pos = int(x_tile_pos / self.grid_tile_count)
        grid_y_pos = int(y_tile_pos / self.grid_tile_count)
        grid_id = grid_y_pos * self.x_grid_count + grid_x_pos
        return grid_id

    def get_nearby_grids_by_grid_id(self, grid_id):
        """9 girds normaly"""
        # mid line
        mid_left_id = grid_id - 1
        mid_id = grid_id
        mid_right_id = grid_id + 1

        # up line
        up_left_id = mid_left_id - self.x_grid_count
        up_mid_id = mid_id - self.x_grid_count
        up_right_id = mid_right_id - self.x_grid_count

        # bottom line
        bot_left_id = mid_left_id + self.x_grid_count
        bot_mid_id = mid_id + self.x_grid_count
        bot_right_id = mid_right_id + self.x_grid_count

        # possible ids
        nearby_ids = []
        possible_ids = [mid_left_id, mid_id, mid_right_id, up_left_id, up_mid_id, up_right_id, bot_left_id, bot_mid_id, bot_right_id]
        for id in possible_ids:
            if id >= 0 and id < self.total_num_of_grids:
                nearby_ids.append(id)

        return nearby_ids

    def get_nearby_players_by_player(self, player):
        # get nearby grid ids
        nearby_grid_ids  = self.get_nearby_grids_by_grid_id(player.grid_id)

        # get nearby grids
        grids = []
        for id in nearby_grid_ids:
            grid = self.get_grid_by_id(id)
            grids.append(grid)

        # get all players in these grids
        dic = {}
        for grid in grids:
            grid_dic = grid.roles
            dic =  {**dic, **grid_dic}

        del dic[player.name]

        return dic

    def add_player_conn(self, player_conn):
        role = player_conn.my_role
        x_tile_pos, y_tile_pos = role.get_x_and_y_tile_position()
        grid_id = self.get_grid_id_by_x_and_y_tile_position(x_tile_pos, y_tile_pos)
        grid = self.grids[grid_id]
        grid.add(player_conn)
        role.grid_id = grid_id

    def move_player_conn_to_new_grid(self, player_conn, new_grid_id):
        # delete from prev grid
        player = player_conn.my_role
        grid = self.get_grid_by_id(player.grid_id)
        grid.remove(player.name)

        # add to new grid
        new_grid = self.get_grid_by_id(new_grid_id)
        new_grid.add(player_conn)
        player.grid_id = new_grid_id

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