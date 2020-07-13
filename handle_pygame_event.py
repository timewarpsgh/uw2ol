import pygame
from twisted.internet import reactor, task
import constants as c

EVENT_MOVE = pygame.USEREVENT + 1
EVENT_HEART_BEAT = pygame.USEREVENT + 2

def handle_pygame_event(self, event):
    """argument self is game"""
    # quit
    if event.type == pygame.QUIT:
        quit(self, event)

    # key down
    elif event.type == pygame.KEYDOWN:

        # return (focus text entry)
        if event.key == pygame.K_RETURN:
            self.text_entry.focus()
            self.text_entry_active = True

        # escape
        if event.key == pygame.K_ESCAPE:
            escape(self, event)

        # other keys
        if not self.text_entry_active:
            other_keys_down(self, event)

    # key up
    elif event.type == pygame.KEYUP:
            key_up(self, event)

    # user defined events
    elif event.type == EVENT_MOVE:
        user_event_move(self, event)
    elif event.type == EVENT_HEART_BEAT:
        self.change_and_send('heart_beat', [])

def quit(self, event):
    pygame.quit()
    reactor.stop()
    sys.exit()

def escape(self, event):

    # exit building
    if len(self.menu_stack) == 1:
        self.my_role.in_building_type = None

    # pop menu_stack
    if len(self.menu_stack) > 0:
        menu_to_kill = self.menu_stack.pop()
        self.selection_list_stack.pop()
        menu_to_kill.kill()
    print(len(self.menu_stack))
    print('escape pressed!')

    # clear buttons_in_windows dict
    self.buttons_in_windows.clear()
    print('buttons_in_windows dict cleared!')

    # deactivate text entry
    self.text_entry_active = False

def init_key_mappings(self):
    """cmds that change local state and sent to server"""
    self.key_mappings = {
        # battle
        'b': ['try_to_fight_with', ['b']],
        'e': ['exit_battle', []],
        'k': ['shoot_ship', [0, 0]],
    }

def other_keys_down(self, event):
    # change and send keys
    if chr(event.key) in self.key_mappings:
        cmd = self.key_mappings[chr(event.key)][0]
        params = self.key_mappings[chr(event.key)][1]
        self.change_and_send(cmd, params)

    # start move
    if event.key == ord('d'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'right'])
    elif event.key == ord('a'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'left'])
    elif event.key == ord('w'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'up'])
    elif event.key == ord('s'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'down'])

    # logins
    if chr(event.key).isdigit():
        self.connection.send('login', [chr(event.key), chr(event.key)])

    # change map
    if event.key == ord('n'):
        if self.my_role.map != 'sea':
            self.change_and_send('change_map', ['sea'])
    elif event.key == ord('m'):
        if self.my_role.map != 'port':
            self.change_and_send('change_map', ['port'])

    # enter building
    if event.key == ord('z'):
        self.button_click_handler.menu_click_handler.cmds.enter_building()

    # auto move
    if event.key == ord('o'):
        print('auto moving!')

        self.timer = task.LoopingCall(move_right_and_then_back, self)
        self.timer.start(5)
    # stop timer
    elif event.key == ord('p'):
        self.timer.stop()


def move_right_and_then_back(self):
    self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'right'])
    reactor.callLater(2, send_stop_moving, self)
    reactor.callLater(2.5, start_moving_left, self)
    reactor.callLater(4.5, send_stop_moving, self)
    # start_moving(self, 'right')
    # reactor.callLater(2, stop_moving, self)
    # reactor.callLater(2.5, start_moving, self, 'left')
    # reactor.callLater(4.5, stop_moving, self)

def send_stop_moving(self):
    self.change_and_send('stop_move', [self.my_role.x, self.my_role.y])

def start_moving_left(self):
    self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'left'])

def key_up(self, event):
    key = chr(event.key)

    # stop moving
    if key in ['w', 's', 'a', 'd']:
        try:
            self.change_and_send('stop_move', [self.my_role.x, self.my_role.y])
        except:
            pass

def user_event_move(self, event):
    if self.my_role:
        if self.move_direction == 1:
            self.change_and_send('move', ['right'])
        else:
            self.change_and_send('move', ['left'])

        self.move_count += 1

        if self.move_count >= 15:
            self.move_count = 0
            self.move_direction *= -1