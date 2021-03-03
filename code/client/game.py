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

# code relocated to these files
import draw
import gui
import handle_pygame_event
import handle_gui_event
import client_packet_received
from port_npc import Dog

from AOI_manager import PortMap, SeaMap

from gui import SelectionListWindow, ButtonClickHandler
from hashes.look_up_tables import id_2_building_type, now_direct_2_alternative_directs
from gui import mate_speak as m_speak
from image_processor import load_image, load_all_images
from sprites import Explosion


class Game():
    def __init__(self):
        # pygame and gui
        self._init_pygame()
        gui.init_gui(self)

        # loop to change ship frame state
        self._init_ship_frame_loop()

        # roles (net data)
        self.my_role = None
        self.other_roles = {}
        Role.GAME = self

        # local data
        self._init_local_data()

        # load assets
        self._init_maps()
        self._load_assets()

        # sprite group
        self.all_sprites = pygame.sprite.Group()
        self.mark_sprites = pygame.sprite.Group()

    def _init_pygame(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        pygame.display.set_caption(c.CAPTION)
        self.screen_surface = pygame.display.set_mode(
            [c.WINDOW_WIDTH, c.WINDOW_HIGHT])
        self.screen_surface_rect = self.screen_surface.get_rect()

    def _init_ship_frame_loop(self):
        self.ship_frame = 1
        looping_task = task.LoopingCall(self._change_ship_frame_state)
        looping_task.start(0.5)

    def _init_local_data(self):
        self.think_time_in_battle = c.THINK_TIME_IN_BATTLE
        self.time_of_day_index = 0
        self.days_spent_at_sea = 0
        self.time_of_day = 'day'
        self.building_text = ''
        self.login_state_text = 'Please login or register.'
        self.other_roles_rects = {}

    def _init_maps(self):
        # maps
        self.map_maker = MapMaker()
        self.map_maker.set_world_map_tiles()
        self.map_maker.set_world_piddle()

        # port_map and sea_map only for grid change detection
        self.port_map = PortMap()
        self.sea_map = SeaMap()

    def _load_assets(self):
        self.images = {}

        # load all imgs in these folders to self.images
        folder_names = ['buildings', 'huds', 'player', 'figures',
                        'discoveries_and_items', 'in_battle']
        for f_name in folder_names:
            load_all_images(self.images, f"../../assets/images/{f_name}")
        # ships
        self.images['ships'] = {}
        load_all_images(self.images['ships'], "../../assets/images/ships")
        # ship in battle
        self.images['ship_in_battle'] = {}
        load_all_images(self.images['ship_in_battle'],
                        "../../assets/images/ship_in_battle")
        # world map grids
        self.images['world_map_grids'] = pygame.image.load\
            ("../../assets/images/world_map/world_map_grids.png").convert_alpha()
        # fonts
        self.font = pygame.font.SysFont("Times New Roman", c.FONT_SIZE)

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

    def _change_ship_frame_state(self):
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
                    for alt_direction in now_direct_2_alternative_directs[my_role.direction]:
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
                            now_grid_id = self.sea_map.\
                                get_grid_id_by_x_and_y_tile_position(x_tile_pos, y_tile_pos)
                        elif my_role.is_in_port():
                            now_grid_id = self.port_map.\
                                get_grid_id_by_x_and_y_tile_position(x_tile_pos, y_tile_pos)

                        if now_grid_id != my_role.grid_id:
                            my_role.grid_id = now_grid_id
                            print(f"grid change to {now_grid_id}!!!!!!")
                            self.connection.send('grid_change',
                                                 [now_grid_id, my_role.direction])

                        my_role.speed_counter = 0

                        # update sea image
                        self._update_sea_image()

            # other roles
            for role in self.other_roles.values():
                if role.moving:
                    # can he move?
                    do_move = False
                    if role.can_move(role.direction):
                        do_move = True
                    else:
                        for alt_direction in now_direct_2_alternative_directs[role.direction]:
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

    def _update_my_role_position(self):
        pass

    def _update_other_roles_positions(self):
        pass

    def _update_sea_image(self):
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
                        self.images['sea'] = self.map_maker.\
                            make_partial_world_map(my_tile_x, my_tile_y, time_of_day)







