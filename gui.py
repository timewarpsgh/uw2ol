import pygame_gui
import pygame
import constants as c

def test():
    print('testing')


class PanelWindow(pygame_gui.elements.UIWindow):
    def __init__(self, rect, ui_manager, text, game):

        # super
        super().__init__(rect, ui_manager,
                         window_display_title='Scale',
                         object_id='#scaling_window',
                         resizable=True)

        # image
        pygame_gui.elements.UIImage(pygame.Rect((0, 0), (game.images['ship_at_sea'].get_rect().size
                                                         )),
                                    game.images['ship_at_sea'], ui_manager,
                                  container=self,
                                  anchors={'top': 'top', 'bottom': 'bottom',
                                           'left': 'left', 'right': 'right'})

        # text box
        pygame_gui.elements.UITextBox(html_text=text,
                                                 relative_rect=pygame.Rect(0, 50, 320, 10),
                                                 manager=ui_manager,
                                                 wrap_to_height=True,
                                                 container=self)

        # push into menu stack
        game.menu_stack.append(self)

        # push into selection_list_stack
        game.selection_list_stack.append(self)

class SelectionListWindow(pygame_gui.elements.UIWindow):
    def __init__(self, rect, ui_manager, dict, game):

        # super
        super().__init__(rect, ui_manager,
                         window_display_title='',
                         object_id='#scaling_window',
                         resizable=True)

        # gets
        self.dict = dict
        item_list = dict.keys()

        # list box
        self.selection_list = pygame_gui.elements.UISelectionList(pygame.Rect(10, 10, 174, 170),
                                            item_list=item_list,
                                            manager=ui_manager,
                                            container=self,
                                            allow_multi_select=False)

        # push into menu stack
        game.menu_stack.append(self)

        # push into selection_list_stack
        game.selection_list_stack.append(self.selection_list)


class ButtonClickHandler():
    def __init__(self, game):
        self.game = game
        self.ui_manager = game.ui_manager
        self.menu_click_handler = MenuClickHandler(game)

    def make_menu(self, dict):
        SelectionListWindow(pygame.Rect((c.WINDOW_WIDTH - 224, 50),
                                        (224, 250)),
                            self.ui_manager,
                            dict, self.game)

    def on_button_click_ships(self):
        dict = {
            'Fleet Info': self.menu_click_handler.ships.on_menu_click_fleet_info,
            'Ship Info': self.menu_click_handler.ships.on_menu_click_ship_info,
            'Rearrange': test,
        }
        self.make_menu(dict)

    def on_button_click_mates(self):
        dict = {
            'Admiral Info':test,
            'Mate Info':self.menu_click_handler.mates.on_menu_click_mate_info,
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

    def on_button_click_cmds(self):
        dict = {
            'Set Target': test,
            'Enter Building': test,
            'Enter Port': self.menu_click_handler.cmds.on_menu_click_enter_port,
            'Escort': test,
            'Go Ashore': self.menu_click_handler.cmds.on_menu_click_go_ashore,
            'View': test,
            'Gossip': test,
            'Battle': test,
        }
        self.make_menu(dict)

    def on_button_click_options(self):
        dict = {
            'Language': test,
            'Sounds': test,
            'Hot Keys': test,
            'Exit': test,
        }
        self.make_menu(dict)

    def on_button_click_port(self):
        if self.game.my_role.map == 'port':
            dict = {
                'Market': test,
                'Bar': test,
                'Dry Dock': test,
                'Port': test,
                'Inn': test,
                'Palace': test,
                'Job House': test,
                'Misc': test,
                'Bank': test,
                'Item Shop': test,
                'Church': test,
                'Fortune House': test,
            }
            self.make_menu(dict)
        else:
            print('only available in port!')
            # make_message_box('only available in port!')

    def on_button_click_battle(self):

        if 'battle' in self.game.my_role.map:
            dict = {
                'View Enemy Ships': self.menu_click_handler.battle.on_menu_click_view_enemy_ships,
                'View My Ships': test,
                'All Ships Move': test,
                'Strategy': test,
            }
            self.make_menu(dict)
        else:
            # make_message_box('only available in battle!')
            print('only available in battle!')

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

class MenuClickHandlerForShips():
    def __init__(self, game):
        self.game = game

    def on_menu_click_fleet_info(self):
        # get my ships
        my_ships = self.game.my_role.ships

        # make panel window
        types = [ship.type for ship in my_ships]
        text = ''
        for type in types:
            text += f'{type}<br>'

        PanelWindow(pygame.Rect((59, 50), (350, 400)),
                    self.game.ui_manager, text, self.game)

    def on_menu_click_ship_info(self):
        # get my ships
        my_ships = self.game.my_role.ships

        # new menu
        dict = {}
        for ship in my_ships:
            dict[ship.name] = [self.on_menu_click_show_one_ship, [ship]]
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_show_one_ship(self, params):
        # get param
        ship = params[0]

        # dict
        dict = {
            'name': ship.name,
            'type': ship.type,
            'hp': f'{ship.now_hp}/{ship.max_hp}',
            'crew': f'{ship.crew}',
        }

        # supply
        for k, v in ship.supplies.items():
            dict[k] = v

            # cargo
        cargoes_dict = ship.cargoes
        for cargo_name, count in cargoes_dict.items():
            dict[cargo_name] = count

        # make text from dict
        text = ''
        for k, v in dict.items():
            text += f'{k}:{v}<br>'

        # make window
        PanelWindow(pygame.Rect((59, 50), (350, 400)),
                    self.game.ui_manager, text, self.game)

class MenuClickHandlerForMates():
    def __init__(self, game):
        self.game = game

    def on_menu_click_mate_info(self):
        dict = {}
        for mate in self.game.my_role.mates:
            dict[mate.name] = [self.on_menu_click_show_one_mate, [mate]]
        self.game.button_click_handler.make_menu(dict)

    def on_menu_click_show_one_mate(self, params):
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

    # def on_menu_click_set_target():
    #     make_input_boxes('set_target', ['target name'])

    def on_menu_click_enter_port(self):
        self.game.change_and_send('change_map', ['port'])

    def on_menu_click_go_ashore(self):
        self.game.change_and_send('discover', [])

    # def on_menu_click_battle():
    #
    #     try:
    #         target_name = g_player.role.target_name
    #         change_and_send('enter_battle_with', [target_name])
    #     except:
    #         print('no target!')

class MenuClickHandlerForOptions():
    def __init__(self, game):
        self.game = game

class MenuClickHandlerForPort():
    def __init__(self, game):
        self.game = game

class MenuClickHandlerForBattle():
    def __init__(self, game):
        self.game = game

    # def on_menu_click_all_ships_move():
    #     change_and_send('all_ships_operate', [0])

    def on_menu_click_view_enemy_ships(self):
        # get enemy ships
        enemy_ships = self.game.other_roles[self.game.my_role.enemy_name].ships

        # new menu
        dict = {}
        for ship in enemy_ships:
            dict[ship.name] = [self.game.button_click_handler.menu_click_handler.\
                ships.on_menu_click_show_one_ship, [ship]]
        self.game.button_click_handler.make_menu(dict)