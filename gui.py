import pygame_gui
from pygame_gui._constants import UI_WINDOW_CLOSE, UI_WINDOW_MOVED_TO_FRONT, UI_BUTTON_PRESSED
import pygame
import constants as c
from port import Port
from role import Ship

import handle_pygame_event

from hashes.hash_ports_meta_data import hash_ports_meta_data
from hashes.look_up_tables import id_2_building_type

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
                                     relative_rect=pygame.Rect(0, 0, 180, 100),
                                     manager=ui_manager,
                                     wrap_to_height=True,
                                     container=self)

        # push into stacks
        game.menu_stack.append(self)
        game.selection_list_stack.append(self)

class InputBoxWindow(pygame_gui.elements.UIWindow):
    """a window with input boxes and an OK button"""
    def __init__(self, rect, ui_manager, protocol_name, params_names_list, game):

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
                pygame.Rect((150, 0 + line_distance*i), (50, 40)), ui_manager,
                object_id=str(i),
                container=self)

            # append to active_input_boxes
            self.game.active_input_boxes.append(input_box)

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

    def make_input_boxes(self, prtocol_name, params_list):
        InputBoxWindow(pygame.Rect((59, 50), (350, 400)),
                       self.ui_manager, prtocol_name, params_list, self.game)

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
                                  (224, 250)),
                      self.ui_manager,
                      text, self.game)

    def on_button_click_ships(self):
        dict = {
            'Fleet Info': self.menu_click_handler.ships.fleet_info,
            'Ship Info': self.menu_click_handler.ships.ship_info,
            'Rearrange': test,
        }
        self.make_menu(dict)

    def on_button_click_mates(self):
        dict = {
            'Admiral Info':test,
            'Mate Info':self.menu_click_handler.mates.mate_info,
        }
        self.make_menu(dict)

    def on_button_click_items(self):
        dict = {
            'Items': self.menu_click_handler.items.on_menu_click_items,
            'Discoveries': self.menu_click_handler.items.on_menu_click_discoveries,
            'Diary': test,
            'World Map': test,
            'Port Map': test
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
        if self.game.my_role.map.isdigit():
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

        # make panel window
        types = [ship.type for ship in ships]
        text = ''
        for type in types:
            text += f'{type}<br>'

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
            dict[str(index)] = [self.show_one_ship, [ship, target]]
            index += 1
        self.game.button_click_handler.make_menu(dict)

    def show_one_ship(self, params):
        # get param
        ship = params[0]
        target = params[1]

        # dict
        dict = {
            'name': ship.name,
            'type': ship.type,
            'durability': f'{ship.now_hp}/{ship.max_hp}',
            'tacking': f'{ship.tacking}',
            'power': f'{ship.power}',
            'capacity': f'{ship.capacity}',
            'useful_capacity': f'{ship.useful_capacity}',
            'max_guns': f'{ship.max_guns}',
            'crew': f'{ship.crew}',
            'min_crew/max_crew': f'{ship.min_crew}/{ship.max_crew}',
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

class MenuClickHandlerForMates():
    def __init__(self, game):
        self.game = game

    def mate_info(self):
        dict = {}
        for mate in self.game.my_role.mates:
            dict[mate.name] = [self.show_one_mate, [mate]]
        self.game.button_click_handler.make_menu(dict)

    def show_one_mate(self, params):
        # get param
        mate = params[0]

        # dict
        dict = {
            'name': mate.name,
            'nation': mate.nation,
        }

        # make text from dict
        text = ''
        for k, v in dict.items():
            text += f'{k}:{v}<br>'

        # make window
        PanelWindow(pygame.Rect((59, 50), (350, 400)),
                    self.game.ui_manager, text, self.game)

class MenuClickHandlerForItems():
    def __init__(self, game):
        self.game = game

    def on_menu_click_items(self):
        dict = {
            f'Gold {self.game.my_role.gold}': test
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_discoveries(self):
        my_discoveries = self.game.my_role.discoveries
        dict = {}
        for k in my_discoveries:
            dict[str(k)] = test
        self.game.button_click_handler.make_menu(dict)

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

                return

        print('no building to enter')

    def enter_port(self):
        self.game.change_and_send('change_map', ['port'])

    def go_ashore(self):
        self.game.change_and_send('discover', [])

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
        for ship in enemy_ships:
            dict[ship.name] = [self.game.button_click_handler.menu_click_handler.\
                ships.show_one_ship, [ship, True]]
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

    def on_menu_click_port(self):
        dict = {
            'Sail': self.port.sail,
            'Load Supply': self.port.load_supply,
            'Unload Supply': self.port.unload_supply,
            'Dry Dock': test,
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
            'Treat': test,
            'Hire Mate': self.bar.hire_mate,
            'Fire Mate': self.bar.fire_mate,
            'Waitress': test,
            'Gamble': test,
        }
        self.game.button_click_handler.make_menu(dict)


    def on_menu_click_dry_dock(self):
        dict = {
            'New Ship': test,
            'Used Ship': self.dry_dock.used_ship,
            'Repair': self.dry_dock.repair,
            'Sell': self.dry_dock.sell_ship,
            'Remodel': test,
            'Invest': test,
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
            'Meet Ruler': test,
            'Defect': test,
            'Gold Aid': test,
            'Ship Aid': test,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_job_house(self):
        dict = {
            'Job Assignment': test,
            'Country Info': test,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_bank(self):
        dict = {
            'Deposit': test,
            'Withdraw': test,
            'Borrow': test,
            'Repay': test,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_item_shop(self):
        dict = {
            'Buy': test,
            'Sell': test,
        }
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_church(self):
        dict = {
            'Pray': test,
            'Donate': test,
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
        self.game.change_and_send('change_map', ['sea'])

    def load_supply(self):
        dict = {
            'Food':test,
            'Water':test,
            'Lumber':test,
            'Shot':test,
            'Load':self.load
        }
        self.game.button_click_handler.make_menu(dict)

    def load(self):
        self.game.button_click_handler.\
            make_input_boxes('load_supply', ['supply name', 'count', 'ship num'])

    def unload_supply(self):
        dict = {
            'Food':test,
            'Water':test,
            'Lumber':test,
            'Shot':test,
            'Unload':self.unload,
        }
        self.game.button_click_handler.make_menu(dict)

    def unload(self):
        self.game.button_click_handler.\
            make_input_boxes('unload_supply', ['supply name', 'count', 'ship num'])

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
            dict[show_text] = test
        dict['buy'] = self.buy_cargo

        self.game.button_click_handler.make_menu(dict)

    def buy_cargo(self):
        self.game.button_click_handler. \
            make_input_boxes('buy_cargo', ['cargo name', 'count', 'ship num'])

    def sell(self):
        self.game.button_click_handler. \
            make_input_boxes('sell_cargo', ['cargo name', 'count', 'ship num'])

class Bar():
    def __init__(self, game):
        self.game = game

    def recruit_crew(self):
        self.game.button_click_handler. \
            make_input_boxes('hire_crew', ['count', 'ship_num'])

    def dismiss_crew(self):
        self.game.button_click_handler. \
            make_input_boxes('fire_crew', ['count', 'ship_num'])

    def hire_mate(self):
        self.game.button_click_handler. \
            make_input_boxes('hire_mate', ['name', 'nation'])

    def fire_mate(self):
        self.game.button_click_handler. \
            make_input_boxes('fire_mate', ['mate num'])

class DryDock():
    def __init__(self, game):
        self.game = game

    def used_ship(self):
        # prepare dict
        dict = {}

            # available ships
        my_map_id = int(self.game.my_role.map)
        port = Port(my_map_id)
        ships_list = port.get_available_ships()

        for ship_type in ships_list:
            dict[ship_type] = [self.show_used_ship, [ship_type]]

            # buy
        dict['buy'] = self.buy_used_ship

        # make menu
        self.game.button_click_handler.make_menu(dict)

    def buy_used_ship(self):
        self.game.button_click_handler. \
            make_input_boxes('buy_ship', ['name', 'type'])

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


def target_clicked(self):
    # self is game
    dict = {
        'View Fleet': [self.button_click_handler.menu_click_handler.ships.fleet_info, True],
        'View Ships': [self.button_click_handler.menu_click_handler.ships.ship_info, True],
    }
    self.button_click_handler.make_menu(dict)
