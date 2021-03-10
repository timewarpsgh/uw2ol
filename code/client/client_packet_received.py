import pygame

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
from role import Role, Ship, Mate, Port
from twisted.internet.task import LoopingCall
import port_npc
import handle_pygame_event
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data

def process_packet(self, pck_type, message_obj):
    # method not in role (in this file)
    if pck_type not in Role.__dict__:
        func_name = eval(pck_type)
        func_name(self, message_obj)

    # sync packets
    elif pck_type in Role.__dict__:
        list = message_obj
        name = list.pop()
        func_name = pck_type
        if name in self.other_roles:
            role = self.other_roles[name]
            print("trying", func_name, list, "for", name)
            func = getattr(role, func_name)
            func(list)
            print(role, func_name, func, list)

# register responses
def register_ok(self, message_obj):
    self.login_state_text = 'Register OK. Please Login.'
    print('register_ok')

def account_exists(self, message_obj):
    self.login_state_text = 'Account exists!'
    print('account_exists')

# make character response
def must_login_first(self, message_obj):
    self.login_state_text = "Must login first to create character."

def new_role_created(self, message_obj):
    self.login_state_text = 'Character created! Please login again.'

def name_exists(self, message_obj):
    self.login_state_text = 'Name used! Please choose another name.'

# login responses
def login_failed(self, message_obj):
    self.login_state_text = 'Login failed!'
    print('account_exists')

def no_role_yet(self, message_obj):
    self.login_state_text = "Login successful! " \
                            "Please create a character. " \
                            "Don't use a number as your name."

def your_role_data_and_others(self, message_obj):
    # my role
    print("got my role data")
    my_role = message_obj[0]
    self.my_role = my_role
    print("my role's x y:", my_role.x, my_role.y, my_role.map, my_role.name)

    if my_role.map.isdigit():
        port_index = int(my_role.map)
        my_role.prev_port_map_id = port_index
        self.port_piddle, self.images['port'] = self.map_maker.make_port_piddle_and_map(port_index, self.time_of_day)

        # normal ports
        if port_index < 100:
            port_npc.init_static_npcs(self, port_index)
            port_npc.init_dynamic_npcs(self, port_index)

    # other roles
    other_roles = message_obj[1]
    for role in other_roles:
        self.other_roles[role.name] = role
    print(other_roles)

    # music
    pygame.mixer.music.load('../../assets/sounds/music/port.ogg')
    pygame.mixer.music.play()

# someone logged in
def new_role(self, message_obj):
    new_role = message_obj
    self.other_roles[new_role.name] = new_role
    print("got new role named:", new_role.name)

# someone logged out
def logout(self, message_obj):
    name_of_logged_out_role = message_obj
    del self.other_roles[name_of_logged_out_role]

# someone changed map
def role_disappeared(self, message_obj):
    name_of_role_that_disappeared = message_obj
    if name_of_role_that_disappeared in self.other_roles:
        del self.other_roles[name_of_role_that_disappeared]

# change map response
def roles_in_new_map(self, message_obj):
    roles_in_new_map = message_obj
    self.my_role = roles_in_new_map[self.my_role.name]
    del roles_in_new_map[self.my_role.name]
    self.other_roles = roles_in_new_map

    print("now my map:", self.my_role.map)

    # if at sea
    if self.my_role.map == 'sea':
        # clear marks
        self.my_role._clear_marks()
        self.reset_think_time_in_battle()

        # music
        pygame.mixer.music.load('../../assets/sounds/music/sea.ogg')
        pygame.mixer.music.play(-1)

        # if just lost from battle
        if not self.my_role.ships:
            self.connection.send('change_map', ['29'])
            self.button_click_handler.show_defeat_window()

    # if in port
    elif self.my_role.map.isdigit():
        port_index = int(self.my_role.map)
        self.port_piddle, self.images['port'] = self.map_maker.\
            make_port_piddle_and_map(port_index, self.time_of_day)

def roles_disappeared(self, message_obj):
    """in delete grids"""
    names_of_roles_that_disappeared = message_obj
    for name in names_of_roles_that_disappeared:
        if name in self.other_roles:
            del self.other_roles[name]

def roles_appeared(self, message_obj):
    """in new grids"""
    roles_appeared = message_obj
    self.other_roles = {**self.other_roles, **roles_appeared}


# enter battle responses
def roles_in_battle_map(self, message_obj):
    """in battle now"""
    # get roles
    roles_in_battle_map = message_obj
    self.other_roles = {}
    for name, role in roles_in_battle_map.items():
        if name == self.my_role.name:
            self.my_role = role
        else:
            self.other_roles[name] = role

    # start battle timer
    self.battle_timer = LoopingCall(_check_battle_timer, self)
    self.battle_timer.start(1)

    # music
    pygame.mixer.music.load('../../assets/sounds/music/battle.ogg')
    pygame.mixer.music.play(-1)

def _check_battle_timer(self):
    if self.my_role.map == 'sea' and self.battle_timer:
        self.battle_timer.stop()
    else:
        if self.my_role.your_turn_in_battle:
            # show marks at the beginning of my turn
            if self.think_time_in_battle == c.THINK_TIME_IN_BATTLE:
                self.my_role._show_marks()

            # auto operate when timer <= 0
            self.think_time_in_battle -= 1
            if self.think_time_in_battle <= 0:
                self.change_and_send('all_ships_operate', [False])

def new_roles_from_battle(self, message_obj):
    new_roles_from_battle = message_obj
    for name, role in new_roles_from_battle.items():
        self.other_roles[name] = role

def target_too_far(self, message_obj):
    msg = "target too far or lv too low!"
    self.button_click_handler.i_speak(msg)

def npc_info(self, message_obj):
    """npc fleet positions"""
    dic = message_obj

    # get 3 lists
    names = []
    destinations = []
    positions = []
    cargoes = []
    for name in dic.keys():
        names.append(dic[name]['mate_name'])
        destinations.append(dic[name]['destination'])
        positions.append(dic[name]['position'])
        cargoes.append(dic[name]['cargo_name'])

    # calc longitude and latitude
    for pos in positions:
        x = int(pos[0] / c.PIXELS_COVERED_EACH_MOVE)
        y = int(pos[1] / c.PIXELS_COVERED_EACH_MOVE)
        longitude, latitude = _calc_longitude_and_latitude(x, y)
        pos[0] = longitude
        pos[1] = latitude

    # maid speak
    speak_str = f"{names[0]}'s fleet, carrying {cargoes[0]}, is heading to {destinations[0]} " \
                f"and his current location is about {positions[0][0]} {positions[0][1]}. <br><br>" \
                f"{names[1]}'s fleet, carrying {cargoes[1]}, is heading to {destinations[1]} " \
                f"and his current location is about {positions[1][0]} {positions[1][1]}."
    self.button_click_handler.menu_click_handler.port.bar._maid_speak(speak_str)

def _calc_longitude_and_latitude(x, y):
    # transform to longitude
    longitude = None
    if x >= 900 and x <= 1980:
        longitude = int(( x - 900 )/6)
        longitude = str(longitude) + 'e'
    elif x > 1980:
        longitude = int((900 + 2160 - x)/6)
        longitude = str(longitude) + 'w'
    else:
        longitude = int((900 - x)/6)
        longitude = str(longitude) + 'w'

    # transform to latitude
    latitude = None
    if y <= 640:
        latitude = int((640 - y)/7.2)
        latitude = str(latitude) + 'N'
    else:
        latitude = int((y - 640)/7.2)
        latitude = str(latitude) + 'S'

    return (longitude, latitude)

def allied_ports_and_pi(self, message_obj):
    d = message_obj

    # make my_dict (economy_id: set of dic)
    my_dict = {}
    for map_id, list in d.items():
        port = Port(map_id)
        economy_id = port.economy_id

        pi = list[0]
        economy = list[1]
        industry = list[2]

        port_name = port.name

        if economy_id in my_dict:
            pass
        else:
            my_dict[economy_id] = []
        dic = {
            'port_name': port_name,
            'pi': pi,
            'economy': economy,
            'industry': industry,
        }
        my_dict[economy_id].append(dic)

    # dic to show
    dic = {}
    for k in sorted(my_dict):
        region_name = hash_ports_meta_data['markets'][k]
        dic[region_name] = [_show_allied_ports_for_one_economy_id, [self, region_name, my_dict[k]]]

    self.button_click_handler.make_menu(dic)

def _show_allied_ports_for_one_economy_id(params):
    self = params[0]
    region_name = params[1]
    list_of_dict = params[2]
    port_count = len(list_of_dict)

    msg = f"In {region_name}, the number of ports allied to us is {port_count}. <br><br>"
    for d in list_of_dict:
        msg += f"{d['port_name']}: PI-{d['pi']}, " \
               f"E-{d['economy']}, " \
               f"I-{d['industry']}<br>"

    self.button_click_handler.make_message_box(msg)
