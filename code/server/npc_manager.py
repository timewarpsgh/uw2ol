# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

import random

from role import Role, Ship, Mate, init_one_default_npc, Path
from hashes.hash_paths import hash_paths
import constants as c

class NpcManager:
    def __init__(self, aoi_manager):
        self.aoi_manager = aoi_manager
        self.npcs = self._init_npcs()

    def _init_npcs(self):
        npcs = {}
        npc_count = c.NPC_COUNT  # 2k no problem now
        for i in range(1, (npc_count + 1)):
            # store in dict
            npcs[str(i)] = init_one_default_npc(str(i))

        return npcs

    def get_all_npcs(self):
        return self.npcs

    def get_npc_by_name(self, name):
        return self.npcs[name]

    def update(self):
        """called each second"""
        for name, npc in self.npcs.items():
            # at sea
            if npc.map == 'sea':
                # self._random_move(npc)
                # self._let_one_npc_move_along_path(npc)
                pass
            # in battle
            else:
                if npc.your_turn_in_battle:
                    self._npc_change_and_send('all_ships_operate', [name], npc.map)

    def _random_move(self, npc):
        random_direction = random.choice(['up', 'down', 'right', 'left'])
        self._npc_change_and_send('move', [random_direction, npc.name], npc.map)

    def _let_one_npc_move_along_path(self, npc):
        # get path and direction
        path = None
        if npc.point_in_path_id == 0:
            # init start and end
            npc.out_ward = True
            npc.end_port_id = random.choice(list(hash_paths[npc.start_port_id].keys()))
            self._npc_change_and_send('start_moving_out', [npc.end_port_id, npc.name], npc.map)

            path = Path(npc.start_port_id, npc.end_port_id)
        else:
            # get path from start and end ids
            path = Path(npc.start_port_id, npc.end_port_id)
            if (npc.point_in_path_id + 1) == len(path.list_of_points):
                npc.out_ward = False
                self._npc_change_and_send('start_moving_back', [npc.name], npc.map)
        # change index
        if npc.out_ward:
            npc.point_in_path_id += 1
        else:
            npc.point_in_path_id -= 1

        # get next point and move to it
        next_point = path.list_of_points[npc.point_in_path_id]
        next_x = next_point[0]
        next_y = next_point[1]
        self._move_to_next_point(npc, next_x, next_y)

    def _move_to_next_point(self, npc, next_x, next_y):
        # get now position
        now_x = int(npc.x / c.PIXELS_COVERED_EACH_MOVE)
        now_y = int(npc.y / c.PIXELS_COVERED_EACH_MOVE)

        # get direction
        direction = None

        if next_y < now_y and next_x == now_x:
            direction = 'up'
        elif next_y > now_y and next_x == now_x:
            direction = 'down'
        elif next_y == now_y and next_x < now_x:
            direction = 'left'
        elif next_y == now_y and next_x > now_x:
            direction = 'right'

        elif next_y < now_y and next_x > now_x:
            direction = 'ne'
        elif next_y < now_y and next_x < now_x:
            direction = 'nw'
        elif next_y > now_y and next_x > now_x:
            direction = 'se'
        elif next_y > now_y and next_x < now_x:
            direction = 'sw'

        self._npc_change_and_send('move', [direction, npc.name], npc.map)
        self._grid_change(npc)

    def _npc_change_and_send(self, protocol_name, params_list, broadcast_map):
        """change local state and send cmd to clients"""
        npc_name = params_list[-1]

        npc = self.get_npc_by_name(npc_name)
        # local change
        try:
            func = getattr(npc, protocol_name)
            func([params_list[0]])
        except:
            print(f'invalid input!!!!!!!! {npc}')
            return False

        # send to players
        else:
            # tell players in same map('sea')
            npc_map = self.aoi_manager.get_map_by_player(npc)
            nearby_players = npc_map.get_nearby_players_by_player(npc)
            for name, conn in nearby_players.items():
                if name.isdigit():
                    pass
                else:
                    conn.send(protocol_name, params_list)

    def _npc_send_to_players(self, protocol_name, params_list, broadcast_map):
        npc_name = params_list[-1]
        # tell players in same map('sea')
        if broadcast_map in self.users:
            for name, conn in self.users[broadcast_map].items():
                if name == 'npcs' or str(name).isdigit():
                    pass
                else:
                    conn.send(protocol_name, params_list)

    def _grid_change(self, npc):
        # have changed grid?
        now_grid_id = None
        x_tile_pos, y_tile_pos = npc.get_x_and_y_tile_position()
        my_map = Role.AOI_MANAGER.get_map_by_player(npc)
        now_grid_id = my_map.get_grid_id_by_x_and_y_tile_position(x_tile_pos, y_tile_pos)

        if now_grid_id != npc.grid_id:
            # change my grid
            map = Role.AOI_MANAGER.get_map_by_player(npc)
            map.move_npc_to_new_grid(npc, now_grid_id)

            # get new and delete grids
            new_grids, delete_grids = map.get_new_and_delete_grids_after_movement(now_grid_id, npc.direction)

            # tell roles in delete grids someone disappeared
            for grid in delete_grids:
                for name, conn in grid.roles.items():
                    if name.isdigit():
                        pass
                    else:
                        conn.send('role_disappeared', npc.name)

            # tell roles in new girds someone appeared
            for grid in new_grids:
                for name, conn in grid.roles.items():
                    if name.isdigit():
                        pass
                    else:
                        conn.send('new_role', npc)


if __name__ == '__main__':
    manager = NpcManager()
    print(len(manager.npcs))




