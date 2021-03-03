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

from AOI_manager import PortMap, SeaMap

from gui import SelectionListWindow, ButtonClickHandler
from hashes.look_up_tables import id_2_building_type
from gui import mate_speak as m_speak
from image_processor import load_image
from sprites import Explosion


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

        # local data
        self.think_time_in_battle = c.THINK_TIME_IN_BATTLE
        self.time_of_day_index = 0
        self.days_spent_at_sea = 0
        self.time_of_day = 'day'

        # load assets
        self.font = None
        self.images = {}
        self._load_assets()
        self.building_text = ''

        # NPCS
            # static
        self.dog = None
        self.old_man = None
        self.agent = None
            # dynamic
        self.man = None
        self.woman = None

        # port_map and sea_map only for grid change detection
        self.port_map = PortMap()
        self.sea_map = SeaMap()

        # sprite group
        self.all_sprites = pygame.sprite.Group()
        self.mark_sprites = pygame.sprite.Group()


    def _load_assets(self):
        # maps
                # port
            # self.port_piddle, self.images['port']  = self.map_maker.make_port_piddle_and_map(29)
                # partial_world_map
        self.map_maker.set_world_map_tiles()
        self.map_maker.set_world_piddle()
        # self.images['sea'] = self.map_maker.make_partial_world_map(900, 262)

                # battle
        self.images['battle'] = pygame.image.load("../../assets/battle.png").convert_alpha()

        # login backgound
        self.images['login_bg'] = pygame.image.load("../../assets/images/buildings/login_bg.png").convert_alpha()
        self.images['login_bg'] = pygame.transform.scale(self.images['login_bg'], (c.WINDOW_WIDTH, c.WINDOW_HIGHT))

        # buildings
        self.images['building_bg'] = pygame.image.load("../../assets/images/buildings/building_bg.png").convert_alpha()
        self.images['building_chat'] = pygame.image.load("../../assets/images/buildings/building_chat.png").convert_alpha()
        for building in id_2_building_type.values():
            try:
                self.images[building] = pygame.image.load(f"../../assets/images/buildings/{building}.png").convert_alpha()
            except:
                pass

        # huds
        self.images['hud_left'] = pygame.image.load("../../assets/images/huds/hud-left.png").convert_alpha()
        self.images['hud_left'] = pygame.transform.scale(self.images['hud_left'], (c.HUD_WIDTH, c.HUD_HIGHT))

        self.images['hud_right'] = pygame.image.load("../../assets/images/huds/hud-right.png").convert_alpha()
        self.images['hud_right'] = pygame.transform.scale(self.images['hud_right'], (c.HUD_WIDTH, c.HUD_HIGHT))

        # sprites
        self.images['ship-tileset'] = pygame.image.load("../../assets/ship-tileset.png").convert_alpha()
        self.images['person_tileset'] = pygame.image.load("../../assets/person_tileset.png").convert_alpha()
        self.images['person_tileset'] = pygame.transform.scale(self.images['person_tileset'], (1024, 32))

        self.images['explosion'] = load_image("../../assets/explosion.png")

        self.images['person_in_port'] = load_image("../../assets/person_in_port.png")
        self.images['ship_at_sea'] = load_image("../../assets/ship_at_sea.png")

        # cannon and engage_sign
        self.images['cannon'] = pygame.image.load("../../assets/cannon.png").convert_alpha()
        self.images['cannon'] = pygame.transform.scale(self.images['cannon'], (10, 10))

        self.images['engage_sign'] = pygame.image.load("../../assets/engage_sign.png").convert_alpha()
        self.images['engage_sign'] = pygame.transform.scale(self.images['engage_sign'], (26, 26))

        self.images['engage_sign_1'] = pygame.image.load("../../assets/engage_sign_1.png").convert_alpha()
        self.images['engage_sign_1'] = pygame.transform.scale(self.images['engage_sign_1'], (26, 26))

        # shoot mark
        self.images['shoot_mark'] = load_image("../../assets/shoot_mark.png")
        self.images['move_mark'] = load_image("../../assets/move_mark.png")
        self.images['no_move_mark'] = load_image("../../assets/no_move_mark.png")

        # ships
        file_names = os.listdir("../../assets/images/ships")
        self.images['ships'] = {}
        for file_name in file_names:
            parts = file_name.split('.')
            self.images['ships'][parts[0]] = pygame.image.load(f"../../assets/images/ships/{file_name}").convert_alpha()

        # figures
        self.images['figures'] = pygame.image.load("../../assets/images/figures/figures.png").convert_alpha()

        # discoveries_and_items
        self.images['discoveries_and_items'] = pygame.image.load("../../assets/images/discoveries_and_items/discoveries_and_items.png").convert_alpha()

        # world map grids
        self.images['world_map_grids'] = pygame.image.load("../../assets/images/world_map/world_map_grids.png").convert_alpha()

        # fonts
        self.font = pygame.font.SysFont("Times New Roman", c.FONT_SIZE)

        # ship in battle
        self.images['ship_in_battle'] = {}
        ship_in_battle = ['up', 'down', 'left', 'right', 'ne', 'sw', 'nw', 'se']
        for name in ship_in_battle:
            self.images['ship_in_battle'][name] = load_image(f"../../assets/images/ship_in_battle/{name}.png")



    def update(self):
        """called each frame"""
        self._process_input_events()
        draw.draw(self)

    def _process_input_events(self):
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
        print(protocol_name)
        print(params_list)

        # when logged in
        if self.my_role:
            func = getattr(self.my_role, protocol_name)
            func(params_list)
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

                        # grid change?
                        x_tile_pos, y_tile_pos = my_role.get_x_and_y_tile_position()

                        now_grid_id = None
                        if my_role.map == 'sea':
                            now_grid_id = self.sea_map.get_grid_id_by_x_and_y_tile_position(x_tile_pos, y_tile_pos)
                        elif my_role.is_in_port():
                            now_grid_id = self.port_map.get_grid_id_by_x_and_y_tile_position(x_tile_pos, y_tile_pos)

                        if now_grid_id != my_role.grid_id:
                            my_role.grid_id = now_grid_id
                            print(f"grid change to {now_grid_id}!!!!!!")
                            self.connection.send('grid_change', [now_grid_id, my_role.direction])

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
                if self.my_role.y <= c.WORLD_MAP_MAX_Y_TO_DRAW_NEW_PARTIAL_WORLD_MAP and \
                        self.my_role.y >= c.WORLD_MAP_MIN_Y_TO_DRAW_NEW_PARTIAL_WORLD_MAP:
                    if self.my_role.x >= c.WORLD_MAP_MIN_X_TO_DRAW_NEW_PARTIAL_WORLD_MAP and \
                            self.my_role.x <= c.WORLD_MAP_MAX_X_TO_DRAW_NEW_PARTIAL_WORLD_MAP:

                        # get time_of_day
                        if (self.time_of_day_index + 1) >= len(c.TIME_OF_DAY_OPTIONS):
                            self.time_of_day_index = 0
                        else:
                            self.time_of_day_index += 1
                        time_of_day = c.TIME_OF_DAY_OPTIONS[self.time_of_day_index]

                        # make sea image
                        self.images['sea'] = self.map_maker.make_partial_world_map(my_tile_x, my_tile_y, time_of_day)







