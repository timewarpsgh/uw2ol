import pygame_gui
from pygame_gui._constants import UI_WINDOW_CLOSE, UI_WINDOW_MOVED_TO_FRONT, UI_BUTTON_PRESSED
import pygame
from twisted.internet import reactor, task
import random

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
import constants as c
from role import Port, Mate, Ship, Discovery, Item
from hashes import hash_villages

import handle_pygame_event

from hashes.hash_ports_meta_data import hash_ports_meta_data
from hashes.look_up_tables import id_2_building_type
from hashes.hash_items import hash_items

def test():
    print('testing')

def init_gui(self):
    """argument self is game"""
    # ui_manager and handlers
    self.ui_manager = pygame_gui.UIManager((c.WINDOW_WIDTH, c.WINDOW_HIGHT))
    self.button_click_handler = ButtonClickHandler(self)

    # text entry
    self.text_entry = pygame_gui.elements.UITextEntryLine(
        pygame.Rect((2, c.WINDOW_HIGHT - 30), (140, -1)), self.ui_manager,
        object_id='#main_text_entry')

    self.text_entry_active = False
    self.active_input_boxes = []

    # buttons
    self.buttons = {}
    init_button(self, {'Ships': self.button_click_handler.on_button_click_ships}, 1)
    init_button(self, {'Mates': self.button_click_handler.on_button_click_mates}, 2)
    init_button(self, {'Items': self.button_click_handler.on_button_click_items}, 3)
    init_button(self, {'Cmds': self.button_click_handler.cmds}, 4)
    init_button(self, {'Options': self.button_click_handler.options}, 5)
    init_button(self, {'Port': self.button_click_handler.port}, 6)
    init_button(self, {'Battle': self.button_click_handler.battle}, 7)
    init_button(self, {'Login': self.button_click_handler.login}, 8)

    self.buttons_in_windows = {}

    # menu stack
    self.menu_stack = []
    self.selection_list_stack = []

def init_button(self, dict, position):
    """argument self is game"""
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

class MessageWindow(pygame_gui.elements.UIWindow):
    def __init__(self, rect, ui_manager, text, game):
        # super
        super().__init__(rect, ui_manager,
                         window_display_title='',
                         object_id='#scaling_window',
                         resizable=True)

        self.game = game

        # text box
        pygame_gui.elements.UITextBox(html_text=text,
                                     relative_rect=pygame.Rect(0, 0, 300, 350),
                                     manager=ui_manager,
                                     wrap_to_height=True,
                                     container=self)

        # push into stacks
        game.menu_stack.append(self)
        game.selection_list_stack.append(self)

class InputBoxWindow(pygame_gui.elements.UIWindow):
    """a window with input boxes and an OK button"""
    def __init__(self, rect, ui_manager, protocol_name, params_names_list, values_list, game):

        # super
        super().__init__(rect, ui_manager,
                         window_display_title='',
                         object_id='#scaling_window',
                         resizable=True)

        # get game
        self.game = game

        # clear active_input_boxes
        self.game.active_input_boxes.clear()

        # for each param
        input_box_list = []
        line_distance = 40
        for i, name in enumerate(params_names_list):

            # text box
            pygame_gui.elements.UITextBox(html_text=name,
                                          relative_rect=pygame.Rect(0, 0 + line_distance*i, 120, 40),
                                          manager=ui_manager,
                                          wrap_to_height=True,
                                          container=self)

            # input box
            input_box = pygame_gui.elements.UITextEntryLine(
                pygame.Rect((150, 0 + line_distance*i), (80, 40)), ui_manager,
                object_id=str(i),
                container=self)

            input_box_list.append(input_box)


            # append to active_input_boxes
            self.game.active_input_boxes.append(input_box)

        # for each value (given)
        if values_list:
            index = 0
            for value in values_list:
                input_box_list[index].set_text(value)
                index +=1

        # get dict
        self.dict = {'OK':[protocol_name]}

        # ok button
        self.game.button_click_handler.make_button_in_window(self.dict, pygame.Rect((50, line_distance * len(params_names_list)), (50, 20)), self)

        # set text entry to active
        self.game.text_entry_active = True

        # push into stacks
        self.game.menu_stack.append(self)
        self.game.selection_list_stack.append(self)

class PanelWindow(pygame_gui.elements.UIWindow):
    """displays info"""
    def __init__(self, rect, ui_manager, text, game, image='none'):

        if image == 'none':
            image = game.images['ship_at_sea']


        # super
        super().__init__(rect, ui_manager,
                         window_display_title='',
                         object_id='#scaling_window',
                         resizable=True)

        self.game = game

        # image
        pygame_gui.elements.UIImage(pygame.Rect((0, 0), (image.get_rect().size
                                                         )),
                                    image, ui_manager,
                                  container=self,
                                  anchors={'top': 'top', 'bottom': 'bottom',
                                           'left': 'left', 'right': 'right'})

        # text box
        if text:
            pygame_gui.elements.UITextBox(html_text=text,
                                                     relative_rect=pygame.Rect(0, image.get_rect().height, 320, 10),
                                                     manager=ui_manager,
                                                     wrap_to_height=True,
                                                     container=self)

        # push into stacks
        game.menu_stack.append(self)
        game.selection_list_stack.append(self)

class SelectionListWindow(pygame_gui.elements.UIWindow):
    """provides a list for selection"""
    def __init__(self, rect, ui_manager, dict, game):

        # super
        super().__init__(rect, ui_manager,
                         window_display_title='',
                         object_id='#scaling_window',
                         resizable=True)

        self.game = game

        # gets
        self.dict = dict
        item_list = dict.keys()

        # list box
        self.selection_list = pygame_gui.elements.UISelectionList(pygame.Rect(10, 10, 174, 170),
                                            item_list=item_list,
                                            manager=ui_manager,
                                            container=self,
                                            allow_multi_select=False)

        # push into stacks
        game.menu_stack.append(self)
        game.selection_list_stack.append(self.selection_list)

class ButtonClickHandler():
    def __init__(self, game):
        self.game = game
        self.ui_manager = game.ui_manager
        self.menu_click_handler = MenuClickHandler(game)

    def make_menu(self, dict):
        SelectionListWindow(pygame.Rect((c.SELECTION_LIST_X, c.SELECTION_LIST_Y),
                                        (c.SELECTION_LIST_WIDTH, c.SELECTION_LIST_HIGHT)),
                            self.ui_manager,
                            dict, self.game)

    def make_input_boxes(self, prtocol_name, params_list, values_list=[]):
        InputBoxWindow(pygame.Rect((59, 50), (350, 400)),
                       self.ui_manager, prtocol_name, params_list, values_list, self.game)

        # g_player.text_entry_active = True

    def make_button_in_window(self, dict, rect, window):
        # get text and function from dict
        text_list = list(dict.keys())
        text = text_list[0]
        function = dict[text]

        # make button
        button_in_window = pygame_gui.elements.UIButton(rect,
                                                        text,
                                                        self.ui_manager,
                                                        object_id='#scaling_button',
                                                        container=window)

        # add to buttons_in_windows dict
        self.game.buttons_in_windows[button_in_window] = function

        print(len(self.game.buttons.keys()))

    def make_message_box(self, text):
        MessageWindow(pygame.Rect((200, 50),
                                  (350, 350)),
                      self.ui_manager,
                      text, self.game)

    def on_button_click_ships(self):
        dict = {
            'Fleet Info': self.menu_click_handler.ships.fleet_info,
            'Ship Info': self.menu_click_handler.ships.ship_info,
            'Swap Ships': self.menu_click_handler.ships.swap_ships,
        }
        self.make_menu(dict)

    def on_button_click_mates(self):
        dict = {
            'Admiral Info':self.menu_click_handler.mates.admiral_info,
            'Mate Info':self.menu_click_handler.mates.mate_info,
        }
        self.make_menu(dict)

    def on_button_click_items(self):
        dict = {
            'Items': self.menu_click_handler.items.on_menu_click_items,
            'Discoveries': self.menu_click_handler.items.on_menu_click_discoveries,
            'Diary': self.menu_click_handler.items.diary,
            'World Map': self.menu_click_handler.items.world_map,
            'Port Map': self.menu_click_handler.items.port_map
        }
        self.make_menu(dict)

    def cmds(self):
        dict = {
            'Enter Building (Z)': test,
            'Enter Port (M)': self.menu_click_handler.cmds.enter_port,
            'Go Ashore': self.menu_click_handler.cmds.go_ashore,
            'Battle (B)': test,
        }
        self.make_menu(dict)

    def options(self):
        dict = {
            'Language': test,
            'Sounds': test,
            'Hot Keys': test,
            'Exit': test,
        }
        self.make_menu(dict)

    def port(self):
        if self.game.my_role.map.isdigit() and c.DEVELOPER_MODE_ON:
            dict = {
                'Market': self.menu_click_handler.port.on_menu_click_market,
                'Bar': self.menu_click_handler.port.on_menu_click_bar,
                'Dry Dock': self.menu_click_handler.port.on_menu_click_dry_dock,
                'Harbor': self.menu_click_handler.port.on_menu_click_port,
                'Inn': self.menu_click_handler.port.on_menu_click_inn,
                'Palace': self.menu_click_handler.port.on_menu_click_palace,
                'Job House': self.menu_click_handler.port.on_menu_click_job_house,
                'Misc': test,
                'Bank': self.menu_click_handler.port.on_menu_click_bank,
                'Item Shop': self.menu_click_handler.port.on_menu_click_item_shop,
                'Church': self.menu_click_handler.port.on_menu_click_church,
                'Fortune House': self.menu_click_handler.port.on_menu_click_fortune_house,
            }
            self.make_menu(dict)
        else:
            print('only available in port!')
            # make_message_box('only available in port!')

    def battle(self):

        if 'battle' in self.game.my_role.map:
            dict = {
                'View Enemy Ships': self.menu_click_handler.battle.enemy_ships,
                'All Ships Move': self.menu_click_handler.battle.all_ships_move,
                'Set All Ships Target': self.menu_click_handler.battle.set_target,
                'Set All Ships Strategy': self.menu_click_handler.battle.set_attack_method,
                'Set One Ships Strategy': self.menu_click_handler.battle.set_one_ships_strategy,
            }
            self.make_menu(dict)
        else:
            # make_message_box('only available in battle!')
            print('only available in battle!')

    def login(self):

        # when not logged in
        if  not self.game.my_role:

            dict = {
                'Login': self.menu_click_handler.login.login,
                'Register': self.menu_click_handler.login.register,
                'Make Character': self.menu_click_handler.login.make_character,
            }
            self.make_menu(dict)

        # when logged in
        else:
            print('only available when not logged in!')

class MenuClickHandler():
    def __init__(self, game):
        # need game info
        self.game = game
        self.ui_manager = game.ui_manager

        # sub handlers
        self.ships = MenuClickHandlerForShips(game)
        self.mates = MenuClickHandlerForMates(game)
        self.items = MenuClickHandlerForItems(game)
        self.cmds = MenuClickHandlerForCmds(game)
        self.options = MenuClickHandlerForOptions(game)
        self.port = MenuClickHandlerForPort(game)  # has a few buildings
        self.battle = MenuClickHandlerForBattle(game)
        self.login = MenuClickHandlerForLogin(game)

class MenuClickHandlerForShips():
    def __init__(self, game):
        self.game = game

    def fleet_info(self, target=False):
        # get ships and nation
        ships = None
        nation = None
        if target:
            # enemy
            role = self.game.my_role
            enemy_name = role.enemy_name
            enemy_role = role._get_other_role_by_name(enemy_name)
            ships = enemy_role.ships

            nation = enemy_role.mates[0].nation
            # my
        else:
            ships = self.game.my_role.ships
            nation = self.game.my_role.mates[0].nation

        # make panel window
        types = [ship.type for ship in ships]
        text = ''
        for type in types:
            text += f'{type}<br>'

        text += f'<br>Fleet Speed: {self.game.my_role.get_fleet_speed([])} knots'
        text += f'<br>Flag: {nation}'


        PanelWindow(pygame.Rect((59, 50), (350, 400)),
                    self.game.ui_manager, text, self.game)

    def ship_info(self, target=False):
        # get ships
        ships = None
        if target:
            # enemy
            role = self.game.my_role
            enemy_name = role.enemy_name
            enemy_role = role._get_other_role_by_name(enemy_name)
            ships = enemy_role.ships
            # my
        else:
            ships = self.game.my_role.ships

        # new menu
        dict = {}
        index = 0
        for ship in ships:
            dict[str(index)] = [self.show_one_ship, [ship, target, index]]
            index += 1
        self.game.button_click_handler.make_menu(dict)

    def show_one_ship(self, params):
        # get param
        ship = params[0]
        target = params[1]
        ship_id = params[2]

        # dict
        captain_name = 'None'
        if ship.captain:
            captain_name = ship.captain.name

        speed = 1
        if ship_id == 0:
            speed = ship.get_speed(self.game.my_role)
        else:
            speed = ship.get_speed()

        dict = {
            'name': f'{ship.name}   type:{ship.type}',
            'captain': f'{captain_name}',
            'durability': f'{ship.now_hp}/{ship.max_hp}',
            'tacking': f'{ship.tacking}    power:{ship.power}',
            'speed': f'{speed} knots',
            'capacity': f'{ship.capacity}',
            'max_guns': f'{ship.max_guns}',
            'min_crew/max_crew': f'{ship.min_crew}/{ship.max_crew}',
            'useful_capacity': f'{ship.useful_capacity}',
            'crew': f'{ship.crew}',
        }

        # if no target selected
        if not target:
            # supply
            dict['supplies'] = f"  F:{ship.supplies['Food']} W:{ship.supplies['Water']}" \
                               f" L:{ship.supplies['Lumber']} S:{ship.supplies['Shot']}"

            # cargo
            cargoes_dict = ship.cargoes
            for cargo_name, count in cargoes_dict.items():
                dict[cargo_name] = count

        # make text from dict
        text = ''
        for k, v in dict.items():
            text += f'{k}:{v}<br>'

        # make window
        ship_image = self.game.images['ships'][ship.type.lower()]
        PanelWindow(pygame.Rect((59, 10), (350, 400)),
                    self.game.ui_manager, text, self.game, ship_image)

    def swap_ships(self):
        self.game.button_click_handler.make_input_boxes('swap_ships', ['from ship num', 'to ship num'])

class MenuClickHandlerForMates():
    def __init__(self, game):
        self.game = game

    def admiral_info(self):

        role = self.game.my_role
        accountant_text = role.accountant.name if role.accountant else 'None'
        first_mate_text = role.first_mate.name if role.first_mate else 'None'
        chief_navigator_text = role.chief_navigator.name if role.chief_navigator else 'None'

        dict = {
            'name': self.game.my_role.name,
            ' ': "",
            'accountant': accountant_text,
            'first mate': first_mate_text,
            'chief navigator': chief_navigator_text,

        }

        # make text from dict
        text = ''
        for k, v in dict.items():
            if v:
                text += f'{k}:{v}<br>'
            else:
                text += '<br>'

        # get figure image
        figure_surface = figure_x_y_2_image(self.game, role.mates[0].image_x, role.mates[0].image_y)

        # make window
        PanelWindow(pygame.Rect((59, 50), (350, 400)),
                    self.game.ui_manager, text, self.game, figure_surface)

    def mate_info(self):
        dict = {}
        index = 0
        for mate in self.game.my_role.mates:
            dict[mate.name] = [self.show_one_mate, [mate, index]]
            index += 1
        self.game.button_click_handler.make_menu(dict)

    def show_one_mate(self, params):
        # get param
        mate = params[0]
        mate_num = params[1]

        # dict
        duty_name = 'None'
        if mate.duty:
            if mate.duty in ['accountant', 'first_mate', 'chief_navigator']:
                duty_name = mate.duty
            else:
                duty_name = 'captain of ' + mate.duty.name

        dict = {
            'name': mate.name,
            'nation': mate.nation,
            'duty': duty_name,
            'lv': f"{mate.lv} exp:{mate.exp} points:{mate.points}",
            'leadership': mate.leadership,
            'seamanship': f"{mate.seamanship} luck:{mate.luck}",
            'knowledge': f"{mate.knowledge} intuition:{mate.intuition}",
            'courage': f"{mate.courage} swordplay:{mate.swordplay}",
            'accounting': mate.accounting,
            'gunnery': mate.gunnery,
            'navigation': mate.navigation,
        }

        # make text from dict
        text = ''
        for k, v in dict.items():
            text += f'{k}:{v}<br>'

        # get figure image
        figure_surface = figure_x_y_2_image(self.game ,mate.image_x, mate.image_y)

        # make window
        PanelWindow(pygame.Rect((59, 50), (350, 400)),
                    self.game.ui_manager, text, self.game, figure_surface)

        # make actions menu
        dict1 = {
            'Set as Captain of': [self.set_as_captain_of, mate_num],
            'Set as hand': [self.set_as_hand, mate_num],
            'Relieve Duty': [self.relieve_duty, mate_num],
            'Level Up': [self.level_up, mate_num],
            'Add Attribute': [self.add_attribute, mate_num]
        }

        # admiral special functions
        if mate_num == 0:
            dict1['Distribute Exp'] = [self.assign_exp, mate_num]

        self.game.button_click_handler.make_menu(dict1)

    def set_as_hand(self, mate_num):

        def accountant(mate_num):
            self.game.button_click_handler. \
                make_input_boxes('set_mate_as_hand', ['mate num', 'position'], [str(mate_num), 'accountant'])

        def first_mate(mate_num):
            self.game.button_click_handler. \
                make_input_boxes('set_mate_as_hand', ['mate num', 'position'], [str(mate_num), 'first_mate'])

        def chief_navigator(mate_num):
            self.game.button_click_handler. \
                make_input_boxes('set_mate_as_hand', ['mate num', 'position'], [str(mate_num), 'chief_navigator'])

        dict1 = {
            'Accountant': [accountant, mate_num],
            'First Mate': [first_mate, mate_num],
            'Chief Navigator': [chief_navigator, mate_num],
        }

        self.game.button_click_handler.make_menu(dict1)

    def assign_exp(self, mate_num):
        self.game.button_click_handler. \
            make_input_boxes('give_exp_to_other_mates', ['mate num', 'amount'])

    def level_up(self, mate_num):
        self.game.button_click_handler. \
            make_input_boxes('add_mates_lv', ['mate num'], [str(mate_num)])

    def add_attribute(self, mate_num):

        def do_add_attribute(params):
            mate_num = params[0]
            attribute_name = params[1]
            self.game.button_click_handler. \
                make_input_boxes('add_mates_attribute', ['mate num', 'attribute'], [str(mate_num), attribute_name])

        dict1 = {
            'Leadership': [do_add_attribute, [mate_num, 'leadership']],
            'Seamanship': [do_add_attribute, [mate_num, 'seamanship']],
            'Luck': [do_add_attribute, [mate_num, 'luck']],
            'Knowledge': [do_add_attribute, [mate_num, 'knowledge']],
            'Intuition': [do_add_attribute, [mate_num, 'intuition']],
            'Courage': [do_add_attribute, [mate_num, 'courage']],
            'Swordplay': [do_add_attribute, [mate_num, 'swordplay']],
        }

        self.game.button_click_handler.make_menu(dict1)

    def set_as_captain_of(self, mate_num):
        self.game.button_click_handler. \
            make_input_boxes('set_mates_duty', ['mate num', 'ship num'], [str(mate_num)])

    def relieve_duty(self, mate_num):
        self.game.button_click_handler. \
            make_input_boxes('relieve_mates_duty', ['mate num'], [str(mate_num)])

class MenuClickHandlerForItems():
    def __init__(self, game):
        self.game = game

    def on_menu_click_items(self):
        items_dict = self.game.my_role.bag.container

        dict = {}
        for k in items_dict.keys():
            item = Item(k)
            dict[f'{item.name} {items_dict[k]}'] = [show_one_item, [self, item]]

        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_discoveries(self):

        def show_one_discovery(discovery):
            # dict
            dict = {
                'name': discovery.name,
                'description': discovery.description,
            }

            # make text from dict
            text = ''
            for k, v in dict.items():
                text += f'{v}<br>'

            # get figure image
            figure_surface = item_x_y_2_image(self.game, discovery.image_x, discovery.image_y)

            # make window
            PanelWindow(pygame.Rect((59, 50), (350, 400)),
                        self.game.ui_manager, text, self.game, figure_surface)

        # do
        my_discoveries = self.game.my_role.discoveries
        dict = {}
        for id in my_discoveries:
            discovery = Discovery(id)
            dict[discovery.name] = [show_one_discovery, discovery]
        self.game.button_click_handler.make_menu(dict)

    def diary(self):
        dict = {
            'Discovery': self.discovery,
            'Trade': test,
            'Fight': test,
            'Abandon Quest': self.abandon_quest,
        }
        self.game.button_click_handler.make_menu(dict)

    def discovery(self):
        discovery_quest_id = self.game.my_role.quest_discovery
        if discovery_quest_id:
            discovery = Discovery(discovery_quest_id)
            self.game.button_click_handler.make_message_box(f""
                 f"On quest to investigate {discovery.longitude} {discovery.latitude}")
        else:
            self.game.button_click_handler.make_message_box("No quest.")

    def abandon_quest(self):
        dict = {
            'Abandon Discovery Quest': self.abandon_discovery_quest,
            'Abandon Trade Quest': test,
            'Abandon Fight Quest': test,
        }
        self.game.button_click_handler.make_menu(dict)

    def abandon_discovery_quest(self):
        self.game.change_and_send('give_up_discovery_quest', [])
        self.game.button_click_handler.make_message_box("Quest abandoned.")

    def world_map(self):
        world_map_grids_image = self.game.images['world_map_grids']
        image_rect = world_map_grids_image.get_rect()
        text = ''

        PanelWindow(pygame.Rect((10, 10), (image_rect.width, (image_rect.height + 60))),
                    self.game.ui_manager, text, self.game, world_map_grids_image)

    def port_map(self):
        if self.game.images['port']:
            port_map = pygame.transform.scale(self.game.images['port'], (c.PORT_MAP_SIZE, c.PORT_MAP_SIZE))
            text = ''

            PanelWindow(pygame.Rect((10, 10), ((c.PORT_MAP_SIZE + 30), (c.PORT_MAP_SIZE + 60))),
                    self.game.ui_manager, text, self.game, port_map)

class MenuClickHandlerForCmds():
    def __init__(self, game):
        self.game = game

    # def set_target(self):
    #     self.game.button_click_handler. \
    #         make_input_boxes('set_target', ['target name'])

    def enter_building(self):
        # get my now position in piddle
        x = int(self.game.my_role.x/c.PIXELS_COVERED_EACH_MOVE)
        y = int(self.game.my_role.y/c.PIXELS_COVERED_EACH_MOVE)

        # get building id to board positions dict
        map_id = int(self.game.my_role.map)

        if map_id >= 100:
            map_id = 100

        dict = hash_ports_meta_data[map_id+1]['buildings']

        for k, v in dict.items():
            if v['x'] == x and v['y'] == y:
                print("entered", k)
                dict = {
                    1:self.game.button_click_handler.menu_click_handler.port.on_menu_click_market,
                    2:self.game.button_click_handler.menu_click_handler.port.on_menu_click_bar,
                    3:self.game.button_click_handler.menu_click_handler.port.on_menu_click_dry_dock,
                    4:self.game.button_click_handler.menu_click_handler.port.on_menu_click_port,
                    5:self.game.button_click_handler.menu_click_handler.port.on_menu_click_inn,
                    6: self.game.button_click_handler.menu_click_handler.port.on_menu_click_palace,
                    7:self.game.button_click_handler.menu_click_handler.port.on_menu_click_job_house,
                    8:test,
                    9:self.game.button_click_handler.menu_click_handler.port.on_menu_click_bank,
                    10:self.game.button_click_handler.menu_click_handler.port.on_menu_click_item_shop,
                    11:self.game.button_click_handler.menu_click_handler.port.on_menu_click_church,
                    12:self.game.button_click_handler.menu_click_handler.port.on_menu_click_fortune_house,
                }
                dict[k]()

                # set building type
                self.game.my_role.in_building_type = k

                # set building image
                self.game.building_image = self.game.images[id_2_building_type[k]]

                # welcome text
                self.game.building_text = 'Welcome! What can I do for you?'

                # trigger event?
                role = self.game.my_role
                pending_event = role.get_pending_event()
                if pending_event:
                    port = Port(map_id)
                    building = id_2_building_type[k]

                    if port.name == pending_event.port:
                        if building == pending_event.building or pending_event.building == 'any':
                            print(pending_event.dialogues)
                            self.present_event(pending_event)
                            self.game.change_and_send('trigger_quest', [])

                return

        print('no building to enter')

    def present_event(self, event):
        dialogues = event.dialogues
        figure_images = event.figure_images

        # show dialogues
        for dialogue in reversed(dialogues):
            speaker = dialogue[0]
            message = dialogue[1]

            image_x = figure_images[speaker][0]
            image_y = figure_images[speaker][1]
            figure_image_speak(self.game, image_x, image_y, message)

        # perform action if any
        if event.action_to_perform:
            protocol = event.action_to_perform[0]
            params = event.action_to_perform[1]
            self.game.change_and_send(protocol, params)

    def enter_port(self):
        self.game.change_and_send('change_map', ['port'])

    def go_ashore(self):

        def get_nearby_village_index():
            # get x and y in tile position
            x_tile = self.game.my_role.x / c.PIXELS_COVERED_EACH_MOVE
            y_tile = self.game.my_role.y / c.PIXELS_COVERED_EACH_MOVE

            # iterate each port
            for i in range(1, 99):
                if abs(x_tile - hash_villages.villages_dict[i]['x']) <= 2 \
                        and abs(y_tile - hash_villages.villages_dict[i]['y']) <= 2:
                    village_id = i
                    return village_id

            return None

        # main
        village_id = get_nearby_village_index()
        if village_id:
            self.game.change_and_send('discover', [village_id])
        else:
            discovery_id = random.randint(0, 90)
            self.game.change_and_send('discover', [discovery_id])
            # self.game.button_click_handler.make_message_box("Can't find anything.")



    def battle(self):
        target_name = self.game.my_role.enemy_name
        if target_name:
            self.game.change_and_send('try_to_fight_with', [target_name])
        else:
            self.game.button_click_handler. \
                make_message_box("you don't have a target")

class MenuClickHandlerForOptions():
    def __init__(self, game):
        self.game = game

class MenuClickHandlerForLogin():
    def __init__(self, game):
        self.game = game

    def login(self):
        self.game.button_click_handler. \
            make_input_boxes('login', ['account', 'password'])
        print('trying to login')

    def register(self):
        self.game.button_click_handler. \
            make_input_boxes('register', ['account', 'password'])
        print('trying to register')

    def make_character(self):
        self.game.button_click_handler. \
            make_input_boxes('create_new_role', ['role_name'])
        print('trying to make character')

class MenuClickHandlerForBattle():
    def __init__(self, game):
        self.game = game

    def all_ships_move(self):
        self.game.change_and_send('all_ships_operate', [])
        self.game.think_time_in_battle = c.THINK_TIME_IN_BATTLE

    def enemy_ships(self):
        # get enemy ships
        enemy_ships = self.game.other_roles[self.game.my_role.enemy_name].ships

        # new menu
        dict = {}
        index = 0
        for ship in enemy_ships:
            dict[ship.name] = [self.game.button_click_handler.menu_click_handler.\
                ships.show_one_ship, [ship, True, index]]
            index += 1
        self.game.button_click_handler.make_menu(dict)

    def set_target(self):
        self.game.button_click_handler. \
            make_input_boxes('set_all_ships_target', ['target_id'])

    def set_attack_method(self):
        self.game.button_click_handler. \
            make_input_boxes('set_all_ships_attack_method', ['attack_method_id'])

    def set_one_ships_strategy(self):
        self.game.button_click_handler. \
            make_input_boxes('set_one_ships_strategy', ['ship_id', 'target_id', 'attack_method'])

class MenuClickHandlerForPort():
    """contains handlers for all buildings in port"""
    def __init__(self, game):
        self.game = game

        self.port = Harbor(game)
        self.market = Market(game)
        self.bar = Bar(game)
        self.dry_dock = DryDock(game)
        self.job_house = JobHouse(game)
        self.church = Church(game)
        self.palace = Palace(game)
        self.bank = Bank(game)
        self.item_shop = ItemShop(game)

    def on_menu_click_port(self):
        dict = {
            'Sail': self.port.sail,
            'Load Supply': self.port.load_supply,
            'Unload Supply': self.port.unload_supply,
            'Dry Dock': self.port.dry_dock,
        }
        self.game.button_click_handler.make_menu(dict)

        self.game.building_text = 'Ready to sail?'

    def on_menu_click_market(self):
        dict = {
            'Buy': self.market.buy,
            'Sell': self.market.sell,
            'Invest': test,
            'Price Index': test,
        }
        self.game.button_click_handler.make_menu(dict)

        self.game.building_text = "You are a merchant, aren't you?"

    def on_menu_click_bar(self):
        dict = {
            'Recruit Crew': self.bar.recruit_crew,
            'Dismiss Crew': self.bar.dismiss_crew,
            'Treat': self.bar.treat,
            'Meet': self.bar.meet,
            'Fire Mate': self.bar.fire_mate,
            'Waitress': test,
            'Gamble': test,
        }
        self.game.button_click_handler.make_menu(dict)


    def on_menu_click_dry_dock(self):
        dict = {
            'New Ship': self.dry_dock.new_ship,
            'Used Ship': self.dry_dock.used_ship,
            'Repair': self.dry_dock.repair,
            'Sell': self.dry_dock.sell_ship,
            'Remodel': self.dry_dock.remodel,
            'Invest': self.dry_dock.invest,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_inn(self):
        dict = {
            'Check In': test,
            'Gossip': test,
            'Port Info': test,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_palace(self):
        dict = {
            'Meet Ruler': self.palace.meet_ruler,
            'Defect': self.palace.defect,
            'Gold Aid': self.palace.gold_aid,
            'Ship Aid': self.palace.ship_aid,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_job_house(self):
        dict = {
            'Job Assignment': self.job_house.job_assignment,
            'Country Info': self.job_house.contry_info,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_bank(self):
        dict = {
            'Check Balance': self.bank.check_balance,
            'Deposit': self.bank.deposit,
            'Withdraw': self.bank.withdraw,
            'Borrow': self.bank.borrow,
            'Repay': self.bank.repay,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_item_shop(self):
        dict = {
            'Buy': self.item_shop.buy,
            'Sell': self.item_shop.sell,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_church(self):
        dict = {
            'Pray': self.church.pray,
            'Donate': self.church.donate,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_fortune_house(self):
        dict = {
            'Life': test,
            'Career': test,
            'Love': test,
            'Mates': test,
        }
        self.game.button_click_handler.make_menu(dict)


class Harbor():
    """menu options under building port"""
    def __init__(self, game):
        self.game = game

    def sail(self):
        # show dialogue
        max_days = self.game.my_role.calculate_max_days_at_sea()
        fleet_speed = self.game.my_role.get_fleet_speed([])

        self.game.building_text = f"You can sail for {max_days} days " \
                                  f"at an average speed of {fleet_speed} knots. " \
                                  f"Are you sure you wnat to set sail?"

        # make menu
        dict = {
            'OK':self.sail_ok,
        }
        self.game.button_click_handler.make_menu(dict)

    def sail_ok(self):

        # def
        def pass_one_day_at_sea(self):
            if self.my_role.map == 'sea':

                # pass peacefully
                if self.days_spent_at_sea <= self.max_days_at_sea:
                    self.days_spent_at_sea += 1
                    print(self.days_spent_at_sea)

                # starved!
                else:
                    self.timer_at_sea.stop()
                    self.connection.send('change_map', ['29'])

        # main
            # mate0 must be on the flag ship
        role = self.game.my_role
        if not role.ships:
            mate_speak(self.game, role.mates[0], "How do I sail without a ship?")
            return

        if not role.ships[0].captain:
            mate_speak(self.game, role.mates[0], 'I need to be the captain of the flag ship.')
            return

        if role.ships[0].captain and role.name != role.ships[0].captain.name:
            mate_speak(self.game, role.mates[0], 'I need to be on the flag ship.')
            return

        if self.game.my_role.map != 'sea' and self.game.my_role.ships:
            # make sea image
            port_tile_x = hash_ports_meta_data[int(self.game.my_role.map) + 1]['x']
            port_tile_y = hash_ports_meta_data[int(self.game.my_role.map) + 1]['y']
            print(port_tile_x, port_tile_y)

            self.game.images['sea'] = self.game.map_maker.make_partial_world_map(port_tile_x, port_tile_y)

            # send
            self.game.connection.send('change_map', ['sea'])

            # init timer at sea

            # max days at sea (local game variable, not in role)
            self.game.max_days_at_sea = self.game.my_role.calculate_max_days_at_sea()
            self.game.days_spent_at_sea = 0
            # timer
            self.game.timer_at_sea = task.LoopingCall(pass_one_day_at_sea, self.game)
            self.game.timer_at_sea.start(c.ONE_DAY_AT_SEA_IN_SECONDS)

            # lose menu
            if len(self.game.menu_stack) >= 1:
                escape_twice(self.game)

    def load_supply(self):
        dict = {
            'Food':[self.load, 'Food'],
            'Water':[self.load, 'Water'],
            'Lumber':[self.load, 'Lumber'],
            'Shot':[self.load, 'Shot'],
        }
        self.game.button_click_handler.make_menu(dict)

    def load(self, item_name):
        self.game.button_click_handler.\
            make_input_boxes('load_supply', ['supply name', 'count', 'ship num'], [item_name])

    def unload_supply(self):
        dict = {
            'Food':[self.unload, 'Food'],
            'Water':[self.unload, 'Water'],
            'Lumber':[self.unload, 'Lumber'],
            'Shot':[self.unload, 'Shot'],
        }
        self.game.button_click_handler.make_menu(dict)

    def unload(self, item_name):
        self.game.button_click_handler.\
            make_input_boxes('unload_supply', ['supply name', 'count', 'ship num'], [item_name])

    def dry_dock(self):
        self.game.building_text = "We don't have any space left for you. Sorry."


class Market():
    def __init__(self, game):
        self.game = game

    def buy(self):
        # get available goods
        map_id = int(self.game.my_role.map)
        port = Port(map_id)
        available_goods_dict = port.get_availbale_goods_dict()

        # make menu
        dict = {}
        for item_name in available_goods_dict:
            buy_price = port.get_commodity_buy_price(item_name)
            show_text = item_name + ' ' + str(buy_price)
            dict[show_text] = [self.negotiate_for_price, [item_name,buy_price]]

        self.game.button_click_handler.make_menu(dict)

    def negotiate_for_price(self, params):
        # params
        cargo_name = params[0]
        buy_price = params[1]

        # price chat
        role = self.game.my_role
        buy_price_modifier = role.get_buy_price_modifier()
        buy_price = int(buy_price * buy_price_modifier)

        # if have permit
        if c.TAX_FREE_PERMIT_ID in role.bag.get_all_items_dict():
            self.game.building_text = f"Since you have a tax free permit, the price would be {buy_price}."
        else:
            buy_price = int(buy_price * 1.2)
            self.game.building_text = f"As you don't have a tax free permit, a 20% tax is applied to the price. " \
                                      f"So it would be {buy_price}."

        # i or my accountant speaks
        mate = None
        if role.accountant:
            mate = role.accountant
        else:
            mate = role.mates[0]
        mate_speak(self.game, mate, f'I think {buy_price} is a reasonable price for {cargo_name}.'
                                                          f'You can still make good profits.')

        # buy button
        def buy(cargo_name):
            self.game.button_click_handler. \
                make_input_boxes('buy_cargo', ['cargo name', 'count', 'ship num'], [cargo_name])

        dict = {
            'Buy': [buy, cargo_name]
        }

        self.game.button_click_handler.make_menu(dict)

    def sell(self):

        # def
        def show_cargo_in_ship(index):

            # def
            def negotiate_for_price(cargo_name):
                # price chat
                role = self.game.my_role

                port = role.get_port()
                unit_price = port.get_commodity_sell_price(cargo_name)

                sell_price_modifier = role.get_sell_price_modifier()
                unit_price = int(unit_price * sell_price_modifier)

                self.game.building_text = f"Alright. Alright... I'm willing to pay {unit_price} each ."
                mate = None
                if role.accountant:
                    mate = role.accountant
                else:
                    mate = role.mates[0]
                mate_speak(self.game, mate, f'I think {unit_price} is a reasonable price here for {cargo_name}.'
                                            f'What do you say?')

                # sell button
                def sell(cargo_name):
                    self.game.button_click_handler. \
                        make_input_boxes('sell_cargo', ['cargo name', 'count', 'ship num'], [cargo_name, '', str(index)])

                dict = {
                    'Sell': [sell, cargo_name]
                }

                self.game.button_click_handler.make_menu(dict)


            # main
            dict = {}

            for cargo_name, amount in self.game.my_role.ships[index].cargoes.items():
                dict[(str(amount) + ' ' + cargo_name)] = [negotiate_for_price, cargo_name]

            self.game.button_click_handler.make_menu(dict)

        # main
        dict = {}

        index = 0
        for ship in self.game.my_role.ships:
            dict[str(index)] = [show_cargo_in_ship, index]
            index += 1

        self.game.button_click_handler.make_menu(dict)




        # self.game.button_click_handler. \
        #     make_input_boxes('sell_cargo', ['cargo name', 'count', 'ship num'])

class Bar():
    def __init__(self, game):
        self.game = game

    def recruit_crew(self):
        self.game.button_click_handler. \
            make_input_boxes('hire_crew', ['count', 'ship_num'])

    def dismiss_crew(self):
        self.game.button_click_handler. \
            make_input_boxes('fire_crew', ['count', 'ship_num'])

    def meet(self):
        # no mate
        if int(self.game.my_role.map) % 2 == 0:
            self.game.button_click_handler.make_message_box("No one's availabale here.")

        # have mate
        else:
            mate_id = int((int(self.game.my_role.map) + 1) / 2)
            mate = Mate(mate_id)
            self.show_one_mate_to_hire(mate, mate_id)

    def show_one_mate_to_hire(self, mate, mate_id):
        # dict
        duty_name = 'None'
        if mate.duty:
            duty_name = 'captain of ' + mate.duty.name

        dict = {
            'name': mate.name,
            'nation': mate.nation,
            'duty': duty_name,
            'lv': f"{mate.lv} exp:{mate.exp} points:{mate.points}",
            'leadership': mate.leadership,
            'seamanship': f"{mate.seamanship} luck:{mate.luck}",
            'knowledge': f"{mate.knowledge} intuition:{mate.intuition}",
            'courage': f"{mate.courage} swordplay:{mate.swordplay}",
            'accounting': mate.accounting,
            'gunnery': mate.gunnery,
            'navigation': mate.navigation,
        }

        # make text from dict
        text = ''
        for k, v in dict.items():
            text += f'{k}:{v}<br>'

        # get figure image
        figure_surface = figure_x_y_2_image(self.game, mate.image_x, mate.image_y)

        # make window
        PanelWindow(pygame.Rect((59, 50), (350, 400)),
                    self.game.ui_manager, text, self.game, figure_surface)

        # make actions menu
        dict1 = {
            'Treat': [self.treat_mate, mate],
            'Gossip': [self.gossip, mate],
            'Hire': [self.hire_mate, mate_id],
        }
        self.game.button_click_handler.make_menu(dict1)

    def treat_mate(self, mate):
        message = 'Thank you!'
        mate_speak(self.game, mate, message)

    def gossip(self, mate):
        message = "I miss the high seas. Just can't sleep well on land."
        mate_speak(self.game, mate, message)

    def hire_mate(self, mate_id):
        self.game.button_click_handler. \
            make_input_boxes('hire_mate', ['mate id'], [str(mate_id)])

    def fire_mate(self):
        self.game.button_click_handler. \
            make_input_boxes('fire_mate', ['mate num'])

    def treat(self):
        self.game.building_text = f"Thank you for your hospitality, Captain {self.game.my_role.name}"

class DryDock():
    def __init__(self, game):
        self.game = game

    def new_ship(self):
        self.game.building_text = "No, kid. You don't to build a ship from scratch. " \
                                  "It takes too much time and resource. Just grab a used one."

    def used_ship(self):
        dict = {
            'view':self.view_used_ship,
            'buy':self.buy_used_ship,
        }

        self.game.button_click_handler.make_menu(dict)


    def view_used_ship(self):
        # prepare dict
        dict = {}

            # available ships
        my_map_id = int(self.game.my_role.map)
        port = Port(my_map_id)
        ships_list = port.get_available_ships()

        for ship_type in ships_list:
            dict[ship_type] = [self.show_used_ship, [ship_type]]

        # make menu
        self.game.button_click_handler.make_menu(dict)

    def buy_used_ship(self):
        # prepare dict
        dict = {}

        # available ships
        my_map_id = int(self.game.my_role.map)
        port = Port(my_map_id)
        ships_list = port.get_available_ships()

        for ship_type in ships_list:
            dict[ship_type] = [self.do_buy_ship, ship_type]

        # make menu
        self.game.button_click_handler.make_menu(dict)

    def do_buy_ship(self, type):
        self.game.button_click_handler. \
            make_input_boxes('buy_ship', ['name', 'type'], ['', type])

    def show_used_ship(self, params):
        # get param
        ship_type = params[0]

        # get ship
        ship = Ship('', ship_type)

        # dict
        dict = {
            'type': ship.type,
            'durability': f'{ship.now_hp}/{ship.max_hp}',
            'tacking': f'{ship.tacking}',
            'power': f'{ship.power}',
            'capacity': f'{ship.capacity}',
            'useful_capacity': f'{ship.useful_capacity}',
            'max_guns': f'{ship.max_guns}',
            'min_crew/max_crew': f'{ship.min_crew}/{ship.max_crew}',
            'price': ship.price
        }

        # make text from dict
        text = ''
        for k, v in dict.items():
            text += f'{k}:{v}<br>'

        # make window
        ship_image = self.game.images['ships'][ship.type.lower()]
        PanelWindow(pygame.Rect((59, 10), (350, 400)),
                    self.game.ui_manager, text, self.game, ship_image)

    def repair(self):
        self.game.change_and_send('repair_all', [])
        self.game.button_click_handler. \
            make_message_box('all ships repaired!')

    def sell_ship(self):
        self.game.button_click_handler. \
            make_input_boxes('sell_ship', ['num'])

    def remodel(self):
        dict = {
            'Capacity':self.remodel_capacity,
            'Weapon':test,
            'Figure':test,
            'Name': test,
        }
        self.game.button_click_handler.make_menu(dict)


    def remodel_capacity(self):
        self.game.button_click_handler. \
            make_input_boxes('remodel_ship_capacity', ['ship_num', 'max_crew', 'max_guns'])

    def invest(self):
        self.game.building_text = "You do want to invest 5 gold ingots to our industry? " \
                                  "That'll definitely help us."

class JobHouse:
    def __init__(self, game):
        self.game = game

    def job_assignment(self):
        self.game.building_text = "Don't know what to do? I have a few suggestions for you."

        dict = {
            'Discovery':self.discovery,
            'Trade':self.trade,
            'Fight':test,
        }
        self.game.button_click_handler.make_menu(dict)

    def discovery(self):
        # if have quest already
        role = self.game.my_role
        if role.quest_discovery:
            # quest done
            if role.quest_discovery in role.discoveries:
                self.game.change_and_send('submit_discovery_quest', [])

            # quest not finished
            else:
                self.game.button_click_handler. \
                        make_message_box("Oh! Have you finished your quest?")

        # no quest
        else:
            # generate random discovery
            discovery_id = random.randint(1, 98)
            # discovery_id = 48 (stonehenge, near london, for testing)
            discovery = Discovery(discovery_id)

            # make menu
            dict = {
                'OK':[self.start_discovery_quest, discovery_id],
                'Maybe Later':test,
            }
            self.game.button_click_handler.make_menu(dict)

            # show message
            self.game.button_click_handler. \
                make_message_box("I heard there's something "
                                 f"interesting at {discovery.longitude} {discovery.latitude}. "
                                 f"Would you like to go and investigate?")

    def start_discovery_quest(self, discovery_id):
        self.game.change_and_send('start_discovery_quest', [discovery_id])
        self.game.button_click_handler.make_message_box("Quest started.")


    def trade(self):
        dict = {
            'A':self.a,
            'B':self.b,
            'C':self.c,
            'D': self.d,
            'E': self.e,
            'F': self.f,
        }
        self.game.button_click_handler.make_menu(dict)

    def a(self):
        glass_beads_text = "Kids in West and East Africa are crazy about glass beads. " \
                           "Amsterdam produces tons of them. You can also get " \
                           "them from the mediterranean."
        spice_text = "You can get spice from South East Asia for about 3 gold coins each " \
                     "and sell them for more than 100 in Northern Europe."

        dict = {
            'Glass Beads':[self.game.button_click_handler.make_message_box, glass_beads_text],
            'Spice of Life':[self.game.button_click_handler.make_message_box, spice_text],
        }

        self.game.button_click_handler.make_menu(dict)

    def b(self):
        sleepy_text = "You can get tobacco from Havana or Caracas for about 35 gold coins each " \
                     "and sell them for about 250 in the Far East. " \
                   "You can get tea from India or the Far East for about 20 gold coins each " \
                     "and sell them for about 220 in Northern Europe. " \
                      "You can get coffee from the Middle East for about 35 gold coins each " \
                      "and sell them for about 340 in the Ottoman Empire. "

        feels_good_text = "You can get silk from Zeiton for about 30 gold coins each " \
             "and sell them for about 250 in Northern Europe."

        dict = {
            'Sleepy?':[self.game.button_click_handler.make_message_box, sleepy_text],
            'Feels Good':[self.game.button_click_handler.make_message_box, feels_good_text],
        }

        self.game.button_click_handler.make_menu(dict)

    def c(self):
        text = "You can get coral from South East Asia for about 50 gold coins each " \
                    "and sell them for about 280 in Europe. " \
               "You can get ivory from some Afrian ports for about 70 gold coins each " \
                    "and sell them for about 300 in the Far East. Do you know Timbuktu?" \
               "You can get pearl from the Far East for about 60 gold coins each " \
                    "and sell them for about 320 in Northern Europe. "

        dict = {
            'Luxury':[self.game.button_click_handler.make_message_box, text],
        }

        self.game.button_click_handler.make_menu(dict)

    def d(self):
        text = "You can get velvet from Iberia for about 80 gold coins each " \
                    "and sell them for about 310 in the Far East. " \
               "You can get amber from Aden for about 100 gold coins each " \
                    "and sell them for about 320 in the Mediterranean" \
               "You can get art from the Far East for about 120 gold coins each " \
                    "and sell them for about 400 in Europe. Athens and Cairo also sells art."

        dict = {
            'Mixed':[self.game.button_click_handler.make_message_box, text],
        }

        self.game.button_click_handler.make_menu(dict)

    def e(self):
        text = "You can get glassware from Venice or Copenhagen for about 180 gold coins each " \
                    "and sell them for about 450 in the Far East. " \

        dict = {
            'Delicate':[self.game.button_click_handler.make_message_box, text],
        }

        self.game.button_click_handler.make_menu(dict)

    def f(self):
        text = "You can get gold from Africa, Veracruz or Rio de Janeiro " \
                    "and sell them for about 1100 in Northern Europe. " \
                    "But, please be cautious. There are pirates out there."

        dict = {
            'Shiny':[self.game.button_click_handler.make_message_box, text],
        }

        self.game.button_click_handler.make_menu(dict)

    def contry_info(self):
        self.game.building_text = "Well...Don't worry about that."

class Church:
    def __init__(self, game):
        self.game = game

    def pray(self):
        self.game.building_text = 'May God bless you in all your endeavours.'

    def donate(self):
        self.game.building_text = 'Thank you for your generosity. ' \
                                  'But please take good care of yourself at the moment.'

class Palace:
    def __init__(self, game):
        self.game = game

    def meet_ruler(self):
        self.game.building_text = "I'm afraid the King's too buy to see you."

    def defect(self):
        self.game.building_text = "We do appreciate your willingness to join us. " \
                                  "Unfortunately, however, our quota has already been fulfilled this year."

    def ship_aid(self):
        self.game.building_text = "If you want a ship, go earn it."

    def gold_aid(self):
        self.game.building_text = "We'd like to help, but doing so " \
                                  "might be detrimental to the value you're trying to prove."

class Bank:
    def __init__(self, game):
        self.game = game

    def check_balance(self):
        balance = self.game.my_role.bank_gold
        self.game.building_text = f"Your current balance is {balance}."

    def deposit(self):
        self.game.building_text = "Dear customer, How much would you like to deposit?"
        self.game.button_click_handler.make_input_boxes('deposit_gold', ['amount'])

    def withdraw(self):
        self.game.building_text = "Dear customer, How much would you like to withdraw from your account?"
        self.game.button_click_handler.make_input_boxes('withdraw_gold', ['amount'])

    def borrow(self):
        # can borrow
        if self.game.my_role.bank_gold <= 0:
            max_credit = self.game.my_role.get_max_credit()
            self.game.building_text = f"Yes. We're happy to lend you up to {max_credit} gold coins." \
                                      f"Kindly remind you, your current balance is {self.game.my_role.bank_gold}."
            self.game.button_click_handler.make_input_boxes('borrow', ['amount'])

        # still have in bank gold
        else:
            self.game.building_text = "It seems you still have some left in your account."

    def repay(self):
        # can repay
        if self.game.my_role.bank_gold < 0:
            self.game.building_text = f"How much would you like to repay your debt?"
            self.game.button_click_handler.make_input_boxes('repay', ['amount'])

        # no need to repay
        else:
            self.game.building_text = "Oh. But you don't owe us anything."


class ItemShop:
    def __init__(self, game):
        self.game = game

    def buy(self):
        # get available items ids
        port = Port(int(self.game.my_role.map))
        items_ids = port.get_available_items_ids_for_sale()

        # make dict
        dict = {}
        for id in items_ids:
            if id in hash_items:
                item = Item(id)
                dict[item.name] = [self.buy_item_name_clicked, id]

        # show dict
        self.game.button_click_handler.make_menu(dict)

    def buy_item_name_clicked(self, item_id):
        # building speak
        item = Item(item_id)
        self.game.building_text = f'{item.name}? I charge {item.price} for this.'

        # show item image
        show_one_item([self, item])

        # show menu
        dict = {
            'OK': [self.buy_item, item_id],
        }
        self.game.button_click_handler.make_menu(dict)

    def buy_item(self, item_id):
        self.game.button_click_handler. \
            make_input_boxes('buy_items', ['item_id', 'count'], [str(item_id)])

    def sell(self):
        items_dict = self.game.my_role.bag.container

        dict = {}
        for k in items_dict.keys():
            item = Item(k)
            dict[f'{item.name} {items_dict[k]}'] = [self.item_name_clicked, k]

        self.game.button_click_handler.make_menu(dict)

    def item_name_clicked(self, item_id):
        # building speak
        item = Item(item_id)
        sell_price = int(item.price / 2)
        self.game.building_text = f'{item.name}? I can pay {sell_price}.'

        # show item image
        show_one_item([self, item])

        # show menu
        dict = {
            'OK': [self.sell_item, item_id],
        }
        self.game.button_click_handler.make_menu(dict)

    def sell_item(self, item_id):
        # sell and escape
        self.game.change_and_send('sell_item', [item_id])
        escape_thrice(self.game)
        reactor.callLater(0.3, self.sell)

        # building speak
        self.game.building_text = 'Thank you!'


def escape_twice(game):
    handle_pygame_event.escape(game, '')
    reactor.callLater(0.1, handle_pygame_event.escape, game, '')

def escape_thrice(game):
    handle_pygame_event.escape(game, '')
    reactor.callLater(0.1, handle_pygame_event.escape, game, '')
    reactor.callLater(0.2, handle_pygame_event.escape, game, '')

def target_clicked(self):
    # self is game
    dict = {
        'View Fleet': [self.button_click_handler.menu_click_handler.ships.fleet_info, True],
        'View Ships': [self.button_click_handler.menu_click_handler.ships.ship_info, True],
    }
    self.button_click_handler.make_menu(dict)

def figure_x_y_2_image(game, x=8, y=8):
    figures_image = game.images['figures']
    figure_surface = pygame.Surface((c.FIGURE_WIDTH, c.FIGURE_HIGHT))
    x_coord = -c.FIGURE_WIDTH * (x-1) - 3
    y_coord = -c.FIGURE_HIGHT * (y-1) - 3
    rect = pygame.Rect(x_coord, y_coord, c.FIGURE_WIDTH, c.FIGURE_HIGHT)
    figure_surface.blit(figures_image, rect)

    return figure_surface


def item_x_y_2_image(game, x, y):
    discoveries_and_items_images = game.images['discoveries_and_items']
    discovery_surface = pygame.Surface((c.ITEMS_IMAGE_SIZE, c.ITEMS_IMAGE_SIZE))
    x_coord = -c.ITEMS_IMAGE_SIZE * (x - 1)
    y_coord = -c.ITEMS_IMAGE_SIZE * (y - 1)
    rect = pygame.Rect(x_coord, y_coord, c.ITEMS_IMAGE_SIZE, c.ITEMS_IMAGE_SIZE)
    discovery_surface.blit(discoveries_and_items_images, rect)

    return discovery_surface

def mate_speak(game, mate, message):
    # make text from dict
    text = message

    # get figure image
    figure_surface = figure_x_y_2_image(game, mate.image_x, mate.image_y)

    # make window
    PanelWindow(pygame.Rect((59, 50), (350, 400)),
                game.ui_manager, text, game, figure_surface)

def figure_image_speak(game, image_x, image_y, message):
    # make text from dict
    text = message

    # get figure image
    figure_surface = figure_x_y_2_image(game, image_x, image_y)

    # make window
    PanelWindow(pygame.Rect((59, 50), (350, 400)),
                game.ui_manager, text, game, figure_surface)


def show_one_item(params):
    # accepts a list
    self = params[0]
    item = params[1]

    # dict
    dict = {
        'name': item.name,
        'description': item.description,
    }

    # make text from dict
    text = ''
    for k, v in dict.items():
        text += f'{v}<br>'

    # get figure image
    figure_surface = item_x_y_2_image(self.game, item.image[0], item.image[1])

    # make window
    PanelWindow(pygame.Rect((59, 50), (350, 400)),
                self.game.ui_manager, text, self.game, figure_surface)