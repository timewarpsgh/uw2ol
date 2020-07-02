import pygame
import pygame_gui
import sys
from twisted.internet import reactor
import constants as c
from role import Role, Ship, Mate

# code relocated to these files
import draw
import gui
import handle_pygame_event
import handle_gui_event
import client_packet_received

from gui import SelectionListWindow, ButtonClickHandler


def test():
    print('testing')


class Game():
    def __init__(self):
        # pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        pygame.display.set_caption(c.CAPTION)
        self.screen_surface = pygame.display.set_mode([c.WINDOW_WIDTH, c.WINDOW_HIGHT])
        handle_pygame_event.init_key_mappings(self)

        # gui
        gui.init_gui(self)

        # connection
        self.connection = None

        # roles (data)
        self.my_role = None
        self.other_roles = {}
        self.all_roles = {}

        # load assets
        self.font = None
        self.images = {}
        self.load_assets()

        # test looping event
        # pygame.time.set_timer(EVENT_MOVE, 50)
        # pygame.time.set_timer(EVENT_HEART_BEAT, 1000)
        self.move_direction = 1
        self.move_count = 0

    def load_assets(self):
        # maps
        self.images['port'] = pygame.image.load("./assets/port.png").convert_alpha()
        self.images['sea'] = pygame.image.load("./assets/sea.png").convert_alpha()
        self.images['battle'] = pygame.image.load("./assets/battle.png").convert_alpha()

        # sprite
        self.images['ship_at_sea'] = pygame.image.load("./assets/ship_at_sea.png").convert_alpha()
        self.images['person_in_port'] = pygame.image.load("./assets/person_in_port.png").convert_alpha()

        # font
        self.font = pygame.font.SysFont("fangsong", 24)

    def update(self):
        """called each frame"""
        self.process_input_events()
        draw.draw(self)

    def process_input_events(self):
        # update ui
        time_delta = self.clock.tick(60) / 1000.0
        self.ui_manager.update(time_delta)

        # get events
        events = pygame.event.get()

        # iterate events
        for event in events:
            handle_pygame_event.handle_pygame_event(self, event)
            handle_gui_event.handle_gui_event(self, event)

    def get_connection(self, obj):
        """get protocol object to access network functions"""
        self.connection = obj

    def pck_received(self, pck_type, message_obj):
        client_packet_received.process_packet(self, pck_type, message_obj)

    def change_and_send(self, protocol_name, params_list):
        self.connection.send(protocol_name, params_list)
        try:
            func = getattr(self.my_role, protocol_name)
            func(params_list)
        except:
            pass
