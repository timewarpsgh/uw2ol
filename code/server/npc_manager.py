# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

import random

from role import Role, Ship, Mate, init_one_default_npc


class NpcManager:
    def __init__(self, users):
        self.npcs = self._init_npcs()
        self.users = users

    def _init_npcs(self):
        npcs = {}
        npc_count = 5  # max is 150 atm due to max protocol size
        for i in range(1, (npc_count + 1)):
            # store in dict
            npcs[str(i)] = init_one_default_npc(str(i))

        return npcs

    def update(self):
        """called each second"""
        for name, npc in self.npcs.items():
            # at sea
            if npc.map == 'sea':
                random_direction = random.choice(['up', 'down', 'right', 'left'])
                self._npc_change_and_send('move', [random_direction, name], npc.map)

            # in battle
            else:
                if npc.your_turn_in_battle:
                    self._npc_change_and_send('all_ships_operate', [name], npc.map)

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
            for name, conn in self.users[broadcast_map].items():
                if name == 'npcs' or str(name).isdigit():
                    pass
                else:
                    conn.send(protocol_name, params_list)



if __name__ == '__main__':
    manager = NpcManager()
    print(len(manager.npcs))




