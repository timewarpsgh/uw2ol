import pygame
import pygame_gui
from twisted.internet import reactor, task

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
import constants as c
from role import Role, Ship, Mate
from map_maker import MapMaker
from translator import Translator


# code relocated to these files
import draw
import gui
import handle_pygame_event
import handle_gui_event
import client_packet_received
from port_npc import Dog


from gui import SelectionListWindow, ButtonClickHandler
from hashes.look_up_tables import id_2_building_type

def test():
    print('testing')


class Game():
    def __init__(self):
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

        # login
        reactor.callLater(1, self.login)
        reactor.callLater(2, self.sail)


    def login(self):
        self.connection.send('login', ['2', '2'])

    def sail(self):
        self.connection.send('change_map', ['sea'])

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


