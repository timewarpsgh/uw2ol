import random

from twisted.internet import reactor, task
from twisted.internet.task import LoopingCall


# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

import constants as c
from hashes.look_up_tables import nation_2_nation_id, capital_map_id_2_nation, \
    done_additional_movements_2_new_and_delete_grids, \
    done_basic_movements_2_new_and_delete_grids


class Grid:
    """a grid holds a dict of roles """
    def __init__(self):
        self.roles = {}

    def add(self, player_conn):
        name = player_conn.my_role.name
        self.roles[name] = player_conn

    def remove(self, name):
        del self.roles[name]

    def add_npc(self, npc):
        self.roles[npc.name] = npc


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

    def is_grid_id_valid(self, grid_id):
        if grid_id >= 0 and grid_id < self.total_num_of_grids:
            return True
        else:
            return False

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
        possible_ids = [mid_left_id, mid_id, mid_right_id,
                        up_left_id, up_mid_id, up_right_id,
                        bot_left_id, bot_mid_id, bot_right_id]
        for id in possible_ids:
            if self.is_grid_id_valid(id):
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

        if player.name in dic:
            del dic[player.name]

        return dic

    def _possible_grid_ids_2_real_grids(self, possible_grid_ids):
        # get ids
        grid_ids = []
        for id in possible_grid_ids:
            if self.is_grid_id_valid(id):
                grid_ids.append(id)

        # get grids
        grids = []
        for id in grid_ids:
            grid = self.get_grid_by_id(id)
            grids.append(grid)

        return grids

    def get_new_and_delete_grids_after_movement(self, new_grid_id, direction):
        # basic 4 directions
        if direction in done_basic_movements_2_new_and_delete_grids:
            return self._get_new_and_delete_grids_after_basic_movement\
                (new_grid_id, direction)

        # additional 4 directions
        elif direction in done_additional_movements_2_new_and_delete_grids:
            return self._get_new_and_delete_grids_after_additional_movement\
                (new_grid_id, direction)

    def _get_new_and_delete_grids_after_basic_movement(self, new_grid_id, direction):
        # new
        new_deltas = done_basic_movements_2_new_and_delete_grids[direction]['new']
        for index, delta in enumerate(new_deltas):
            if isinstance(delta, str):
                new_deltas[index] = int(delta) * self.x_grid_count

        new_mid_grid_id = new_grid_id + new_deltas[0]
        new_left_grid_id = new_mid_grid_id + new_deltas[1]
        new_right_grid_id = new_mid_grid_id + new_deltas[2]

        possible_new_grid_ids = [new_left_grid_id, new_mid_grid_id, new_right_grid_id]
        new_grids = self._possible_grid_ids_2_real_grids(possible_new_grid_ids)

        # delete
        delete_deltas = done_basic_movements_2_new_and_delete_grids[direction]['delete']
        for index, delta in enumerate(delete_deltas):
            if isinstance(delta, str):
                delete_deltas[index] = int(delta) * self.x_grid_count

        delete_mid_grid_id = new_grid_id + delete_deltas[0]
        delete_left_grid_id = delete_mid_grid_id + delete_deltas[1]
        delete_right_grid_id = delete_mid_grid_id + delete_deltas[2]

        possible_delete_grid_ids = [delete_left_grid_id, delete_mid_grid_id, delete_right_grid_id]
        delete_grids = self._possible_grid_ids_2_real_grids(possible_delete_grid_ids)

        # ret
        return new_grids, delete_grids

    def _get_new_and_delete_grids_after_additional_movement(self, new_grid_id, direction):
        # new
        new_deltas = done_additional_movements_2_new_and_delete_grids[direction]['new']
        for index, delta in enumerate(new_deltas):
            if index == 0:
                list = new_deltas[index]
                for id, inner_delta in enumerate(list):
                    if isinstance(inner_delta, str):
                        list[id] = int(inner_delta) * self.x_grid_count
            else:
                if isinstance(delta, str):
                    new_deltas[index] = int(delta) * self.x_grid_count

        new_grid_1 = new_grid_id + new_deltas[0][0] + new_deltas[0][1]
        new_grid_2 = new_grid_1 + new_deltas[1]
        new_grid_3 = new_grid_2 + new_deltas[2]
        new_grid_4 = new_grid_3 + new_deltas[3]
        new_grid_5 = new_grid_4 + new_deltas[4]

        possible_new_grid_ids = [new_grid_1, new_grid_2, new_grid_3, new_grid_4, new_grid_5]
        new_grids = self._possible_grid_ids_2_real_grids(possible_new_grid_ids)

        # delete
        delete_deltas = done_additional_movements_2_new_and_delete_grids[direction]['delete']
        for index, delta in enumerate(delete_deltas):
            if isinstance(delta, str):
                delete_deltas[index] = int(delta) * self.x_grid_count

        delete_grid_1 = new_grid_id + delete_deltas[0]
        delete_grid_2 = delete_grid_1 + delete_deltas[1]
        delete_grid_3 = delete_grid_2 + delete_deltas[2]
        delete_grid_4 = delete_grid_3 + delete_deltas[3]
        delete_grid_5 = delete_grid_4 + delete_deltas[4]

        possible_delete_grid_ids = [delete_grid_1, delete_grid_2,
                                    delete_grid_3, delete_grid_4, delete_grid_5]
        delete_grids = self._possible_grid_ids_2_real_grids(possible_delete_grid_ids)

        # ret
        return new_grids, delete_grids

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

    def remove_player(self, player):
        grid = self.get_grid_by_id(player.grid_id)
        grid.remove(player.name)

    def add_npc(self, npc):
        x_tile_pos, y_tile_pos = npc.get_x_and_y_tile_position()
        grid_id = self.get_grid_id_by_x_and_y_tile_position(x_tile_pos, y_tile_pos)
        grid = self.grids[grid_id]
        grid.add_npc(npc)
        npc.grid_id = grid_id

    def move_npc_to_new_grid(self, npc, new_grid_id):
        # delete from prev grid
        grid = self.get_grid_by_id(npc.grid_id)
        grid.remove(npc.name)

        # add to new grid
        new_grid = self.get_grid_by_id(new_grid_id)
        new_grid.add_npc(npc)
        npc.grid_id = new_grid_id


class PortMap(Map):
    def __init__(self, map_id=1):
        Map.__init__(self)

        # fill empty fields
        self.x_tile_count = c.PORT_TILES_COUNT
        self.y_tile_count = c.PORT_TILES_COUNT

        self.x_grid_count = int(self.x_tile_count / self.grid_tile_count) + 1
        self.y_grid_count = self.x_grid_count

        self.total_num_of_grids = self.x_grid_count * self.y_grid_count + 1

        self.grids = [None] * self.total_num_of_grids
        for i in range(0, self.total_num_of_grids):
            self.grids[i] = Grid()

        # allied nation and price index
        self.nation = None
        self.price_index = None
        self.economy = None
        self.industry = None

        self.owner = None
        self.owner_nation = None
        self.deposit_ingots = None
        self.got_tax = {}
        self.mode = 'easy'


        self.map_id = map_id

    def set_allied_nation(self, nation):
        self.nation = nation

    def set_price_index(self, pi):
        self.price_index = pi

class WindWaveMgr:
    """winds and waves (the same no matter where you are)"""

    def __init__(self):
        self.wind_speed = random.randint(0, c.MAX_WIND_OR_WAVE)
        self.wind_direction = random.choice(c.EIGHT_DIRECTIONS)
        self.wave_speed = random.randint(0, c.MAX_WIND_OR_WAVE)
        self.wave_direction = random.choice(c.EIGHT_DIRECTIONS)

    def change(self):
        int = random.randint(0, 9)
        if int >= 7:
            self.wind_speed = random.randint(0, c.MAX_WIND_OR_WAVE)
            self.wind_direction = random.choice(c.EIGHT_DIRECTIONS)
            self.wave_speed = random.randint(0, c.MAX_WIND_OR_WAVE)
            self.wave_direction = random.choice(c.EIGHT_DIRECTIONS)

class SeaMap(Map):
    def __init__(self):
        Map.__init__(self)

        # grids
        self.x_tile_count = c.WORLD_MAP_COLUMNS
        self.y_tile_count = c.WORLD_MAP_ROWS

        self.x_grid_count = int(self.x_tile_count / self.grid_tile_count) + 1
        self.y_grid_count = int(self.y_tile_count / self.grid_tile_count) + 1

        self.total_num_of_grids = self.x_grid_count * self.y_grid_count + 1

        self.grids = [None] * self.total_num_of_grids
        for i in range(0, self.total_num_of_grids):
            self.grids[i] = Grid()

        # winds and waves
        self.wind_wave_mgr = WindWaveMgr()

    def get_wind_wave_mgr(self):
        return self.wind_wave_mgr

class BattleMap(Map):
    """different from sea or port. has only one grid"""
    def __init__(self):
        Map.__init__(self)
        only_grid = Grid()
        self.grids.append(only_grid)

    def get_nearby_players_by_player(self, player):
        dic = self.grids[0].roles
        return dic

    def get_all_players_inside(self):
        return self.grids[0].roles

    def add_player_conn(self, player_conn):
        self.grids[0].add(player_conn)

    def add_npc(self, npc):
        self.grids[0].add_npc(npc)

class AOIManager:
    """Area of Interest Manager has many maps"""
    def __init__(self):
        # sea
        self.sea = SeaMap()

        # nations ports (each nation has a set of map ids)
        self.nations_ports = {}
        for nation in nation_2_nation_id.keys():
            self.nations_ports[nation] = set()

        # ports
        self.ports = None
        self._init_ports()

        # battle maps (keys are the names of initiators)
        self.battle_fields = {
            'e.g:alex': BattleMap(),
        }

    def _init_ports(self):
        # ports, map_id 0 - 129
        port_count = c.PORT_COUNT
        self.ports = [None] * port_count
        nations = list(nation_2_nation_id.keys())
        for i in range(port_count):
            port_map = PortMap(i)
            rand_nation = random.choice(nations)
            port_map.set_allied_nation(rand_nation)
            self.nations_ports[rand_nation].add(port_map)

            price_index = random.randint(80, 120)
            port_map.set_price_index(price_index)

            port_map.economy = random.randint(1, 1000)
            port_map.industry = random.randint(1, 1000)

            self.ports[i] = port_map

        # capital ports allied to own nation
        for map_id, nation in capital_map_id_2_nation.items():
            port_map = self.ports[map_id]
            prev_nation = port_map.nation
            self.nations_ports[prev_nation].remove(port_map)
            port_map.set_allied_nation(nation)
            self.nations_ports[nation].add(port_map)

        # update nation and PI
        self.timer = task.LoopingCall(self._update_ports_nation_and_price_index)
        self.timer.start(c.PORTS_ALLIED_NATION_AND_PRICE_INDEX_CHANGE_INTERVAL_SECONDS, False)

    def _update_ports_nation_and_price_index(self):
        # ports, map_id 0 - 129
        port_count = c.PORT_COUNT
        nations = list(nation_2_nation_id.keys())
        for i in range(port_count):
            rand_nation = random.choice(nations)
            self.ports[i].set_allied_nation(rand_nation)
            price_index = random.randint(80, 120)
            self.ports[i].set_price_index(price_index)

            self.ports[i].economy = random.randint(1, 1000)
            self.ports[i].industry = random.randint(1, 1000)

        # capital ports allied to own nation
        for map_id, nation in capital_map_id_2_nation.items():
            self.ports[map_id].set_allied_nation(nation)

    def get_sea_map(self):
        return self.sea

    def get_port_map_by_id(self, map_id):
        return self.ports[map_id]

    def get_battle_map_by_player_map(self, player_map):
        return self.battle_fields[player_map]

    def get_map_by_player(self, player):
        if player.map == 'sea':
            return self.sea
        elif player.is_in_port():
            return self.get_port_map_by_id(int(player.map))
        else:
            return self.get_battle_map_by_player_map(player.map)

    def create_battle_map_by_name(self, map_name):
        self.battle_fields[map_name] = BattleMap()
        return self.battle_fields[map_name]

    def delete_battle_map_by_name(self, map_name):
        del self.battle_fields[map_name]

if __name__ == '__main__':
    aoi_manager = AOIManager()
    sea_map = aoi_manager.get_sea_map()
    port_map = aoi_manager.get_port_map_by_id(0)
    battle_map = aoi_manager.get_battle_map_by_player_name('alex')

    print(port_map.grids[64])

    a = port_map.get_grid_id_by_x_and_y_tile_position(96, 96)
    print(a)

    print(sea_map.x_grid_count, sea_map.y_grid_count)
    print(len(sea_map.grids))

    print(sea_map.get_grid_id_by_x_and_y_tile_position(900, 262))