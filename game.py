import pygame
import pygame_gui
import sys
from twisted.internet import reactor
import constants as c
from role import Role, Ship, Mate

from gui import SelectionListWindow, ButtonClickHandler

EVENT_MOVE = pygame.USEREVENT + 1
EVENT_HEART_BEAT = pygame.USEREVENT + 2

def test():
    print('testing')


class Game():
    # init
    def __init__(self):
        # pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        pygame.display.set_caption(c.CAPTION)
        self.screen_surface = pygame.display.set_mode([c.WINDOW_WIDTH, c.WINDOW_HIGHT])

        # gui
        self.init_gui()

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

    def init_gui(self):
        # ui_manager and handlers
        self.ui_manager = pygame_gui.UIManager((c.WINDOW_WIDTH, c.WINDOW_HIGHT))
        self.button_click_handler = ButtonClickHandler(self)

        # text entry
        self.text_entry = pygame_gui.elements.UITextEntryLine(
            pygame.Rect((c.WINDOW_WIDTH / 2 - 260, c.WINDOW_HIGHT - 30), (140, -1)), self.ui_manager,
            object_id='#main_text_entry')

        # buttons
        self.buttons = {}
        self.init_button({'Ships': self.button_click_handler.on_button_click_ships}, 1)
        self.init_button({'Mates': self.button_click_handler.on_button_click_mates}, 2)
        self.init_button({'Items': self.button_click_handler.on_button_click_items}, 3)
        self.init_button({'Cmds': self.button_click_handler.on_button_click_cmds}, 4)
        self.init_button({'Options': self.button_click_handler.on_button_click_options}, 5)
        self.init_button({'Port': self.button_click_handler.on_button_click_port}, 6)
        self.init_button({'Battle': self.button_click_handler.on_button_click_battle}, 7)

        # menu stack
        self.menu_stack = []
        self.selection_list_stack = []

    # gui functions
    def init_button(self, dict, position):

        # get text and function from dict
        text_list = list(dict.keys())
        text = text_list[0]
        function = dict[text]

        # make button
        button = pygame_gui.elements.UIButton(pygame.Rect((c.WINDOW_WIDTH - c.BUTTON_WIDTH * position,
                                                           c.WINDOW_HIGHT - c.BUTTON_HIGHT),
                                                          (c.BUTTON_WIDTH, c.BUTTON_HIGHT)),
                                              text,
                                              self.ui_manager,
                                              object_id='#scaling_button')

        # add to buttons dict
        self.buttons[button] = function

    def on_button_click_ships(self):
        dict = {
            'Fleet Info': test,
            'Ship Info': test,
            'Rearrange': test,
        }
        self.make_menu(dict)

    def on_button_click_mates(self):
        dict = {
            'Admiral Info':test,
            'Mate Info':test,
        }
        self.make_menu(dict)

    def make_menu(self, dict):
        SelectionListWindow(pygame.Rect((c.WINDOW_WIDTH - 224, 50),
                                        (224, 250)),
                                         self.ui_manager,
                                         dict, self)

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

    # update
    def update(self):
        """called each frame"""
        self.process_input_events()
        self.draw()

    def process_input_events(self):

        # update ui
        time_delta = self.clock.tick(60) / 1000.0
        self.ui_manager.update(time_delta)

        # get events
        events = pygame.event.get()

        # iterate events
        for event in events:
            self.handle_pygame_event(event)
            self.handle_gui_event(event)

    def handle_pygame_event(self, event):
        # quit
        if event.type == pygame.QUIT:
            pygame.quit()
            reactor.stop()
            sys.exit()

        # key
        elif event.type == pygame.KEYDOWN:

            # escape
            if event.key == pygame.K_ESCAPE:

                # pop menu_stack
                if len(self.menu_stack) > 0:
                    menu_to_kill = self.menu_stack.pop()
                    self.selection_list_stack.pop()
                    menu_to_kill.kill()
                print(len(self.menu_stack))
                print('escape pressed!')

            # other keys
            elif event.key == ord('p'):
                print(self.my_role.name)
            elif event.key == ord('1'):
                self.connection.send('login', ['1', '1'])
            elif event.key == ord('2'):
                self.connection.send('login', ['2', '2'])
            elif event.key == ord('3'):
                self.connection.send('login', ['3', '3'])
            elif event.key == ord('4'):
                self.connection.send('login', ['4', '4'])
            elif event.key == ord('5'):
                self.connection.send('login', ['5', '5'])
            elif event.key == ord('w'):
                self.change_and_send('move', ['up'])
            elif event.key == ord('s'):
                self.change_and_send('move', ['down'])
            elif event.key == ord('a'):
                self.change_and_send('move', ['left'])
            elif event.key == ord('d'):
                self.change_and_send('move', ['right'])

            elif event.key == ord('n'):
                self.change_and_send('change_map', ['sea'])
            elif event.key == ord('m'):
                self.change_and_send('change_map', ['port'])

            elif event.key == ord('b'):
                self.change_and_send('try_to_fight_with', ['b'])
            elif event.key == ord('e'):
                self.change_and_send('exit_battle', [])
            elif event.key == ord('v'):
                self.change_and_send('try_to_fight_with', ['d'])

            elif event.key == ord('k'):
                self.change_and_send('shoot_ship', [0, 0])

        # user defined events
        elif event.type == EVENT_MOVE:
            # print("got move event")

            if self.my_role:
                if self.move_direction == 1:
                    self.change_and_send('move', ['right'])
                else:
                    self.change_and_send('move', ['left'])

                self.move_count += 1

                if self.move_count >= 15:
                    self.move_count = 0
                    self.move_direction *= -1

        elif event.type == EVENT_HEART_BEAT:
            self.change_and_send('heart_beat', [])

    def handle_gui_event(self, event):

        # pass event to gui manager
        self.ui_manager.process_events(event)

        # if event type is gui event
        if event.type == pygame.USEREVENT:

            # entry box entered
            if (event.user_type == pygame_gui.UI_TEXT_ENTRY_FINISHED and
                    event.ui_object_id == '#main_text_entry'):

                # unfocus
                if event.text:
                    print(event.text)

            # button press
            elif event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element in self.buttons:
                    self.buttons[event.ui_element]()

            # selection list
            elif event.user_type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
                if event.ui_element == self.selection_list_stack[-1]:
                    window = self.menu_stack[-1]
                    dict = window.dict
                    dict_value = dict[event.text]

                    if isinstance(dict_value, list):
                        function = dict[event.text][0]
                        function(dict_value[1])
                    else:
                        dict[event.text]()


    def draw(self):
        # fill
        self.screen_surface.fill(c.BLACK)

        # if logged in
        if self.my_role:

            # draw map
            now_map = self.my_role.map
            if now_map == 'port' or now_map == 'sea':
                self.screen_surface.blit(self.images[now_map], (0, 0))
            else:
                self.screen_surface.blit(self.images['battle'], (0, 0))

            # in port
            if now_map == 'port':
                # draw my role
                self.screen_surface.blit(self.images['person_in_port'], (self.my_role.x, self.my_role.y))

                # draw other roles
                for role in self.other_roles.values():
                    self.screen_surface.blit(self.images['person_in_port'], (role.x, role.y))

            # at sea
            elif now_map == 'sea':
                # draw my role
                self.screen_surface.blit(self.images['ship_at_sea'], (self.my_role.x, self.my_role.y))

                # draw other roles
                for role in self.other_roles.values():
                    self.screen_surface.blit(self.images['ship_at_sea'], (role.x, role.y))

            # in battle
            else:
                # my ships
                index = 0
                for ship in self.my_role.ships:
                    index += 30

                    # ship
                    self.screen_surface.blit(self.images['ship_at_sea'], (10, 10 + index))

                    # # state
                    # if ship.state == 'shooting':
                    #     self.screen_surface.blit(Ship.shooting_img, (60, 10 + index))
                    # elif ship.state == 'shot':
                    #     damage_img = g_font.render(ship.damage_got, True, COLOR_BLACK)
                    #     self.screen_surface.blit(damage_img, (60, 10 + index))

                    # hp
                    now_hp_img = self.font.render(str(ship.now_hp), True, c.BLACK)
                    self.screen_surface.blit(now_hp_img, (20 + 20, 10 + index))

                # enemy ships
                index = 0
                for ship in self.other_roles[self.my_role.enemy_name].ships:
                    index += 30

                    # ship
                    self.screen_surface.blit(self.images['ship_at_sea'], (c.WINDOW_WIDTH - 50, 10 + index))

                    # # state
                    # if ship.state == 'shooting':
                    #     g_screen.blit(Ship.shooting_img, (WIDTH - 100, 10 + index))
                    # elif ship.state == 'shot':
                    #     damage_img = g_font.render(ship.damage_got, True, COLOR_BLACK)
                    #     g_screen.blit(damage_img, (WIDTH - 100, 10 + index))

                    # hp
                    now_hp_img = self.font.render(str(ship.now_hp), True, c.BLACK)
                    self.screen_surface.blit(now_hp_img, (c.WINDOW_WIDTH - 70 - 10, 10 + index))

            # draw ui
            self.ui_manager.draw_ui(self.screen_surface)

        # not logged in
        else:
            text_surface = self.font.render('Please Login', True, c.WHITE)
            self.screen_surface.blit(text_surface, (5, 5))

        # flip
        pygame.display.flip()

    def get_connection(self, obj):
        """get protocol object to access network functions"""
        self.connection = obj

    def pck_received(self, pck_type, message_obj):

        if pck_type == 'your_role_data_and_others':
            # my role
            print("got my role data")
            my_role = message_obj[0]
            self.my_role = my_role
            print("my role's x y:", my_role.x, my_role.y, my_role.map, my_role.name)

            # other roles
            other_roles = message_obj[1]
            for role in other_roles:
                self.other_roles[role.name] = role
            print(other_roles)

        elif pck_type == 'new_role':
            new_role = message_obj
            self.other_roles[new_role.name] = new_role
            print("got new role named:", new_role.name)

        elif pck_type == 'logout':
            name_of_logged_out_role = message_obj
            del self.other_roles[name_of_logged_out_role]

        elif pck_type == 'roles_in_new_map':
            roles_in_new_map = message_obj
            self.my_role = roles_in_new_map[self.my_role.name]
            del roles_in_new_map[self.my_role.name]
            self.other_roles = roles_in_new_map

        elif pck_type == 'role_disappeared':
            name_of_role_that_disappeared = message_obj
            del self.other_roles[name_of_role_that_disappeared]

        elif pck_type == 'roles_disappeared':
            names_of_roles_that_disappeared = message_obj
            for name in names_of_roles_that_disappeared:
                del self.other_roles[name]

        elif pck_type == 'roles_in_battle_map':
            roles_in_battle_map = message_obj
            self.other_roles = {}
            for name, role in roles_in_battle_map.items():
                if name == self.my_role.name:
                    self.my_role = role
                else:
                    self.other_roles[name] = role

                # set game and in client to role

                role.in_client = True
                role.game = self

        elif pck_type == 'new_roles_from_battle':
            new_roles_from_battle = message_obj
            for name, role in new_roles_from_battle.items():
                self.other_roles[name] = role

        # sync packets
        elif pck_type in Role.__dict__:
            list = message_obj
            name = list.pop()
            func_name = pck_type
            role = self.other_roles[name]
            print("trying", func_name, list, "for", name)
            func = getattr(role, func_name)
            func(list)


    def change_and_send(self, protocol_name, params_list):
        self.connection.send(protocol_name, params_list)
        try:
            func = getattr(self.my_role, protocol_name)
            func(params_list)
        except:
            pass
