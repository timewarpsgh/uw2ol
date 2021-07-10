import pygame
from twisted.internet import reactor, task
import random

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data
import gui
from pygame_gui._constants import UI_WINDOW_CLOSE
from port_npc import Dog, OldMan, Agent, Man, Woman
import port_npc
import tkinter as tk

EVENT_MOVE = pygame.USEREVENT + 1
EVENT_HEART_BEAT = pygame.USEREVENT + 2

def handle_pygame_event(self, event):
    """argument self is game"""
    # quit
    if event.type == pygame.QUIT:
        quit(self, event)
    # key down
    elif event.type == pygame.KEYDOWN:
        key_down(self, event)
    # key up
    elif event.type == pygame.KEYUP:
        key_up(self, event)
    # mouse button down
    elif event.type == pygame.MOUSEBUTTONDOWN:
        mouse_button_down(self, event)
    # user defined events
    user_defined_events(self, event)

def key_down(self, event):
    # return (focus text entry)
    if event.key > 256:
        return

    if event.key == pygame.K_RETURN:
        msg = self.text_entry.get()
        if msg:
            self.change_and_send('speak', [msg])
            self.text_entry.delete(0, "end")
            self.embed.focus()
            self.text_entry_active = False
        else:
            self.text_entry.focus()
            self.text_entry_active = True

    # escape
    if event.key == pygame.K_ESCAPE:
        escape(self, event)
    # other keys
    if not self.text_entry_active:
        # in game
        if self.my_role:
            other_keys_down(self, event)
        # not in game
        else:
            # logins
            if chr(event.key).isdigit():
                self.connection.send('login', [chr(event.key), chr(event.key)])

def mouse_button_down(self, event):
    if self.my_role:
        # left button
        if event.button == 1:
            # in battle
            if self.my_role.is_in_battle():
                for s in self.mark_sprites:
                    if s.rect.collidepoint(event.pos):
                        s.clicked()
            # not in battle
            else:
                if self.other_roles_rects:
                    # set target
                    for name, rect in self.other_roles_rects.items():
                        if rect.collidepoint(event.pos):
                            self.my_role.enemy_name = name
                            print('target set to:', name)
                            break

                if self.my_role_rect.collidepoint(event.pos):
                    self.my_role.enemy_name = None

        # right button
        elif event.button == 3:
            if self.other_roles_rects:
                # set target
                for name, rect in self.other_roles_rects.items():
                    if rect.collidepoint(event.pos):
                        self.my_role.enemy_name = name
                        print('target set to:', name)
                        gui.target_clicked(self)
                        return

def user_defined_events(self, event):
    if event.type == EVENT_MOVE:
        user_event_move(self, event)
    elif event.type == EVENT_HEART_BEAT:
        self.change_and_send('heart_beat', [])
    # ui window close event
    elif event.type == pygame.USEREVENT:
        if event.user_type == UI_WINDOW_CLOSE:
            if self.menu_stack:
                self.menu_stack.pop()
                self.selection_list_stack.pop()
                print('event ui window close!')
                print('stack length:', len(self.menu_stack))

                if self.my_role:
                    # not in building
                    if self.my_role.in_building_type == None:
                        pass
                    # in building
                    elif len(self.menu_stack) == 0:
                        self.my_role.in_building_type = None
                else:
                    self.active_input_boxes.clear()
                    pass


def quit(self, *event):
    # when in game
    if self.my_role:
        if self.my_role.map.isdigit():
            reactor.stop()
            self.root.quit()
            pygame.quit()
            sys.exit()
        else:
            self.button_click_handler. \
                make_message_box('Exit while in port please.')
            print('Exit while in port please.')
    # when not in game
    else:
        self.root.quit()
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
        menu_to_kill = self.menu_stack[-1]
        menu_to_kill.kill()
    print('escape pressed!')

    # clear buttons_in_windows dict
    self.buttons_in_windows.clear()
    print('buttons_in_windows dict cleared!')

    # deactivate text entry
    self.text_entry_active = False

    # clear input boxes
    self.active_input_boxes.clear()

def other_keys_down(self, event):
    # not in battle
    if not self.my_role.is_in_battle():
        _not_in_battle_keys(self, event)
    # in battle
    else:
        _in_battle_keys(self, event)
    # developer keys
    if c.DEVELOPER_MODE_ON:
        pass

def _not_in_battle_keys(self, event):
    # start move
    if event.key == ord('d'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'right'])
    elif event.key == ord('a'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'left'])
    elif event.key == ord('w'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'up'])
    elif event.key == ord('s'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'down'])

    elif event.key == ord('e'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'ne'])
    elif event.key == ord('q'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'nw'])
    elif event.key == ord('z'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'sw'])
    elif event.key == ord('x'):
        self.change_and_send('start_move', [self.my_role.x, self.my_role.y, 'se'])

    # change map to sea
    if event.key == ord('n'):
        if c.DEVELOPER_MODE_ON:
            self.button_click_handler.menu_click_handler.port.port._sail_ok()

    # change map to port
    elif event.key == ord('m'):
        __change_map_to_port(self)

    # enter building
    if event.key == ord('f'):
        self.button_click_handler.menu_click_handler.cmds.enter_building()

    # go ashore
    if event.key == ord('g'):
        self.button_click_handler.menu_click_handler.cmds.go_ashore()

    # enter battle
    if event.key == ord('b'):
        if self.my_role.enemy_name:
            # get my_role and enemy_role
            enemy_role = self.my_role._get_other_role_by_name(self.my_role.enemy_name)
            my_role = self.my_role

            # if escorted, set enemy to escort
            if enemy_role.escorted_by:
                escort_name = enemy_role.escorted_by
                escort_role = self.my_role._get_other_role_by_name(escort_name)
                if my_role.is_target_role_in_battle_distance(escort_role):
                    enemy_role = escort_role

            # try to fight with enemy
            if my_role.is_target_role_in_battle_distance(enemy_role):
                if enemy_role.mates[0].nation == my_role.mates[0].nation and not c.DEVELOPER_MODE_ON:
                    self.button_click_handler.i_speak("That fleet is from my own country.")
                else:
                    self.connection.send('try_to_fight_with', [enemy_role.name])
            else:
                msg = "Target too far!"
                msg = self.trans(msg)
                self.button_click_handler. \
                    make_message_box(msg)

    # change language
    if event.key == ord('l'):
        if self.translator.to_langguage == 'EN':
            self.button_click_handler.menu_click_handler.options._set_to_chinese()
        else:
            self.button_click_handler.menu_click_handler.options._set_to_english()

def __change_map_to_port(self):
    if not self.my_role.map.isdigit():
        port_id = get_nearby_port_index(self)
        if port_id or port_id == 0:
            self.connection.send('change_map', [str(port_id), self.days_spent_at_sea])
            self.timer_at_sea.stop()

            # make npcs
            if port_id < 100:
                self.time_of_day = random.choice(c.TIME_OF_DAY_OPTIONS)

                if self.time_of_day == 'night':
                    self.dog = None
                    self.old_man = None
                    self.agent = None

                    self.man = None
                    self.woman = None
                else:
                    port_npc.init_static_npcs(self, port_id)
                    port_npc.init_dynamic_npcs(self, port_id)

            # don't make
            else:
                self.dog = None
                self.old_man = None
                self.agent = None

                self.man = None
                self.woman = None

            # music
            port_name = hash_ports_meta_data[port_id + 1]['name']
            economy_id = hash_ports_meta_data[port_id + 1]['economyId']
            region_name = hash_ports_meta_data['markets'][economy_id]

            if port_name in ["Lisbon", "Seville", "London", "Marseille", "Amsterdam", "Venice"]:
                pygame.mixer.music.load('../../assets/sounds/music/port/' + port_name + '.mp3')
            else:
                if region_name in ['North Africa','East Africa','West Africa']:
                    pygame.mixer.music.load('../../assets/sounds/music/port/African Town.mp3')
                elif region_name in ['Middle East','Ottoman Empire']:
                    pygame.mixer.music.load('../../assets/sounds/music/port/Middle Eastern Town.mp3')
                elif region_name == 'Northern Europe':
                    pygame.mixer.music.load('../../assets/sounds/music/port/Northern Europe Town.mp3')
                elif region_name == 'The Mediterranean' or region_name == 'Iberia':
                    pygame.mixer.music.load('../../assets/sounds/music/port/Southern Europe Town.mp3')
                elif region_name == 'Central America':
                    pygame.mixer.music.load('../../assets/sounds/music/port/Central America Town.mp3')    
                elif region_name == 'South America':
                    pygame.mixer.music.load('../../assets/sounds/music/port/South America Town.mp3')
                elif region_name in ['India']:
                    pygame.mixer.music.load('../../assets/sounds/music/port/Indian Town.mp3')
                elif region_name in ['Southeast Asia']:
                    pygame.mixer.music.load('../../assets/sounds/music/port/Southeast Asian Town.ogg')
                elif port_id == 94 or port_id == 95 or port_id == 97:
                    pygame.mixer.music.load('../../assets/sounds/music/port/China Town.mp3')
                elif port_id == 98 or port_id == 99:
                    pygame.mixer.music.load('../../assets/sounds/music/port/Japan Town.mp3')
                elif port_id == 119:
                    pygame.mixer.music.load('../../assets/sounds/music/port/Oceania Town.mp3')
                else:
                    pygame.mixer.music.load('../../assets/sounds/music/port.ogg')
            pygame.mixer.music.play()

def _in_battle_keys(self, event):
    if event.key == ord('b'):
        self.button_click_handler.menu_click_handler.battle.escape_battle()
    elif event.key == ord('k'):
        self.button_click_handler.menu_click_handler.battle.all_ships_move()
    elif event.key == ord('l'):
        self.change_and_send('set_all_ships_target', [0])
    elif event.key == ord('o'):
        self.change_and_send('set_all_ships_attack_method', [0])
    elif event.key == ord('i'):
        self.change_and_send('set_all_ships_attack_method', [1])

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
    if event.key > 256:
        return
    if not self.text_entry_active:
        key = chr(event.key)
        # stop moving
        if key in ['w', 's', 'a', 'd', 'e', 'q', 'z', 'x']:
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