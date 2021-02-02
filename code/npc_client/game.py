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


class Game():
    def __init__(self, ac, psw):
        # ac and psw
        self.ac = ac
        self.psw = psw

        # some stuff
        self.movement = None
        self.connection = None

        # roles (data)
        self.my_role = None
        self.other_roles = {}
        self.all_roles = {}
        Role.GAME = self

        # local data
        self.think_time_in_battle = c.THINK_TIME_IN_BATTLE
        self.time_of_day_index = 0
        self.days_spent_at_sea = 0

        # action sequence
        reactor.callLater(1, self.login)
        reactor.callLater(2, self.sail)
        reactor.callLater(3, self.start_moving)

    # controls
    def login(self):
        self.connection.send('login', [self.ac, self.psw])

    def sail(self):
        if self.my_role:
            self.connection.send('change_map', ['sea'])
        else:
            reactor.callLater(1, self.sail)

    def start_moving(self):
        self.timer = task.LoopingCall(self.move)
        self.timer.start(1)

    def move(self):
        if self.my_role:
            # at sea
            if self.my_role.is_at_sea():
                random_direction = random.choice(['up', 'down', 'right', 'left'])
                self.change_and_send('move', [random_direction])

                # self.change_and_send('move', ['up'])
                # reactor.callLater(0.5, self.change_and_send, 'move', ['down'])

            # in battle
            elif not self.my_role.is_in_port():
                if self.my_role.your_turn_in_battle:
                    self.change_and_send('all_ships_operate', [])


    # essentials
    def get_connection(self, obj):
        """get protocol object to access network functions"""
        self.connection = obj

    def pck_received(self, pck_type, message_obj):
        client_packet_received.process_packet(self, pck_type, message_obj)

    def change_and_send(self, protocol_name, params_list):
        # when logged in
        if self.my_role:
            try:
                func = getattr(self.my_role, protocol_name)
                func(params_list)
            except:
                print('invalid input!')
                return False
            else:
                self.connection.send(protocol_name, params_list)
                return True

        # when not logged in
        else:
            params_list_in_str = [str(i) for i in params_list]
            self.connection.send(protocol_name, params_list_in_str)
            return True


