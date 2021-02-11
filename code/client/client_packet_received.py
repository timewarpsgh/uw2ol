# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
from role import Role, Ship, Mate
from twisted.internet.task import LoopingCall
import port_npc
import handle_pygame_event
import constants as c

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


# register responses
def register_ok(self, message_obj):
    self.login_state_text = 'Register OK. Please Login.'
    print('register_ok')

def account_exists(self, message_obj):
    self.login_state_text = 'Account exists!'
    print('account_exists')

# make character response
def new_role_created(self, message_obj):
    self.login_state_text = 'Character created! Please login again.'

def name_exists(self, message_obj):
    self.login_state_text = 'Name used! Please choose another name.'

# login responses
def login_failed(self, message_obj):
    self.login_state_text = 'Login failed!'
    print('account_exists')

def no_role_yet(self, message_obj):
    self.login_state_text = "Login successful! Please create a character. Don't use a number as your name."

def your_role_data_and_others(self, message_obj):
    # my role
    print("got my role data")
    my_role = message_obj[0]
    self.my_role = my_role
    print("my role's x y:", my_role.x, my_role.y, my_role.map, my_role.name)

    if my_role.map.isdigit():
        port_index = int(my_role.map)
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

    # escape
    # handle_pygame_event.escape(self, '')

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
        # if just lost from battle
        if not self.my_role.ships:
            self.connection.send('change_map', ['29'])

    # if in port
    elif self.my_role.map.isdigit():
        port_index = int(self.my_role.map)
        self.port_piddle, self.images['port'] = self.map_maker.make_port_piddle_and_map(port_index, self.time_of_day)

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
    roles_in_battle_map = message_obj
    self.other_roles = {}
    for name, role in roles_in_battle_map.items():
        if name == self.my_role.name:
            self.my_role = role
        else:
            self.other_roles[name] = role

        # set game and in client to role
        role.in_client = True

    # start battle timer
    self.battle_timer = LoopingCall(_check_battle_timer, self)
    self.battle_timer.start(1)

def _check_battle_timer(self):
    if self.my_role.map == 'sea':
        self.battle_timer.stop()
    else:
        if self.my_role.your_turn_in_battle:
            self.think_time_in_battle -= 1
            print(self.think_time_in_battle)
            if self.think_time_in_battle <= 0:
                self.change_and_send('all_ships_operate', [])
                self.think_time_in_battle = c.THINK_TIME_IN_BATTLE

def new_roles_from_battle(self, message_obj):
    new_roles_from_battle = message_obj
    for name, role in new_roles_from_battle.items():
        self.other_roles[name] = role


def target_too_far(self, message_obj):
    self.button_click_handler. \
        make_message_box("target too far!")

