import pygame
import pygame_gui
import sys
from twisted.internet import reactor, task
import constants as c
from role import Role, Ship, Mate
from map_maker import MapMaker

# code relocated to these files
import draw
import gui
import handle_pygame_event
import handle_gui_event
import client_packet_received

from gui import SelectionListWindow, ButtonClickHandler
from hashes.look_up_tables import id_2_building_type

def test():
    print('testing')


class Game():
    def __init__(self):
        # pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        pygame.display.set_caption(c.CAPTION)
        self.screen_surface = pygame.display.set_mode([c.WINDOW_WIDTH, c.WINDOW_HIGHT])
        self.screen_surface_rect = self.screen_surface.get_rect()
        handle_pygame_event.init_key_mappings(self)
        self.movement = None
        self.map_maker = MapMaker()
        self.port_piddle = self.map_maker.make_port_piddle()

        print(self.port_piddle)
        x = 7
        y = 4
        print(self.port_piddle[x-2:x+3, y-2:y+3])

        # loop to change ship frame state
        self.ship_frame = 1
        looping_task = task.LoopingCall(self.change_ship_frame_state)
        looping_task.start(0.5)

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

        # buildings
        self.images['building_bg'] = pygame.image.load("./assets/images/buildings/building_bg.png").convert_alpha()
        self.images['building_chat'] = pygame.image.load("./assets/images/buildings/building_chat.png").convert_alpha()
        for building in id_2_building_type.values():
            try:
                self.images[building] = pygame.image.load(f"./assets/images/buildings/{building}.png").convert_alpha()
            except:
                pass







        # huds
        self.images['hud_left'] = pygame.image.load("./assets/images/huds/hud-left.png").convert_alpha()
        self.images['hud_left'] = pygame.transform.scale(self.images['hud_left'], (c.HUD_WIDTH, c.HUD_HIGHT))

        self.images['hud_right'] = pygame.image.load("./assets/images/huds/hud-right.png").convert_alpha()
        self.images['hud_right'] = pygame.transform.scale(self.images['hud_right'], (c.HUD_WIDTH, c.HUD_HIGHT))

        # sprites
        self.images['ship_at_sea'] = pygame.image.load("./assets/ship_at_sea.png").convert_alpha()
        self.images['person_in_port'] = pygame.image.load("./assets/person_in_port.png").convert_alpha()

        self.images['ship-tileset'] = pygame.image.load("./assets/ship-tileset.png").convert_alpha()
        self.images['person_tileset'] = pygame.image.load("./assets/person_tileset.png").convert_alpha()
        self.images['person_tileset'] = pygame.transform.scale(self.images['person_tileset'], (1024, 32))

        # fonts
        self.font = pygame.font.SysFont("fangsong", c.FONT_SIZE)

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

    def change_ship_frame_state(self):
        """invoded every 1 second for ship animation"""
        self.ship_frame *= -1