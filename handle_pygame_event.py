import pygame
from twisted.internet import reactor, task
import constants as c
import sys
from hashes.hash_ports_meta_data import hash_ports_meta_data

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
        if self.my_role:
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
        # to sea
        if self.my_role.map != 'sea':
            # make sea image
            port_tile_x = hash_ports_meta_data[int(self.my_role.map) + 1]['x']
            port_tile_y = hash_ports_meta_data[int(self.my_role.map) + 1]['y']
            print(port_tile_x, port_tile_y)

            self.images['sea'] = self.map_maker.make_partial_world_map(port_tile_x, port_tile_y)

            # send
            self.connection.send('change_map', ['sea'])


            # init timer at sea

                # max days at sea (local game variable, not in role)
            self.max_days_at_sea = self.my_role.calculate_max_days_at_sea()
            self.days_spent_at_sea = 0
                # timer
            self.timer_at_sea = task.LoopingCall(pass_one_day_at_sea, self)
            self.timer_at_sea.start(c.ONE_DAY_AT_SEA_IN_SECONDS)

    elif event.key == ord('m'):
        # to port
        if not self.my_role.map.isdigit():
            port_id = get_nearby_port_index(self)
            if port_id:
                self.connection.send('change_map', [str(port_id)])
                self.timer_at_sea.stop()

    # enter building
    if event.key == ord('z'):
        self.button_click_handler.menu_click_handler.cmds.enter_building()

    # developer keys
    if c.DEVELOPER_MODE_ON:

        # change and send keys
        if chr(event.key) in self.key_mappings:
            cmd = self.key_mappings[chr(event.key)][0]
            params = self.key_mappings[chr(event.key)][1]
            self.change_and_send(cmd, params)

        # auto move
        if event.key == ord('o'):
            print('auto moving!')

            self.timer = task.LoopingCall(move_right_and_then_back, self)
            self.timer.start(5)

        # stop timer
        elif event.key == ord('p'):
            self.timer.stop()

        # battle
        if event.key == ord('b'):
            self.connection.send('try_to_fight_with', ['b'])
        elif event.key == ord('e'):
            self.connection.send('exit_battle', [])
        elif event.key == ord('k'):
            self.change_and_send('shoot_ship', [0, 0])


def pass_one_day_at_sea(self):
    if self.my_role.map == 'sea':

        # pass peacefully
        if self.days_spent_at_sea <= self.max_days_at_sea:
            self.days_spent_at_sea += 1
            print(self.days_spent_at_sea)

        # starved!
        else:
            self.timer_at_sea.stop()
            self.change_and_send('change_map', ['29'])

def get_nearby_port_index(self):
    # get x and y in tile position
    x_tile = self.my_role.x / c.PIXELS_COVERED_EACH_MOVE
    y_tile = self.my_role.y / c.PIXELS_COVERED_EACH_MOVE

    # iterate each port
    for i in range(1,131):
        if abs(x_tile - hash_ports_meta_data[i]['x']) <= 2 \
                and abs(y_tile - hash_ports_meta_data[i]['y']) <= 2:
            port_id = i - 1
            return port_id

    return None

def move_right_and_then_back(self):
    self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'right'])
    reactor.callLater(2, send_stop_moving, self)
    reactor.callLater(2.5, start_moving_left, self)
    reactor.callLater(4.5, send_stop_moving, self)

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