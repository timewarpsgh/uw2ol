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

    # move
    if event.key == ord('d'):
        start_moving(self, 'right')
    elif event.key == ord('a'):
        start_moving(self, 'left')
    elif event.key == ord('w'):
        start_moving(self, 'up')
    elif event.key == ord('s'):
        start_moving(self, 'down')

    # start move
    if event.key == ord('h'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'right'])
    elif event.key == ord('f'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'left'])
    elif event.key == ord('t'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'up'])
    elif event.key == ord('g'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'down'])


    # logins
    if chr(event.key).isdigit():
        self.connection.send('login', [chr(event.key), chr(event.key)])

    # change map
    if event.key == ord('n'):
        self.change_and_send('change_map', ['sea'])
    elif event.key == ord('m'):
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
    reactor.callLater(2, self.change_and_send, 'stop_move', [])
    reactor.callLater(2.5, start_moving_left, self)
    reactor.callLater(4.5, self.change_and_send, 'stop_move', [])
    # start_moving(self, 'right')
    # reactor.callLater(2, stop_moving, self)
    # reactor.callLater(2.5, start_moving, self, 'left')
    # reactor.callLater(4.5, stop_moving, self)

def start_moving_left(self):
    self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'left'])

def can_move(self, direction):
    # get piddle
    piddle = self.port_piddle

    # perl piddle and python numpy(2d array) are different
    y = int(self.my_role.x/16)
    x = int(self.my_role.y/16)

    # directions
    if direction == 'up':
        if piddle[x, y] in c.WALKABLE_TILES and piddle[x, y + 1] in c.WALKABLE_TILES:
            return True
    elif direction == 'down':
        if piddle[x + 2, y] in c.WALKABLE_TILES and piddle[x + 2, y + 1] in c.WALKABLE_TILES:
            return True
    elif direction == 'left':
        if piddle[x + 1, y - 1] in c.WALKABLE_TILES :
            return True
    elif direction == 'right':
        if piddle[x + 1, y + 2] in c.WALKABLE_TILES :
            return True

    return False

def start_moving(self, direction):
    if not self.movement:
        self.movement = task.LoopingCall(try_to_move,self, direction)
        loopDeferred = self.movement.start(c.MOVE_TIME_INVERVAL)

def try_to_move(self, direction):
    if can_move(self, direction):
        self.change_and_send('move', [direction])

def key_up(self, event):
    key = chr(event.key)

    # stop moving
    if key == 'w' or key == 's' or key == 'a' or key == 'd':
        try:
            stop_moving(self)
        except:
            pass

    if key == 'h' or key == 'f' or key == 't' or key == 'g':
        try:
            self.change_and_send('stop_move', [self.my_role.x, self.my_role.y])
        except:
            pass

def stop_moving(self):
    self.movement.stop()
    self.movement = None

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