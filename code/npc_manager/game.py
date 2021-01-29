import pygame
import pygame_gui
import random
from twisted.internet import reactor, task

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
import constants as c
from role import Role, Ship, Mate

# code relocated to these files
import client_packet_received
from hashes.look_up_tables import id_2_building_type

def test():
    print('testing')


class Game():
    def __init__(self):
        # some stuff
        self.connection = None

        # roles (data)
        self.npcs = {}
        self.other_roles = {}
        self.all_roles = {}
        Role.GAME = self

        # action sequence
        reactor.callLater(1, self.login)
        # reactor.callLater(2, self.sail)
        reactor.callLater(3, self.start_moving)

    # controls
    def login(self):
        self.connection.send('npc_login', [])

    def sail(self):
        if self.my_role:
            self.connection.send('change_map', ['sea'])
        else:
            reactor.callLater(1, self.sail)

    def start_moving(self):
        self.timer = task.LoopingCall(self.move)
        self.timer.start(1)

    def move(self):
        if self.npcs:
            for name, npc in self.npcs.items():
                random_direction = random.choice(['up', 'down', 'right', 'left'])
                self.npc_change_and_send('move', [name, random_direction])

                # self.change_and_send('move', ['up'])
                # reactor.callLater(0.5, self.change_and_send, 'move', ['down'])

            # # in battle
            # elif not self.my_role.is_in_port():
            #     if self.my_role.your_turn_in_battle:
            #         self.npc_change_and_send('all_ships_operate', [])


    # essentials
    def get_connection(self, obj):
        """get protocol object to access network functions"""
        self.connection = obj

    def pck_received(self, pck_type, message_obj):
        client_packet_received.process_packet(self, pck_type, message_obj)

    def npc_change_and_send(self, protocol_name, params_list):
        npc_name = params_list[0]

        # when logged in
        if self.npcs:
            try:
                func = getattr(self.npcs[npc_name], protocol_name)
                func(params_list)
            except:
                print('invalid input!')
                return False
            else:
                protocol_name = 'npc_' + protocol_name
                self.connection.send(protocol_name, params_list)
                return True

        # when not logged in
        # else:
        #     params_list_in_str = [str(i) for i in params_list]
        #     self.connection.send(protocol_name, params_list_in_str)
        #     return True


