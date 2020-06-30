import pygame_gui
import pygame
import constants as c

def test():
    print('testing')


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

    def make_menu(self, dict):
        SelectionListWindow(pygame.Rect((c.WINDOW_WIDTH - 224, 50),
                                        (224, 250)),
                            self.ui_manager,
                            dict, self.game)

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

    def on_button_click_items(self):
        dict = {
            'Items': test,
            'Discoveries': test,
            'Diary': test,
            'World Map': test,
            'Port Map': test
        }
        self.make_menu(dict)

    def on_button_click_cmds(self):
        dict = {
            'Set Target': test,
            'Enter Building': test,
            'Enter Port': test,
            'Escort': test,
            'Go Ashore': test,
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

        if self.game.my_role.map == 'battle':
            dict = {
                'View Enemy Ships': test,
                'View My Ships': test,
                'All Ships Move': test,
                'Strategy': test,
            }
            self.make_menu(dict)
        else:
            # make_message_box('only available in battle!')
            print('only available in battle!')