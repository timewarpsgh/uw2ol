import pygame
from twisted.internet import reactor, task


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
        # move
        'w': ['move', ['up']],
        's': ['move', ['down']],
        'a': ['move', ['left']],
        'd': ['move', ['right']],

        # change map
        'n': ['change_map', ['sea']],
        'm': ['change_map', ['port']],

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

    # read keys
    if event.key == ord('h'):
        start_moving(self, 'right')
    elif event.key == ord('f'):
        start_moving(self, 'left')
    elif event.key == ord('t'):
        start_moving(self, 'up')
    elif event.key == ord('g'):
        start_moving(self, 'down')


        # self.change_and_send('move', ['right'])

        # print(self.my_role.name)

    # send keys
    if event.key == ord('1'):
        self.connection.send('login', ['1', '1'])
    elif event.key == ord('2'):
        self.connection.send('login', ['2', '2'])
    elif event.key == ord('3'):
        self.connection.send('login', ['3', '3'])
    elif event.key == ord('4'):
        self.connection.send('login', ['4', '4'])
    elif event.key == ord('5'):
        self.connection.send('login', ['5', '5'])

def start_moving(self, direction):
    if self.movement:
        self.movement.stop()
        self.movement = None

    self.movement = task.LoopingCall(self.change_and_send, 'move', [direction])
    loopDeferred = self.movement.start(0.1)

def key_up(self, event):
    key = chr(event.key)
    if key == 'h' or key == 'f' or key == 't' or key == 'g':
        # stop moving
        try:
            self.movement.stop()
            self.movement = None
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