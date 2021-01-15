import pygame
import pygame_gui
import sys, os
from twisted.internet import reactor, task

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
        # handle_pygame_event.init_key_mappings(self)
        self.movement = None
        self.map_maker = MapMaker()
        self.login_state_text = 'Please login or register.'
        self.other_roles_rects = {}

        # loop to change ship frame state
        self.ship_frame = 1
        looping_task = task.LoopingCall(self.change_ship_frame_state)
        looping_task.start(0.5)

        # translator
        self.translator = Translator()

        # gui
        gui.init_gui(self)

        # connection
        self.connection = None

        # roles (data)
        self.my_role = None
        self.other_roles = {}
        self.all_roles = {}
        Role.GAME = self

        self.think_time_in_battle = c.THINK_TIME_IN_BATTLE

        # load assets
        self.font = None
        self.images = {}
        self.load_assets()
        self.building_text = ''

    def load_assets(self):
        # maps
                # port
            # self.port_piddle, self.images['port']  = self.map_maker.make_port_piddle_and_map(29)
                # partial_world_map
        self.map_maker.set_world_map_tiles()
        self.map_maker.set_world_piddle()
        # self.images['sea'] = self.map_maker.make_partial_world_map(900, 262)

                # battle
            # self.images['sea'] = pygame.image.load("./assets/sea.png").convert_alpha()
        self.images['battle'] = pygame.image.load("./assets/battle.png").convert_alpha()

        # login backgound
        self.images['login_bg'] = pygame.image.load("./assets/images/buildings/login_bg.png").convert_alpha()
        self.images['login_bg'] = pygame.transform.scale(self.images['login_bg'], (c.WINDOW_WIDTH, c.WINDOW_HIGHT))

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

        # cannon and engage_sign
        self.images['cannon'] = pygame.image.load("./assets/cannon.png").convert_alpha()
        self.images['cannon'] = pygame.transform.scale(self.images['cannon'], (10, 10))

        self.images['engage_sign'] = pygame.image.load("./assets/engage_sign.png").convert_alpha()
        self.images['engage_sign'] = pygame.transform.scale(self.images['engage_sign'], (16, 16))

        # ships
        file_names = os.listdir("./assets/images/ships")
        self.images['ships'] = {}
        for file_name in file_names:
            parts = file_name.split('.')
            self.images['ships'][parts[0]] = pygame.image.load(f"./assets/images/ships/{file_name}").convert_alpha()

        # figures
        self.images['figures'] = pygame.image.load("./assets/images/figures/figures.png").convert_alpha()

        # discoveries_and_items
        self.images['discoveries_and_items'] = pygame.image.load("./assets/images/discoveries_and_items/discoveries_and_items.png").convert_alpha()

        # world map grids
        self.images['world_map_grids'] = pygame.image.load("./assets/images/world_map/world_map_grids.png").convert_alpha()

        # fonts
        self.font = pygame.font.SysFont("Times New Roman", c.FONT_SIZE)

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

    def change_ship_frame_state(self):
        """invoded every 1 second for ship animation"""
        self.ship_frame *= -1

    def update_roles_positions(self):
        if self.my_role:
            # my role
            my_role = self.my_role
            if my_role.moving:
                # can i move
                do_move = False
                if my_role.can_move(my_role.direction):
                    do_move = True
                else:
                    for alt_direction in c.ALTERNATIVE_DIRECTIONS[my_role.direction]:
                        if my_role.can_move(alt_direction):
                            my_role.direction = alt_direction
                            do_move = True
                            continue

                # do move
                if do_move:
                    my_role.speed_counter += 1
                    if my_role.speed_counter == my_role.speed_counter_max:
                        my_role.move([my_role.direction])
                        my_role.speed_counter = 0

                        # update sea image
                        self.update_sea_image()

            # other roles
            for role in self.other_roles.values():
                if role.moving:
                    # can he move?
                    do_move = False
                    if role.can_move(role.direction):
                        do_move = True
                    else:
                        for alt_direction in c.ALTERNATIVE_DIRECTIONS[role.direction]:
                            if role.can_move(alt_direction):
                                role.direction = alt_direction
                                do_move = True
                                continue
                    # do move
                    if do_move:
                        role.speed_counter +=1
                        if role.speed_counter == role.speed_counter_max:
                            role.move([role.direction])
                            role.speed_counter = 0

    def update_sea_image(self):
        if self.my_role.map == 'sea':
            my_tile_x = int(self.my_role.x / c.PIXELS_COVERED_EACH_MOVE)
            my_tile_y = int(self.my_role.y / c.PIXELS_COVERED_EACH_MOVE)

            if abs(my_tile_x - self.map_maker.x_tile) >= 12 or abs(my_tile_y - self.map_maker.y_tile) >= 12:
                print("out of box! time to draw new map")
                self.images['sea'] = self.map_maker.make_partial_world_map(my_tile_x, my_tile_y)