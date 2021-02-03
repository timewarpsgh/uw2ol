# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

import random

from role import Role, Ship, Mate, init_one_default_npc, Path
from hashes.hash_paths import hash_paths
import constants as c

class NpcManager:
    def __init__(self, users):
        self.npcs = self._init_npcs()
        self.users = users

    def _init_npcs(self):
        npcs = {}
        npc_count = 36  # max is 150 atm due to max protocol size
        for i in range(1, (npc_count + 1)):
            # store in dict
            npcs[str(i)] = init_one_default_npc(str(i))

        return npcs

    def update(self):
        """called each second"""
        for name, npc in self.npcs.items():
            # at sea
            if npc.map == 'sea':
                self._let_one_npc_move_along_path(npc)
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
            path = Path(npc.start_port_id, npc.end_port_id)
        else:
            # get path from start and end ids
            path = Path(npc.start_port_id, npc.end_port_id)
            if (npc.point_in_path_id + 1) == len(path.list_of_points):
                npc.out_ward = False

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

    def _npc_change_and_send(self, protocol_name, params_list, broadcast_map):
        """change local state and send cmd to clients"""
        npc_name = params_list[-1]

        # local change
        try:
            func = getattr(self.npcs[npc_name], protocol_name)
            func([params_list[0]])
        except:
            print('invalid input!')
            return False

        # send to players
        else:
            # tell players in same map('sea')
            if broadcast_map in self.users:
                for name, conn in self.users[broadcast_map].items():
                    if name == 'npcs' or str(name).isdigit():
                        pass
                    else:
                        conn.send(protocol_name, params_list)



if __name__ == '__main__':
    manager = NpcManager()
    print(len(manager.npcs))




