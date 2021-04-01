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
from role import Port, Mate, Ship, Discovery, Item, Gun

from image_processor import load_image

import handle_pygame_event

from hashes.hash_ports_meta_data import hash_ports_meta_data
from hashes.look_up_tables import id_2_building_type, lv_2_exp_needed_to_next_lv, capital_map_id_2_ruler_image
from hashes.look_up_tables import nation_2_tax_permit_id

from hashes.hash_items import hash_items
from hashes.hash_villages import villages_dict
from hashes.hash_bible_quotes import hash_bible_quotes
from hashes.hash_cannons import hash_cannons
from hashes import hash_villages

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
    _init_button(self, {'Ships': self.button_click_handler.on_button_click_ships}, 1)
    _init_button(self, {'Mates': self.button_click_handler.on_button_click_mates}, 2)
    _init_button(self, {'Items': self.button_click_handler.on_button_click_items}, 3)
    _init_button(self, {'Cmds': self.button_click_handler.cmds}, 4)
    _init_button(self, {'Options': self.button_click_handler.options}, 5)
    _init_button(self, {'Battle': self.button_click_handler.battle}, 6)
    _init_button(self, {'Sail': self.button_click_handler.login}, 7)
    _init_button(self, {'Test': self.button_click_handler.port}, 8)

    self.buttons_in_windows = {}

    # menu stack
    self.menu_stack = []
    self.selection_list_stack = []

def _init_button(self, dict, position):
    """argument self is game"""
    # get text and function from dict
    text_list = list(dict.keys())
    text = text_list[0]
    function = dict[text]
    text = self.translator.translate(text)

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
        text_box_list = []
        input_box_list = []
        line_distance = 40

        params_names_list = [self.game.translator.translate(name) for name in params_names_list]
        for i, name in enumerate(params_names_list):
            # text box
            text_box = pygame_gui.elements.UITextBox(html_text=name,
                                          relative_rect=pygame.Rect(0, 0 + line_distance*i, 120, 40),
                                          manager=ui_manager,
                                          wrap_to_height=True,
                                          container=self)
            text_box_list.append(text_box)

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
                input_box_list[index].kill()
                text_box_list[index].kill()
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

class FleetPanelWindow(pygame_gui.elements.UIWindow):
    """displays info"""
    def __init__(self, rect, ui_manager, game, target):
        # super
        super().__init__(rect, ui_manager,
                         window_display_title='',
                         object_id='#scaling_window',
                         resizable=True)

        self.game = game

        # get ships and nation
        ships = None
        nation = None
        speed = None
        if target:
            # enemy
            role = self.game.my_role
            enemy_name = role.enemy_name
            enemy_role = role._get_other_role_by_name(enemy_name)

            ships = enemy_role.ships
            nation = enemy_role.mates[0].nation
            speed = enemy_role.get_fleet_speed([])

            # my
        else:
            ships = self.game.my_role.ships
            nation = self.game.my_role.mates[0].nation
            speed = self.game.my_role.get_fleet_speed([])

        # get text
        types = [ship.type for ship in ships]
        text = ''
        for type in types:
            type_text = self.game.translator.translate(type)
            text += f'{type_text}, '

        fleet_speed_text = self.game.translator.translate('Fleet Speed')
        flag_text = self.game.translator.translate('Flag')
        knots_text = self.game.translator.translate('knots')
        nation_text = self.game.translator.translate(nation)
        text += f'<br>{fleet_speed_text}: {speed} {knots_text}'
        text += f'<br>{flag_text}: {nation_text}'

        # show bg
        bg_image = game.images['ships']['fleet_info']
        bg_rect = bg_image.get_rect()

        rect = pygame.Rect((0, -10), (bg_rect.width, bg_rect.height - 110))
        pygame_gui.elements.UIImage(rect,
                                    bg_image,
                                    ui_manager,
                                    container=self,
                                    anchors={'top': 'top', 'bottom': 'bottom',
                                             'left': 'left', 'right': 'right'})

        # get ships_images
        ships_types = [s.type for s in ships]
        ships_images = [game.images['ships'][t.lower()] for t in ships_types]

        # show images
        for index, image in enumerate(ships_images):
            image = pygame.transform.scale(image, (113, 85))

            image_width = image.get_rect().width
            image_height = image.get_rect().height
            if index <= 4:
                x = (image_width + 7) * index
                y = 0
            else:
                x = (image_width + 7) * (index - 5)
                y = image_height

            rect = pygame.Rect((x, y), (image.get_rect().size))
            pygame_gui.elements.UIImage(rect,
                                        image,
                                        ui_manager,
                                        container=self,
                                        anchors={'top': 'top', 'bottom': 'bottom',
                                               'left': 'left', 'right': 'right'})

        # show text
        if text and ships_images:
            x = 0
            y = ships_images[0].get_rect().height * 2 + 20

            rect = pygame.Rect(x, y, 600, 10)
            pygame_gui.elements.UITextBox(html_text=text,
                                         relative_rect=rect,
                                         manager=ui_manager,
                                         wrap_to_height=True,
                                         container=self)

        # push into stacks
        game.menu_stack.append(self)
        game.selection_list_stack.append(self)

class PanelWindow(pygame_gui.elements.UIWindow):
    """displays info"""
    def __init__(self, rect, ui_manager, text, game, image='none'):
        # default image
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
        dict = {self.game.translator.translate(k): dict[k] for k in dict.keys()}
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
    """ function 1: make menu, input box, msg box, speak ...
        function 2: menu text for most outside interfaces(buttons)
    """
    def __init__(self, game):
        self.game = game
        self.ui_manager = game.ui_manager
        self.menu_click_handler = MenuClickHandler(game)

    def escape(self):
        handle_pygame_event.escape(self.game, '')

    def escape_thrice(self):
        escape_thrice(self.game)

    def escape_4_times(self):
        handle_pygame_event.escape(game, '')
        reactor.callLater(0.1, handle_pygame_event.escape, game, '')
        reactor.callLater(0.2, handle_pygame_event.escape, game, '')
        reactor.callLater(0.3, handle_pygame_event.escape, game, '')

    def escape_n_times(self, n):
        game = self.game
        for i in range(n):
            delay = i * 0.1
            reactor.callLater(delay, handle_pygame_event.escape, game, '')

    def make_menu(self, dict):
        # make window
        SelectionListWindow(pygame.Rect((c.SELECTION_LIST_X, c.SELECTION_LIST_Y),
                                        (c.SELECTION_LIST_WIDTH, c.SELECTION_LIST_HIGHT)),
                            self.ui_manager,
                            dict, self.game)

        # sound
        self.game.sounds['wave'].play()

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
        do = False
        if self.game.my_role:
            if self.game.my_role.is_in_client_and_self():
                do = True
        else:
            do =True

        if do:
            text = self.game.translator.translate(text)
            MessageWindow(pygame.Rect((200, 50),
                                      (350, 350)),
                          self.ui_manager,
                          text, self.game)

    def building_speak(self, msg):
        self.game.building_text = msg

    def mate_speak(self, mate, msg):
        reactor.callLater(0.1, mate_speak, self.game, mate, msg)

    def i_speak(self, msg):
        mate = self.game.my_role.mates[0]
        reactor.callLater(0.1, mate_speak, self.game, mate, msg)

    def show_sunk_window(self):
        game = self.game
        rect = pygame.Rect(0, 0, c.WINDOW_WIDTH, c.WINDOW_HIGHT)
        text = "Your fleet starved."
        image = game.images['sunk']
        sunk_window = PanelWindow(rect, game.ui_manager, text, game, image)

    def show_victory_window(self):
        game = self.game
        rect = pygame.Rect(0, 0, c.WINDOW_WIDTH, c.WINDOW_HIGHT)
        text = "The enemy fleet was defeated!"
        image = game.images['win_battle']
        sunk_window = PanelWindow(rect, game.ui_manager, text, game, image)

    def show_defeat_window(self):
        game = self.game
        rect = pygame.Rect(0, 0, c.WINDOW_WIDTH, c.WINDOW_HIGHT)
        text = "We tried our best."
        image = game.images['lose_battle']
        sunk_window = PanelWindow(rect, game.ui_manager, text, game, image)

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
            'Equipments': self.menu_click_handler.items.equipments,
            'Items': self.menu_click_handler.items.on_menu_click_items,
            'Discoveries': self.menu_click_handler.items.on_menu_click_discoveries,
            'Diary': self.menu_click_handler.items.diary,
            'World Map': self.menu_click_handler.items.world_map,
            'Port Map': self.menu_click_handler.items.port_map
        }
        self.make_menu(dict)

    def cmds(self):
        dict = {
            'Enter Building (F)': self.menu_click_handler.cmds.enter_building,
            'Enter Port (M)': test,
            'Go Ashore (G)': self.menu_click_handler.cmds.go_ashore,
            'Battle (B)': test,
        }
        self.make_menu(dict)

    def options(self):
        dict = {
            'Language': test,
            'Sounds': self.menu_click_handler.options.sounds,
            'Hot Keys': test,
            'Exit': [handle_pygame_event.quit, self.game]
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
                'View Enemy Ships': self.menu_click_handler.battle.view_enemy_ships,
                'All Ships Target': self.menu_click_handler.battle.set_all_ships_target,
                'All Ships Strategy': self.menu_click_handler.battle.set_all_ships_attack_method,
                'One Ship Target': self.menu_click_handler.battle.set_one_ship_target,
                'One Ship Strategy': self.menu_click_handler.battle.set_one_ship_strategy,
                'Escape Battle': self.menu_click_handler.battle.escape_battle,
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
                'Create Character': self.menu_click_handler.login.make_character,
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
        self.target = MenuClickHandlerForTarget(game)

class MenuClickHandlerForShips():
    def __init__(self, game):
        self.game = game

    def fleet_info(self, target=False):
        FleetPanelWindow(pygame.Rect((0, 0), (900, 900)),
                    self.game.ui_manager, self.game, target)

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
        for index, ship in enumerate(ships):
            dict[f"{index} {ship.name}"] = [_show_one_ship, [self, ship, target, index]]
        self.game.button_click_handler.make_menu(dict)

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
                k = self.game.translator.translate(k)
                text += f'{k}: {v}<br>'
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
            dict[mate.name] = [self._show_one_mate, [mate, index]]
            index += 1
        self.game.button_click_handler.make_menu(dict)

    def _show_one_mate(self, params):
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

        nation_text = self.game.translator.translate(mate.nation)
        dict = {
            'name/nation': f"{mate.name}/{nation_text}",
            'duty': duty_name,
            '1': '',
            'lv/points': f"{mate.lv}/{mate.points}",
            'exp/to_next_lv': f"{mate.exp}/{lv_2_exp_needed_to_next_lv[mate.lv]}",
            '2': '',
            'leadership/seamanship/luck': f"{mate.leadership}/{mate.seamanship}/{mate.luck}",
            'knowledge/intuition': f"{mate.knowledge}/{mate.intuition}",
            'courage/swordplay': f"{mate.courage}/{mate.swordplay}",
            '3': '',
            'accounting/gunnery/navigation': f"{mate.accounting}/{mate.gunnery}/{mate.navigation}",
        }

        # make text from dict
        text = ''
        for k, v in dict.items():
            if k.isdigit():
                text += f'<br>'
            else:
                k = self.game.translator.translate(k)
                text += f'{k}: {v}<br>'

        # get figure image
        figure_surface = figure_x_y_2_image(self.game ,mate.image_x, mate.image_y)

        # make window
        PanelWindow(pygame.Rect((59, 12), (350, 400)),
                    self.game.ui_manager, text, self.game, figure_surface)

        # make actions menu
        dict1 = {
            'Set as Captain of': [self._set_as_captain_of, mate_num],
            'Relieve Duty': [self._relieve_duty, mate_num],
            'Level Up': [self._level_up, mate_num],
            'Add Attribute': [self._add_attribute, mate_num]
        }

        # admiral special functions
        if mate_num == 0:
            dict1['Distribute Exp'] = [self._assign_exp, mate_num]
        else:
            dict1['Set as hand'] = [self._set_as_hand, mate_num]


        self.game.button_click_handler.make_menu(dict1)

    def _set_as_hand(self, mate_num):

        def accountant(mate_num):
            self.game.change_and_send('set_mate_as_hand', [mate_num, 'accountant'])
            escape_thrice(self.game)
            reactor.callLater(0.3, self._show_one_mate, [self.game.my_role.mates[mate_num], mate_num])

        def first_mate(mate_num):
            self.game.change_and_send('set_mate_as_hand', [mate_num, 'first_mate'])
            escape_thrice(self.game)
            reactor.callLater(0.3, self._show_one_mate, [self.game.my_role.mates[mate_num], mate_num])

        def chief_navigator(mate_num):
            self.game.change_and_send('set_mate_as_hand', [mate_num, 'chief_navigator'])
            escape_thrice(self.game)
            reactor.callLater(0.3, self._show_one_mate, [self.game.my_role.mates[mate_num], mate_num])

        dict1 = {
            'Accountant': [accountant, mate_num],
            'First Mate': [first_mate, mate_num],
            'Chief Navigator': [chief_navigator, mate_num],
        }

        mate = self.game.my_role.mates[mate_num]
        if mate.duty:
            mate_speak(self.game, mate, "I already have a duty.")
        else:
            self.game.button_click_handler.make_menu(dict1)

    def _assign_exp(self, mate_num):
        escape_twice(self.game)
        reactor.callLater(0.3, self.game.button_click_handler. \
            make_input_boxes, 'give_exp_to_other_mates', ['mate num', 'amount'])

    def _level_up(self, mate_num):
        # def
        def do_lv_up(mate_num):
            self.game.change_and_send('add_mates_lv', [mate_num])
            escape_thrice(self.game)
            reactor.callLater(0.3, self._show_one_mate, [self.game.my_role.mates[mate_num], mate_num])

        # main
        dict = {
            'OK': [do_lv_up, mate_num]
        }

        mate = self.game.my_role.mates[mate_num]
        exp_needed = lv_2_exp_needed_to_next_lv[mate.lv]

        if mate.exp < exp_needed:
            mate_speak(self.game, mate, "I don't have enough experience to reach the next level.")
        else:
            self.game.button_click_handler.make_menu(dict)

    def _add_attribute(self, mate_num):

        def do_add_attribute(params):
            mate_num = params[0]
            attribute_name = params[1]

            mate = self.game.my_role.mates[mate_num]
            if mate.points == 0:
                mate_speak(self.game, mate, "I have 0 point.")
            else:
                self.game.change_and_send('add_mates_attribute', [mate_num, attribute_name])
                escape_thrice(self.game)
                reactor.callLater(0.3, self._show_one_mate, [self.game.my_role.mates[mate_num], mate_num])
                reactor.callLater(0.35, self._add_attribute, mate_num)

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

    def _set_as_captain_of(self, mate_num):
        # def
        def do_set_as_captain_of(ship_id):
            ship = self.game.my_role.ships[ship_id]
            if ship.captain:
                mate = self.game.my_role.mates[mate_num]
                mate_speak(self.game, mate, f"{ship.name} has a captain.")
            else:
                self.game.change_and_send('set_mates_duty', [mate_num, ship_id])
                escape_thrice(self.game)
                reactor.callLater(0.3, self._show_one_mate, [self.game.my_role.mates[mate_num], mate_num])

        # main
        d = {}
        for id, ship in enumerate(self.game.my_role.ships):
            d[f"{id} {ship.name}"] = [do_set_as_captain_of, id]

        mate = self.game.my_role.mates[mate_num]
        if mate.duty:
            mate_speak(self.game, mate, "I already have a duty.")
        else:
            self.game.button_click_handler.make_menu(d)

    def _relieve_duty(self, mate_num):
        # def
        def do_relieve_duty(mate_num):
            self.game.change_and_send('relieve_mates_duty', [mate_num])
            escape_thrice(self.game)
            reactor.callLater(0.3, self._show_one_mate, [self.game.my_role.mates[mate_num], mate_num])

        # main
        dict = {
            'OK': [do_relieve_duty, mate_num]
        }
        self.game.button_click_handler.make_menu(dict)


class MenuClickHandlerForItems():
    def __init__(self, game):
        self.game = game

    def equipments(self):
        equipments_dict = self.game.my_role.body.container

        dict = {}
        for k in equipments_dict.keys():
            item_id = equipments_dict[k]
            k = self.game.translator.translate(k)
            if item_id == None:
                dict[f'{k}: {item_id}'] = test
            else:
                item = Item(item_id)
                dict[f'{k}: {item.name}'] = [self._unequip_item_name_clicked, item]

        self.game.button_click_handler.make_menu(dict)

    def _unequip_item_name_clicked(self, item):
        # show item's info
        show_one_item([self, item])

        # menu for item use
        dict = {}
        dict['Unequip'] = [self._unequip_item_clicked, item]
        self.game.button_click_handler.make_menu(dict)

    def _unequip_item_clicked(self, item):
        self.game.change_and_send('unequip', [item.id])
        escape_thrice(self.game)
        reactor.callLater(0.3, self.equipments)

    def on_menu_click_items(self):
        # show bag load (e.g: 8/10)
        dict = {}
        now_items_count = self.game.my_role.bag.get_all_items_count()
        now_bag_load = str(now_items_count) + '/' + str(c.MAX_ITEMS_IN_BAG)
        dict[now_bag_load] = test

        # show items
        items_dict = self.game.my_role.bag.container
        for k in items_dict.keys():
            item = Item(k)
            dict[f'{item.name} {items_dict[k]}'] = [self._item_name_clicked, item]

        self.game.button_click_handler.make_menu(dict)

    def _item_name_clicked(self, item):
        # show item's info
        show_one_item([self, item])

        # menu for item use
        if hasattr(item, 'type'):
            dict = {}
            if item.type == 'consumable':
                dict['Use'] = [self._use_item_clicked, item]
            elif item.type in self.game.my_role.body.container:
                dict['Equip'] = [self._equip_item_clicked, item]

            self.game.button_click_handler.make_menu(dict)

    def _use_item_clicked(self, item):
        self.game.change_and_send('consume_potion', [item.id])
        escape_thrice(self.game)
        reactor.callLater(0.3, self.on_menu_click_items)

    def _equip_item_clicked(self, item):
        self.game.change_and_send('equip', [item.id])
        escape_thrice(self.game)
        reactor.callLater(0.3, self.on_menu_click_items)

    def on_menu_click_discoveries(self):
        my_discoveries = self.game.my_role.discoveries
        dict = {}
        for id in my_discoveries:
            discovery = Discovery(id)
            dict[discovery.name] = [self._show_one_discovery, discovery]
        self.game.button_click_handler.make_menu(dict)

    def _show_one_discovery(self, discovery):
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

    def diary(self):
        dict = {
            'Main Objective': self._main_objective,
            'Quest Log': self._quest_log,
            'Abandon Quest': self._abandon_quest,
        }
        self.game.button_click_handler.make_menu(dict)

    def _main_objective(self):
        if self.game.my_role.main_quest_port:
            port = self.game.my_role.main_quest_port
            building = self.game.my_role.main_quest_building

            msg = f"Go to {port} {building}."
            self.game.button_click_handler.i_speak(msg)

    def _quest_log(self):
        discovery_quest_id = self.game.my_role.quest_discovery
        if discovery_quest_id:
            discovery = Discovery(discovery_quest_id)
            msg = f"On quest to investigate {discovery.longitude} {discovery.latitude}"
            i_speak(self.game, msg)
        else:
            msg = f"I have no quest."
            i_speak(self.game, msg)

    def _abandon_quest(self):
        dict = {
            'OK': self.__do_abandon,
        }
        self.game.button_click_handler.make_menu(dict)

    def __do_abandon(self):
        if self.game.my_role.have_quest():
            self.game.change_and_send('give_up_discovery_quest', [])
            msg = f"Quest abandoned."
            i_speak(self.game, msg)
        else:
            msg = f"I have no quest to abandon."
            i_speak(self.game, msg)

    def world_map(self):
        # image
        world_map_grids_image = self.game.images['world_map_grids']
        image_rect = world_map_grids_image.get_rect()
        text = ''

        PanelWindow(pygame.Rect((10, 10), (image_rect.width, (image_rect.height + 60))),
                    self.game.ui_manager, text, self.game, world_map_grids_image)

        # sound
        self.game.sounds['map'].play()

    def port_map(self):
        # image
        if self.game.images['port']:
            port_map = pygame.transform.scale(self.game.images['port'], (c.PORT_MAP_SIZE, c.PORT_MAP_SIZE))
            text = ''

            PanelWindow(pygame.Rect((10, 10), ((c.PORT_MAP_SIZE + 30), (c.PORT_MAP_SIZE + 60))),
                    self.game.ui_manager, text, self.game, port_map)

        # sound
        self.game.sounds['map'].play()

class MenuClickHandlerForCmds():
    def __init__(self, game):
        self.game = game

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
                    8:self.game.button_click_handler.menu_click_handler.port.on_menu_click_msc,
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
                            self._present_event(pending_event)
                            self.game.change_and_send('trigger_quest', [])

                return

        print('no building to enter')

    def _present_event(self, event):
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
            # discovery_id = random.randint(0, 90)
            # self.game.change_and_send('discover', [discovery_id])
            self.game.button_click_handler.make_message_box("Can't find anything.")


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

    def sounds(self):
        d = {
            'Music': self._music,
            'Effect': self._effect,
        }
        self.game.button_click_handler.make_menu(d)

    def _music(self):
        d = {
            'Pause': [pygame.mixer.music.set_volume, 0],
            'Resume': [pygame.mixer.music.set_volume, 1],
        }
        self.game.button_click_handler.make_menu(d)

    def _effect(self):
        d = {
            'Pause': self.__stop_all_sound_effects,
            'Resume': self.__resume_all_sound_effects,
        }
        self.game.button_click_handler.make_menu(d)

    def __stop_all_sound_effects(self):
        for sound in self.game.sounds.values():
            sound.set_volume(0)

    def __resume_all_sound_effects(self):
        for sound in self.game.sounds.values():
            sound.set_volume(1)

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

    def view_enemy_ships(self):
        # get enemy ships
        enemy_ships = self.game.other_roles[self.game.my_role.enemy_name].ships

        # new menu
        dict = {}
        index = 0
        for ship in enemy_ships:
            dict[ship.name] = [_show_one_ship, [self, ship, True, index]]
            index += 1
        self.game.button_click_handler.make_menu(dict)

    def set_all_ships_target(self):
        d = {}
        enemy_ships = self.game.my_role.get_enemy_role().ships
        for id, s in enumerate(enemy_ships):
            d[str(id)] = [self._do_set_all_ships_target, id]
        self.game.button_click_handler.make_menu(d)

    def _do_set_all_ships_target(self, id):
        self.game.change_and_send('set_all_ships_target', [id])
        self.game.button_click_handler.escape()

    def set_all_ships_attack_method(self):
        d = {
            'Shoot': [self._do_set_all_ships_strategy, 0],
            'Engage': [self._do_set_all_ships_strategy, 1],
            'Escape': [self._do_set_all_ships_strategy, 2],
        }
        self.game.button_click_handler.make_menu(d)

    def _do_set_all_ships_strategy(self, attack_method_id):
        self.game.change_and_send('set_all_ships_attack_method',
                                  [attack_method_id])
        self.game.button_click_handler.escape()

    def set_one_ship_target(self):
        my_ships_text = self.game.translator.translate('My Ships')
        d = {
            my_ships_text: test,
        }
        for id, s in enumerate(self.game.my_role.ships):
            if id != 0:
                d[str(id)] = [self._choose_target, id]
        self.game.button_click_handler.make_menu(d)

    def _choose_target(self, my_ship_id):
        targets_text = self.game.translator.translate('Targets')
        d = {
            targets_text: test,
        }
        enemy_ships = self.game.my_role.get_enemy_role().ships
        for id, s in enumerate(enemy_ships):
            d[str(id)] = [self.__do_set_target_for_one_ship, [my_ship_id, id]]
        self.game.button_click_handler.make_menu(d)

    def __do_set_target_for_one_ship(self, params):
        my_ship_id = params[0]
        target_ship_id = params[1]
        attack_method_id = None

        self.game.change_and_send('set_one_ships_strategy',
                                  [my_ship_id, target_ship_id, attack_method_id])
        self.game.button_click_handler.escape()

    def set_one_ship_strategy(self):
        d = {}
        for id, s in enumerate(self.game.my_role.ships):
            if id != 0:
                d[str(id)] = [self._choose_strategy, id]
        self.game.button_click_handler.make_menu(d)

    def _choose_strategy(self, ship_id):
        d = {
            'Shoot': [self.__do_set_strategy_for_one_ship, [ship_id, 0]],
            'Engage': [self.__do_set_strategy_for_one_ship, [ship_id, 1]],
            'Escape': [self.__do_set_strategy_for_one_ship, [ship_id, 2]],
        }
        self.game.button_click_handler.make_menu(d)

    def __do_set_strategy_for_one_ship(self, params):
        ship_id = params[0]
        attack_method_id = params[1]
        target_id = self.game.my_role.ships[ship_id].target

        self.game.change_and_send('set_one_ships_strategy',
                                  [ship_id, target_id, attack_method_id])
        self.game.button_click_handler.escape()

    def escape_battle(self):
        game = self.game
        if game.my_role.your_turn_in_battle:
            if game.my_role.can_escape() or c.DEVELOPER_MODE_ON:
                game.connection.send('exit_battle', [])
            else:
                game.button_click_handler.i_speak(
                    "Must be far enough from enemy flagship to escape.")


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
        self.inn = Inn(game)
        self.msc = Msc(game)
        self.fortune_house = FortuneHouse(game)

    def on_menu_click_port(self):
        dict = {
            'Sail': self.port.sail,
            'Load Supply': self.port.load_supply,
            'Unload Supply': self.port.unload_supply,
        }
        self.game.button_click_handler.make_menu(dict)

        self.game.building_text = 'Ready to sail?'

    def on_menu_click_market(self):
        dict = {
            'Buy': self.market.buy,
            'Sell': self.market.sell,
            'Price Index': self.market.price_index,
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
            'Waitress': self.bar.waitress,
        }
        self.game.button_click_handler.make_menu(dict)


    def on_menu_click_dry_dock(self):
        dict = {
            'New Ship': self.dry_dock.new_ship,
            'Used Ship': self.dry_dock.used_ship,
            'Repair': self.dry_dock.repair,
            'Sell': self.dry_dock.sell_ship,
            'Remodel': self.dry_dock.remodel,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_inn(self):
        dict = {
            'Check In': self.inn.check_in,
            'Gossip': self.inn.gossip,
            'Port Info': self.inn.port_info,
            'Walk Around': self.inn.walk_around,
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

    def on_menu_click_msc(self):
        dict = {
            'Enter': self.msc.enter,
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
            'Life': self.fortune_house.life,
            'Career': self.fortune_house.career,
            'Love': self.fortune_house.love,
            'Mates': self.fortune_house.mates,
        }
        self.game.button_click_handler.make_menu(dict)

class MenuClickHandlerForTarget():
    def __init__(self, game):
        self.game = game

    def view_fleet(self):
        if not self.game.my_role.get_enemy_role().name == self.game.my_role.name:
            self.game.button_click_handler.menu_click_handler.ships.fleet_info(True)

    def view_ships(self):
        if not self.game.my_role.get_enemy_role().name == self.game.my_role.name:
            self.game.button_click_handler.menu_click_handler.ships.ship_info(True)

    def gossip(self):
        if not self.game.my_role.get_enemy_role().name == self.game.my_role.name:
            enemy_name = self.game.my_role.enemy_name
            enemy_role = self.game.my_role._get_other_role_by_name(enemy_name)
            target_mate = enemy_role.mates[0]
            destination_port = None
            if enemy_role.out_ward:
                destination_port = Port((enemy_role.end_port_id - 1))
            else:
                destination_port = Port((enemy_role.start_port_id - 1))
            fleet_type = enemy_role.get_npc_fleet_type()
            message = f"I'm {target_mate.name} directing a {fleet_type} fleet " \
                      f"from {target_mate.nation}. We are heading to {destination_port.name}."
            mate_speak(self.game, target_mate, message)

    def captain_info(self):
        if not self.game.my_role.get_enemy_role().name == self.game.my_role.name:
            enemy_role = self.game.my_role.get_enemy_role()
            if enemy_role:
                mate = enemy_role.mates[0]
                self._show_captain(mate)

    def _show_captain(self, mate):
        # dict
        nation_text = self.game.translator.translate(mate.nation)
        dict = {
            'name/nation': f"{mate.name}/{nation_text}",
            '1': '',
            'lv': f"{mate.lv}",
            '2': '',
            'leadership/seamanship/luck': f"{mate.leadership}/{mate.seamanship}/{mate.luck}",
            'knowledge/intuition': f"{mate.knowledge}/{mate.intuition}",
            'courage/swordplay': f"{mate.courage}/{mate.swordplay}",
            '3': '',
            'accounting/gunnery/navigation': f"{mate.accounting}/{mate.gunnery}/{mate.navigation}",
        }

        # make text from dict
        text = ''
        for k, v in dict.items():
            if k.isdigit():
                text += f'<br>'
            else:
                k = self.game.translator.translate(k)
                text += f'{k}:{v}<br>'

        # get figure image
        figure_surface = figure_x_y_2_image(self.game, mate.image_x, mate.image_y)

        # make window
        PanelWindow(pygame.Rect((59, 12), (350, 400)),
                    self.game.ui_manager, text, self.game, figure_surface)

    def view_mates(self):


        pass

class Harbor():
    """menu options under building port"""
    def __init__(self, game):
        self.game = game

    def sail(self):
        # show dialogue
        max_days = self.game.my_role.calculate_max_days_at_sea()
        fleet_speed = self.game.my_role.get_fleet_speed([])

        t1 = self.game.trans("You can sail for")
        t2 = self.game.trans("days")
        t3 = self.game.trans("at an average speed of")
        t4 = self.game.trans("knots")
        t5 = self.game.trans("Are you sure you want to set sail?")
        msg = f"{t1} {max_days} {t2} " \
              f"{t3} {fleet_speed} {t4}. " \
              f"{t5}"
        self.game.button_click_handler.building_speak(msg)

        # make menu
        dict = {
            'OK':self._sail_ok,
        }
        self.game.button_click_handler.make_menu(dict)

    def _sail_ok(self):
        # can't sail
        role = self.game.my_role
        if not role.ships:
            msg = "How do I sail without a ship?"
            msg = self.game.trans(msg)
            mate_speak(self.game, role.mates[0], msg)
            return

        if not role.ships[0].captain:
            msg = 'I need to be the captain of the flag ship.'
            msg = self.game.trans(msg)
            mate_speak(self.game, role.mates[0], msg)
            return

        if role.ships[0].captain and role.name != role.ships[0].captain.name:
            msg = 'I need to be on the flag ship.'
            msg = self.game.trans(msg)
            mate_speak(self.game, role.mates[0], msg)
            return

        # can sail
        if self.game.my_role.map != 'sea' and self.game.my_role.ships:
            # delete dynamic npcs
            self.game.man = None
            self.game.woman = None

            # make sea image
            port_tile_x = hash_ports_meta_data[int(self.game.my_role.map) + 1]['x']
            port_tile_y = hash_ports_meta_data[int(self.game.my_role.map) + 1]['y']
            print(port_tile_x, port_tile_y)

            self.game.time_of_day_index = 1
            time_of_day = c.TIME_OF_DAY_OPTIONS[self.game.time_of_day_index]
            self.game.images['sea'] = self.game.map_maker.make_partial_world_map(port_tile_x, port_tile_y, time_of_day)

            # send
            self.game.connection.send('change_map', ['sea'])

            # init timer at sea

            # max days at sea (local game variable, not in role)
            self.game.max_days_at_sea = self.game.my_role.calculate_max_days_at_sea()
            self.game.days_spent_at_sea = 0
            # timer
            self.game.timer_at_sea = task.LoopingCall(self.__pass_one_day_at_sea, self.game)
            self.game.timer_at_sea.start(c.ONE_DAY_AT_SEA_IN_SECONDS)

            # lose menu
            if len(self.game.menu_stack) >= 1:
                escape_twice(self.game)

            # music
            file_name = random.choice(['sea', 'sea_1'])
            pygame.mixer.music.load(f"../../assets/sounds/music/{file_name}.ogg")
            pygame.mixer.music.play(-1)

    def __pass_one_day_at_sea(self, game):
        if game.my_role.map == 'sea':

            # pass peacefully
            if game.days_spent_at_sea <= game.max_days_at_sea:

                game.days_spent_at_sea += c.EACH_DAY_PASS

                # low supply alert
                if (game.max_days_at_sea - game.days_spent_at_sea) == c.SUPPLY_LOW_ALERT_DAYS:
                    msg = f"Our supply is low. We can only last for {c.SUPPLY_LOW_ALERT_DAYS} more days!"
                    game.button_click_handler.i_speak(msg)

                # rand lighting and rain?
                if random.random() < 4 / 100:
                    game.sounds['lightning'].play()
                    reactor.callLater(2, game.sounds['rain'].play)

            # starved!
            else:
                game.timer_at_sea.stop()
                prev_port_map_str = str(game.my_role.prev_port_map_id)
                game.connection.send('change_map', [prev_port_map_str, -1])

                # show image
                game.button_click_handler.show_sunk_window()

    def load_supply(self):
        t1 = self.game.trans("Everything is 5 coins each")
        t2 = self.game.trans("Once set, we refill your ships based on the configurations immediately after you enter any port")
        msg = f"{t1}. " \
              f"{t2[:12]} " \
              f"{t2[12:]}. "
        self.game.button_click_handler.building_speak(msg)
        dict = {
            'Food':[self._load, 'Food'],
            'Water':[self._load, 'Water'],
            # 'Lumber':[self._load, 'Lumber'],
            # 'Shot':[self._load, 'Shot'],
        }
        self.game.button_click_handler.make_menu(dict)

    def _load(self, item_name):
        self.game.button_click_handler.\
            make_input_boxes('load_supply', ['supply name', 'count', 'ship num'], [item_name])

    def unload_supply(self):
        dict = {
            'Food':[self._unload, 'Food'],
            'Water':[self._unload, 'Water'],
            # 'Lumber':[self._unload, 'Lumber'],
            # 'Shot':[self._unload, 'Shot'],
        }
        self.game.button_click_handler.make_menu(dict)

    def _unload(self, item_name):
        self.game.button_click_handler.\
            make_input_boxes('unload_supply', ['supply name', 'count', 'ship num'], [item_name])


class Market():
    def __init__(self, game):
        self.game = game

    def buy(self):
        # get available goods
        map_id = int(self.game.my_role.map)
        port = self.game.my_role.get_port()
        available_goods_dict = port.get_availbale_goods_dict()

        # make menu
        dict = {}
        for item_name in available_goods_dict:
            buy_price = port.get_commodity_buy_price(item_name)
            show_text = item_name + ' ' + str(buy_price)
            dict[show_text] = [self._negotiate_for_price, [item_name,buy_price]]

        self.game.button_click_handler.make_menu(dict)

    def _negotiate_for_price(self, params):
        # params
        cargo_name = params[0]
        buy_price = params[1]

        # price chat
        role = self.game.my_role
        buy_price_modifier = role.get_buy_price_modifier()
        buy_price = int(buy_price * buy_price_modifier)

        # if have permit
        right_tax_permit_id = nation_2_tax_permit_id[role.nation]
        if right_tax_permit_id in role.bag.get_all_items_dict() and role.nation == role.mates[0].nation:
            text = self.game.translator.translate("Alright. Since you have a tax free permit, the price would be")
            self.game.building_text = f"{text} {buy_price}."
        else:
            buy_price = int(buy_price * 1.2)
            text1 = self.game.translator.translate("Alright. As you don't have a tax free permit, a 20% tax is applied to the price.")
            text2 = self.game.translator.translate("So it would be")
            self.game.building_text = f'{text1} ' \
                                      f"{text2} {buy_price}."


        # i or my accountant speaks
        mate = None
        if role.accountant:
            mate = role.accountant
        else:
            mate = role.mates[0]
        text1 = self.game.translator.translate("I think")
        text2 = self.game.translator.translate("is a reasonable price for")
        text3 = self.game.translator.translate("You can still make good profits.")
        msg = f"{text1} {buy_price} {text2} {cargo_name}. <br>"\
              f"{text3}."
        mate_speak(self.game, mate, msg)

        # buy button
        def buy(cargo_name):
            escape_twice(self.game)
            reactor.callLater(0.3, self.game.button_click_handler. \
                make_input_boxes, 'buy_cargo',
                              ['cargo name', 'count', 'ship num'],
                              [cargo_name])

        dict = {
            'Buy': [buy, cargo_name]
        }

        self.game.button_click_handler.make_menu(dict)

    def sell(self):
        dict = {}

        index = 0
        for ship in self.game.my_role.ships:
            dict[str(index)] = [self._show_cargo_in_ship, index]
            index += 1

        self.game.button_click_handler.make_menu(dict)

    def _show_cargo_in_ship(self, index):
        dict = {}

        for cargo_name, amount in self.game.my_role.ships[index].cargoes.items():
            dict[(str(amount) + ' ' + cargo_name)] = [self.__negotiate_for_sell_price, [cargo_name, index]]

        self.game.button_click_handler.make_menu(dict)

    def __negotiate_for_sell_price(self, params):
        cargo_name = params[0]
        index = params[1]

        # price chat
        role = self.game.my_role

        port = role.get_port()
        unit_price = port.get_commodity_sell_price(cargo_name)

        sell_price_modifier = role.get_sell_price_modifier()
        unit_price = int(unit_price * sell_price_modifier)

        text1 = self.game.translator.translate("Alright. Alright... I'm willing to pay")
        text2 = self.game.translator.translate("each")
        self.game.building_text = f"{text1} {unit_price} {text2}."
        mate = None
        if role.accountant:
            mate = role.accountant
        else:
            mate = role.mates[0]

        text3 = self.game.translator.translate('I think')
        text4 = self.game.translator.translate('is a reasonable price for')
        text5 = self.game.translator.translate('What do you say?')
        mate_speak(self.game, mate, f'{text3} {unit_price} {text4} {cargo_name}. <br>'
                                    f'{text5}')

        # sell button
        def sell(cargo_name):
            escape_thrice(self.game)
            reactor.callLater(0.3, self.game.button_click_handler. \
                make_input_boxes, 'sell_cargo',
                              ['cargo name', 'ship num', 'count'],
                              [cargo_name, str(index)])

        dict = {
            'Sell': [sell, cargo_name]
        }

        self.game.button_click_handler.make_menu(dict)

    def price_index(self):
        text_1_trans = self.game.translator.translate('The price index of this port is')
        text_2_trans = self.game.translator.translate('Any cargo you buy or sell will be affected by this index.')
        msg = f"{text_1_trans} {self.game.my_role.price_index}%. " \
              f"{text_2_trans[:8]} " \
              f"{text_2_trans[8:]}"


        self.game.button_click_handler.building_speak(msg)

class Bar():
    def __init__(self, game):
        self.game = game

    def recruit_crew(self):
        text1 = self.game.translator.translate('Who wants to sail with Captain')
        text2 = self.game.translator.translate('Each of you will get')
        text3 = self.game.translator.translate('coins')
        self.game.building_text = f"{text1} {self.game.my_role.name}? " \
                                  f"{text2} {c.CREW_UNIT_COST} {text3}."
        self.game.button_click_handler. \
            make_input_boxes('hire_crew', ['count', 'ship_num'])

    def dismiss_crew(self):
        text1 = self.game.translator.translate('Is your ship too crowded?')
        self.game.button_click_handler.building_speak(text1)
        self.game.button_click_handler. \
            make_input_boxes('fire_crew', ['count', 'ship_num'])

    def treat(self):
        text1 = self.game.translator.translate('Thank you for your hospitality, Captain')
        self.game.building_text = f"{text1} {self.game.my_role.name}"

    def meet(self):
        # no mate
        if int(self.game.my_role.map) % 2 == 0:
            text1 = self.game.translator.translate("No one's availabale here.")
            self.game.button_click_handler.building_speak(text1)

        # have mate
        else:
            mate_id = int((int(self.game.my_role.map) + 1) / 2)
            mate = Mate(mate_id)

            my_mates_names = {mate.name for mate in self.game.my_role.mates}

            if mate.name in my_mates_names:
                self.game.button_click_handler.building_speak("No one's availabale here.")
            else:
                self._show_one_mate_to_hire(mate, mate_id)

    def _show_one_mate_to_hire(self, mate, mate_id):
        # dict
        duty_name = 'None'
        if mate.duty:
            duty_name = 'captain of ' + mate.duty.name

        nation_text = self.game.trans(mate.nation)
        dict = {
            'name/nation': f"{mate.name}/{nation_text}",
            'lv': mate.lv,
            'leadership/seamanship/luck': f"{mate.leadership}/{mate.seamanship}/{mate.luck}",
            'knowledge/intuition': f"{mate.knowledge}/{mate.intuition}",
            'courage/swordplay': f"{mate.courage}/{mate.swordplay}",
            'accounting/gunnery/navigation': f"{mate.accounting}/{mate.gunnery}/{mate.navigation}",
        }

        # make text from dict
        text = ''
        for k, v in dict.items():
            k = self.game.trans(k)
            text += f'{k}: {v}<br>'

        # get figure image
        figure_surface = figure_x_y_2_image(self.game, mate.image_x, mate.image_y)

        # make window
        PanelWindow(pygame.Rect((59, 50), (350, 400)),
                    self.game.ui_manager, text, self.game, figure_surface)

        # make actions menu
        dict1 = {
            'Treat': [self._treat_mate, mate],
            'Gossip': [self._gossip, mate],
            'Hire': [self._hire_mate, mate_id],
        }
        self.game.button_click_handler.make_menu(dict1)

    def _treat_mate(self, mate):
        message = self.game.translator.translate('Thank you!')
        mate_speak(self.game, mate, message)

    def _gossip(self, mate):
        message = self.game.translator.translate("I miss the high seas. Just can't sleep well on land.")
        mate_speak(self.game, mate, message)

    def _hire_mate(self, mate_id):

        def do_hire():
            self.game.change_and_send('hire_mate', [mate_id])

        d = {
            'OK': do_hire
        }
        self.game.button_click_handler.make_menu(d)

    def fire_mate(self):
        mates = self.game.my_role.mates[1:]

        d = {}
        for mate_num, mate in enumerate(mates, 1):
            d[mate.name] = [self._mate_name_clicked, [mate, mate_num]]

        self.game.button_click_handler.make_menu(d)

    def _mate_name_clicked(self, params):
        mate = params[0]
        mate_num = params[1]

        msg = "Did I do anything wrong? Are you sure?"
        msg = self.game.translator.translate(msg)
        mate_speak(self.game, mate, msg)

        def do_fire():
            self.game.change_and_send('fire_mate', [mate_num])
            escape_thrice(self.game)
            reactor.callLater(0.3,
                              self.game.button_click_handler.mate_speak,
                              mate, "Farewell. I'll miss you captain.")

        dic = {
            'OK': do_fire
        }
        self.game.button_click_handler.make_menu(dic)

    def waitress(self):
        port = self.game.my_role.get_port()
        maid = port.get_maid()
        if maid:
            # speak
            t1 = self.game.trans("I'm")
            t2 = self.game.trans("How are you?")
            self._maid_speak(f"{t1} {maid.name}. {t2}")

            # menu
            dict = {
                'Ask Info': self._ask_info,
                'Investigate': self._investigate,
                'Tell Story': self._tell_story,
            }
            self.game.button_click_handler.make_menu(dict)
        else:
            t1 = self.game.trans("We don't have a maid here. Sorry.")
            self.game.building_text = t1

    def _maid_speak(self, msg):
        port = self.game.my_role.get_port()
        maid = port.get_maid()
        figure_image_speak(self.game, maid.image[0], maid.image[1], msg)

    def _ask_info(self):
        msg = self.game.trans("Uhh... That's too personal.")
        self._maid_speak(msg)

    def _investigate(self):
        dict = {
            'England': [self.__nation_clicked, 'England'],
            'Holland': [self.__nation_clicked, 'Holland'],
            'Portugal': [self.__nation_clicked, 'Portugal'],
            'Spain': [self.__nation_clicked, 'Spain'],
            'Italy': [self.__nation_clicked, 'Italy'],
            'Turkey': [self.__nation_clicked, 'Turkey'],
        }
        self.game.button_click_handler.make_menu(dict)

    def __nation_clicked(self, nation):
        print(nation)
        dict = {
            'Merchant Fleet': [self.___send_request, [nation, 'merchant']],
            'Convoy Fleet': [self.___send_request, [nation, 'convoy']],
            'Battle Fleet': [self.___send_request, [nation, 'battle']],
        }
        self.game.button_click_handler.make_menu(dict)

    def ___send_request(self, params):
        nation = params[0]
        fleet_type = params[1]
        self.game.connection.send('get_npc_info', [nation, fleet_type])

    def _tell_story(self):
        msg = self.game.trans("Wow! Interesting...")
        self._maid_speak(msg)

class DryDock():
    def __init__(self, game):
        self.game = game

    def new_ship(self):
        msg = "No, kid. You don't want to build a ship from scratch. " \
              "It takes too much time and resource. Just grab a used one."
        msg = self.game.trans(msg)
        self.game.button_click_handler.make_message_box(msg)

    def used_ship(self):
        # speak
        msg = "Have a look. These are the kinds of ships we offer."
        msg = self.game.trans(msg)
        self.game.button_click_handler.building_speak(msg)

        # prepare dict
        dict = {}

        # available ships
        my_map_id = int(self.game.my_role.map)
        port = self.game.my_role.get_port()
        ships_list = port.get_available_ships()

        for ship_type in ships_list:
            dict[ship_type] = [self._ship_name_clicked, ship_type]

        # make menu
        self.game.button_click_handler.make_menu(dict)

    def _ship_name_clicked(self, ship_type):
        # show ship info
        self._show_used_ship([ship_type])

        # show menu
        dict = {
            'OK': [self._do_buy_ship, ship_type]
        }
        self.game.button_click_handler.make_menu(dict)

    def _do_buy_ship(self, type):
        escape_twice(self.game)
        reactor.callLater(0.3, self.game.button_click_handler. \
            make_input_boxes, 'buy_ship', ['type', 'name'], [type])

    def _show_used_ship(self, params):
        # get param
        ship_type = params[0]

        # get ship
        ship = Ship('', ship_type)

        # dict
        type_text = self.game.trans(ship.type)
        dict = {
            'type': type_text,
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
            k = self.game.trans(k)
            text += f'{k}: {v}<br>'

        # make window
        ship_image = self.game.images['ships'][ship.type.lower()]
        PanelWindow(pygame.Rect((59, 10), (350, 400)),
                    self.game.ui_manager, text, self.game, ship_image)

    def repair(self):
        # calcu need_to_repair
        need_to_repair = False
        ships = self.game.my_role.ships
        for s in ships:
            if s.now_hp < s.max_hp:
                need_to_repair = True
                break

        # if need
        if need_to_repair:
            cost = self.game.my_role._calc_repair_all_cost()
            t1 = self.game.trans("Repairing all your ships will cost you")
            t2 = self.game.trans("coins")
            t3 = self.game.trans("Are you sure?")
            self.game.building_text = f"{t1} {cost} {t2}. " \
                                      f"{t3}"

            d = {
                'OK': self._do_repair,
            }
            self.game.button_click_handler.make_menu(d)

        else:
            t1 = self.game.trans("All your ships are in perfect shape.")
            self.game.building_text = t1

    def _do_repair(self):
        self.game.change_and_send('repair_all', [])

    def sell_ship(self):
        dict = {}
        index = 0
        for ship in self.game.my_role.ships:
            dict[str(index)] = [self._ship_id_clicked, index]
            index += 1
        self.game.button_click_handler.make_menu(dict)

    def _ship_id_clicked(self , ship_id):
        # show ship panel
        params = [self, self.game.my_role.ships[ship_id], False, ship_id]
        _show_one_ship(params)
        price = int(self.game.my_role.ships[ship_id].price / 2)

        t1 = self.game.trans("I can pay")
        t2 = self.game.trans("for this one")
        self.game.building_text = f"{t1} {price} {t2} ."

        # show ok menu
        dict = {
            'OK': [self._sell, ship_id]
        }
        self.game.button_click_handler.make_menu(dict)

    def _sell(self, id):
        escape_thrice(self.game)
        reactor.callLater(0.3, self.sell_ship)
        if id == 0:
            t1 = self.game.trans("You can't sell your flag ship.")
            self.game.building_text = t1
        else:
            t1 = self.game.trans("We'll take good care of her!")
            self.game.building_text = t1
            self.game.change_and_send('sell_ship', [id])

    def remodel(self):
        dict = {
            'Capacity':self._remodel_capacity,
            'Weapon':self._remodel_weapon,
            'Name': self._remodel_name,
        }
        self.game.button_click_handler.make_menu(dict)

    def _remodel_capacity(self):
        my_ships = self.game.my_role.ships
        d = {}
        for id, s in enumerate(my_ships):
            d[str(id) + " " + s.name] = [self.__do_remodel_capacity, id]

        self.game.button_click_handler.make_menu(d)

    def __do_remodel_capacity(self, id):
        # building speaks max guns and max crew
        ship = self.game.my_role.ships[id]
        model_ship = Ship('x', ship.type)
        model_ship.max_guns
        model_ship.max_crew

        t1 = self.game.trans("This ship can have at most")
        t2 = self.game.trans("guns and")
        t3 = self.game.trans("crew")
        msg = f"{t1} {model_ship.max_guns} " \
              f"{t2} {model_ship.max_crew} {t3}."
        self.game.button_click_handler.building_speak(msg)

        # show input boxes
        self.game.button_click_handler. \
            make_input_boxes('remodel_ship_capacity', ['ship_num', 'max_crew', 'max_guns'],
                             [id])

    def _remodel_weapon(self):
        ships = self.game.my_role.ships
        d = {}
        for id, ship in enumerate(ships):
            d[str(id) + " " + ship.name] = [self.__ship_name_clicked, [self, ship, False, id]]
        self.game.button_click_handler.make_menu(d)

    def __ship_name_clicked(self, params):
        ship_id = params[-1]

        # show ship info
        _show_one_ship(params)

        # show cannons menu
        d = {}
        for gun_id in hash_cannons.keys():
            gun = Gun(gun_id)
            d[gun.name] = [self.___gun_name_clicked, [ship_id, gun_id]]
        self.game.button_click_handler.make_menu(d)

    def ___gun_name_clicked(self, params):
        ship_id = params[0]
        gun_id = params[1]

        ship = self.game.my_role.ships[ship_id]
        gun = Gun(gun_id)

        t1 = self.game.trans("costs")
        t2 = self.game.trans("each")
        t3 = self.game.trans("of them will cost you")
        t4 = self.game.trans("Are you sure?")
        msg = f"{gun.name} {t1} {gun.price} {t2}. " \
              f"{ship.max_guns} {t3} {ship.max_guns * gun.price}. " \
              f"{t4}"
        self.game.button_click_handler.make_message_box(msg)

        d = {
            'OK': [self.____do_remodel_gun, [ship_id, gun_id]]
        }
        self.game.button_click_handler.make_menu(d)

    def ____do_remodel_gun(self, params):
        ship_id = params[0]
        gun_id = params[1]
        self.game.change_and_send('remodel_ship_gun', [ship_id, gun_id])


    def _remodel_name(self):
        self.game.button_click_handler. \
            make_input_boxes('remodel_ship_name', ['ship_num', 'name'])


class JobHouse:
    def __init__(self, game):
        self.game = game

    def job_assignment(self):
        self.game.building_text = "Don't know what to do? I have a few suggestions for you."

        dict = {
            'Discover':self._discover,
            'Trade':self._trade,
            'Fight':self._fight,
        }
        self.game.button_click_handler.make_menu(dict)

    def _discover(self):
        # if have quest already
        role = self.game.my_role
        if role.have_quest():
            # quest done
            if role.quest_discovery in role.discoveries:
                self.game.change_and_send('submit_discovery_quest', [])

            # quest not finished
            else:
                self.game.building_text = "Oh! Have you finished your quest?"

        # no quest
        else:
            # generate random discovery
            set_for_unkown_places = villages_dict.keys() - self.game.my_role.discoveries.keys()

            # set not empty
            if set_for_unkown_places:
                discovery_id = random.choice(list(set_for_unkown_places))
                #  (stonehenge, near london, for testing)
                # discovery_id = 48
                discovery = Discovery(discovery_id)

                # show message
                self.game.building_text = f"I heard there's something interesting " \
                                          f"at {discovery.longitude} {discovery.latitude}. " \
                                          f"Would you like to go and investigate? "

                # make menu
                dict = {
                    'OK': [self.__start_discovery_quest, discovery_id],
                }
                self.game.button_click_handler.make_menu(dict)

            else:
                self.game.building_text = "Wow~  You have been to lots of places. " \
                                          "I'm afraid I can't provide any more advice."

    def __start_discovery_quest(self, discovery_id):
        self.game.change_and_send('start_discovery_quest', [discovery_id])
        self.game.button_click_handler.i_speak("Quest accepted.")

    def _trade(self):
        dict = {
            'A':self.__a,
            'B':self.__b,
            'C':self.__c,
            'D': self.__d,
            'E': self.__e,
            'F': self.__f,
        }
        self.game.button_click_handler.make_menu(dict)

    def __a(self):
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

    def __b(self):
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

    def __c(self):
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

    def __d(self):
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

    def __e(self):
        text = "You can get glassware from Venice or Copenhagen for about 180 gold coins each " \
                    "and sell them for about 450 in the Far East. " \

        dict = {
            'Delicate':[self.game.button_click_handler.make_message_box, text],
        }

        self.game.button_click_handler.make_menu(dict)

    def __f(self):
        text = "You can get gold from Africa, Veracruz or Rio de Janeiro " \
                    "and sell them for about 1100 in Northern Europe. " \
                    "But, please be cautious. There are pirates out there."

        dict = {
            'Shiny':[self.game.button_click_handler.make_message_box, text],
        }

        self.game.button_click_handler.make_menu(dict)

    def _fight(self):
        text = "I don't have much information on that. " \
               "But why don't you talk with the bar girls?"
        self.game.building_text = text

    def contry_info(self):
        msg = "Go to your capital and ask your ruler about this. "
        self.game.button_click_handler.building_speak(msg)


class Church:
    def __init__(self, game):
        self.game = game

    def pray(self):
        port_id = self.game.my_role.get_port_id()
        quote_str = hash_bible_quotes[port_id]
        self.game.button_click_handler.make_message_box(quote_str)

    def donate(self):
        self.game.building_text = 'Thank you for your generosity. ' \
                                  'But please take good care of yourself at the moment.'

class Palace:
    def __init__(self, game):
        self.game = game

    def meet_ruler(self):
        t1 = self.game.trans("Hello")
        t2 = self.game.trans("Are you interested in our allied ports")
        msg = f"{t1}, {self.game.my_role.name}. <br>{t2}?"
        image_x, image_y = capital_map_id_2_ruler_image[self.game.my_role.get_map_id()]
        figure_image_speak(self.game, image_x, image_y, msg)

        d = {
            'Country Info': self._get_country_info
        }
        self.game.button_click_handler.make_menu(d)

    def _get_country_info(self):
        self.game.connection.send('get_allied_ports_and_pi', [])

    def defect(self):
        t1 = self.game.trans("You do wish to join us?")
        t2 = self.game.trans("You need to be over lv 15 and contribute 20 gold ingots.")
        msg = f"{t1} " \
              f"{t2}"
        self.game.button_click_handler.building_speak(msg)

        d = {
            'OK': self._do_defect
        }
        self.game.button_click_handler.make_menu(d)

    def _do_defect(self):
        self.game.change_and_send('defect', [])
        self.game.button_click_handler.escape()

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
            self.game.building_text = f"Yes. We're happy to lend you up to {max_credit} gold coins. " \
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
        # show bag load (e.g: 8/10)
        dict = {}
        now_items_count = self.game.my_role.bag.get_all_items_count()
        now_bag_load = str(now_items_count) + '/' + str(c.MAX_ITEMS_IN_BAG)
        dict[now_bag_load] = test

        # show items
        items_dict = self.game.my_role.bag.container
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


class Inn:
    def __init__(self, game):
        self.game = game

    def check_in(self):
        msg = "Sweet dreams."
        msg = self.game.trans(msg)
        self.game.button_click_handler.building_speak(msg)

    def gossip(self):
        msg = "I've no idea why this port keeps allying to different nations."
        msg = self.game.trans(msg)
        msg = f"{msg[:12]} " \
              f"{msg[12:]} "
        self.game.button_click_handler.building_speak(msg)

    def port_info(self):
        t1 = self.game.trans("This port is allied to")
        t2 = self.game.trans(self.game.my_role.nation)
        msg = f"{t1}{t2}."
        self.game.button_click_handler.building_speak(msg)

    def walk_around(self):
        port = self.game.my_role.get_port()
        port_name = port.name
        port_name = port_name.lower()

        # load img
        sketch = None
        try:
            sketch = load_image(f"../../assets/images/port_sketches/{port_name}.png")
            sketch = pygame.transform.scale(sketch,
                                     (c.WINDOW_WIDTH - 50,
                                      c.WINDOW_HIGHT - 50))
        except:
            msg = "Didn't see anything interesting."
            self.game.button_click_handler.i_speak(msg)
        else:
            sketch_rect = sketch.get_rect()
            sketch_rect.height += 50
            PanelWindow(sketch_rect, self.game.ui_manager,
                        None, self.game, image=sketch)


class Msc:
    def __init__(self, game):
        self.game = game

    def enter(self):
        msg = "Entry is by invitation only."
        self.game.button_click_handler.building_speak(msg)


class FortuneHouse:
    def __init__(self, game):
        self.game = game

    def life(self):
        d = {
            'Talents': self._talents,
            'Skills': self._skills,
        }
        self.game.button_click_handler.make_menu(d)

    def _talents(self):
        msg = "Each of us in this world is born with three talents. " \
              "Navigation allows you to sail faster. " \
              "Gunnery makes you a natural fighter. " \
              "Accounting makes you comfortable doing business. " \
              "You don't seem to have any of them. " \
              "I'm afraid you can't have them even if you pay me."
        self.game.button_click_handler.make_message_box(msg)

    def _skills(self):
        msg = "There are six skills you can acquire. " \
              "Leadership allows you to find more company. " \
              "Seamanship allows you to sail faster. " \
              "Luck? Do you believe it? " \
              "Knowledge allows you to buy cargo with less cost. " \
              "Intuition allows you to sell cargo for more profit. " \
              "Courage makes your shooting more effective in battle. " \
              "Swordplay makes your engaging more effective. "
        self.game.button_click_handler.make_message_box(msg)

    def career(self):
        msg = "If you need advice on acreer development, " \
              "go consult the guy at the job house."
        self.game.button_click_handler.building_speak(msg)

    def love(self):
        msg = "Bar girls know a lot, but there aren't many of them."
        self.game.button_click_handler.building_speak(msg)

    def mates(self):
        msg = "Have you found good company?"
        self.game.button_click_handler.building_speak(msg)


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
        'View Fleet': self.button_click_handler.menu_click_handler.target.view_fleet,
        'View Ships': self.button_click_handler.menu_click_handler.target.view_ships,
    }

    # if npc
    if self.my_role.get_enemy_role().is_npc():
        dict['Gossip'] = self.button_click_handler.menu_click_handler.target.gossip
        dict['Captain Info'] = self.button_click_handler.menu_click_handler.target.captain_info
    # if player
    else:
        dict['Captain Info'] = self.button_click_handler.menu_click_handler.target.captain_info


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

def i_speak(game, message):
    # make text from dict
    text = message
    mate = game.my_role.mates[0]

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
    if hasattr(item, 'effects_description'):
        dict['effects_description'] = item.effects_description

    # make text from dict
    text = ''
    for k, v in dict.items():
        text += f'{v}<br>'

    # get figure image
    figure_surface = item_x_y_2_image(self.game, item.image[0], item.image[1])

    # make window
    PanelWindow(pygame.Rect((59, 50), (350, 400)),
                self.game.ui_manager, text, self.game, figure_surface)

def _show_one_ship(params):
    # get param
    self = params[0]
    ship = params[1]
    target = params[2]
    ship_id = params[3]

    # dict
    captain_name = 'None'
    if ship.captain:
        captain_name = ship.captain.name

    speed = 1
    if ship_id == 0:
        speed = ship.get_speed(self.game.my_role)
    else:
        speed = ship.get_speed()

    gun = Gun(ship.gun)
    gun_name = gun.name
    knots_text = self.game.translator.translate('knots')
    dict = {
        'name/type/captain': f'{ship.name}/{ship.type}/{captain_name}',
        '1': '',
        'tacking/power/speed': f'{ship.tacking}/{ship.power}/{speed} {knots_text}',
        'durability': f'{ship.now_hp}/{ship.max_hp}',
        '2': '',
        'capacity': f'{ship.capacity}',
        'max_guns/guns': f'{ship.max_guns}/{ship.max_guns} {gun_name}',
        'min_crew/crew/max_crew': f'{ship.min_crew}/{ship.crew}/{ship.max_crew}',
        '3': '',
        'affective_capacity': f'{ship.useful_capacity}',
    }

    # if no target selected
    if not target:
        # supply
        food_text = self.game.translator.translate('F')
        water_text = self.game.translator.translate('W')
        dict['supplies'] = f"{food_text}{ship.supplies['Food']} {water_text}{ship.supplies['Water']} "

        # cargo
        cargoes_dict = ship.cargoes
        for cargo_name, count in cargoes_dict.items():
            dict['supplies'] += cargo_name + ':' + str(count)

    # make text from dict
    text = ''
    for k, v in dict.items():
        if k.isdigit():
            text += f'<br>'
        else:
            k = self.game.translator.translate(k)
            text += f'{k}: {v}<br>'

    # make window
    ship_image = self.game.images['ships'][ship.type.lower()]
    PanelWindow(pygame.Rect((59, 12), (350, 400)),
                self.game.ui_manager, text, self.game, ship_image)