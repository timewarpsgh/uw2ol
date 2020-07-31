from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, threads, defer

from protocol import MyProtocol
from DBmanager import Database
from role import Role
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data
import server_packet_received


import os
import sys


def process_packet(self, pck_type, message_obj):
    """ self is Echo Protocol
        responses based on different packet types
    """
    # method not in role (in this file)
    if pck_type not in Role.__dict__:
        func_name = eval(pck_type)
        func_name(self, message_obj)

    # method in role (commands that change my role's state are broadcast to other clients in same map)
    elif pck_type in Role.__dict__:
        # server changes role state
        func_name = pck_type
        func = getattr(self.my_role, func_name)
        func(message_obj)

        # send to other clients
        params_list = message_obj
        params_list.append(self.my_role.name)
        self.send_to_other_clients(func_name, params_list)

####################### packet types ###########################
def register(self, message_obj):
    # get ac and psw
    account = message_obj[0]
    password = message_obj[1]

    # register ok?
    d = threads.deferToThread(self.factory.db.register, account, password)
    d.addCallback(self.on_register_got_result)

def create_new_role(self, message_obj):
    name = message_obj[0]
    account = self.account

    d = threads.deferToThread(self.factory.db.create_character, account, name)
    d.addCallback(self.on_create_character_got_result)

def login(self, message_obj):
    # get ac and psw
    account = message_obj[0]
    password = message_obj[1]

    # try to login
    d = threads.deferToThread(self.factory.db.login, account, password)
    d.addCallback(self.on_login_got_result)

def change_map(self, message_obj):
    # get now_map and target_map
    now_map = self.my_role.map
    target_map = message_obj[0]

    # change my map and position
    self.my_role.map = target_map

    print("map changed to:", self.my_role.map)

    # to sea
    if target_map == 'sea':
        self.my_role.x = hash_ports_meta_data[int(now_map) + 1]['x'] * c.PIXELS_COVERED_EACH_MOVE
        self.my_role.y = hash_ports_meta_data[int(now_map) + 1]['y'] * c.PIXELS_COVERED_EACH_MOVE
        # to port
    elif target_map.isdigit():
        self.my_role.x = hash_ports_meta_data[int(target_map) + 1]['buildings'][4]['x'] * c.PIXELS_COVERED_EACH_MOVE
        self.my_role.y = hash_ports_meta_data[int(target_map) + 1]['buildings'][4]['y'] * c.PIXELS_COVERED_EACH_MOVE

        print("changed to", self.my_role.x, self.my_role.y)

    # change users() state
    del self.factory.users[now_map][self.my_role.name]
    self.factory.users[target_map][self.my_role.name] = self

    # send roles_in_new_map to my client
    roles_in_new_map = {}
    for name, conn in self.factory.users[target_map].items():
        roles_in_new_map[name] = conn.my_role

    self.send('roles_in_new_map', roles_in_new_map)

    # send disappear message to other roles in my previous map
    for name, conn in self.factory.users[now_map].items():
        conn.send('role_disappeared', self.my_role.name)

    # send new_role to other roles in my current map
    for name, conn in self.factory.users[target_map].items():
        if name != self.my_role.name:
            conn.send('new_role', self.my_role)

def try_to_fight_with(self, message_obj):
    # gets
    enemy_name = message_obj[0]
    enemy_conn = self.factory.users[self.my_role.map][enemy_name]
    enemy_role = enemy_conn.my_role
    my_role = self.my_role

    # sets
    my_role.enemy_name = enemy_name
    enemy_role.enemy_name = my_role.name

    # can fight
    if abs(enemy_role.x - my_role.x) <= 50 and abs(enemy_role.y - my_role.y) <= 50:
        '''both enter battle map'''
        print('can go battle!')

        # store my previous map
        my_previous_map = self.my_role.map

        # change my map and enemy map
        my_name = self.my_role.name
        battle_map_name = 'battle_' + my_name
        self.my_role.map = battle_map_name
        enemy_role.map = battle_map_name

        self.my_role.your_turn_in_battle = True
        enemy_role.your_turn_in_battle = False

        # change users dict state
        del self.factory.users[my_previous_map][my_name]
        del self.factory.users[my_previous_map][enemy_role.name]

        self.factory.users[battle_map_name] = {}
        self.factory.users[battle_map_name][my_name] = self
        self.factory.users[battle_map_name][enemy_role.name] = enemy_conn

        # send roles_in_new_map to my client and enemy client
        roles_in_new_map = {}
        for name, conn in self.factory.users[battle_map_name].items():
            roles_in_new_map[name] = conn.my_role

        # init all ships positions in battle
        for role in roles_in_new_map.values():
            # my role
            if role.name == my_name:
                y_index = 1
                for ship in role.ships:
                    ship.x = 1
                    ship.y = y_index
                    ship.direction = role.direction
                    y_index += 1
            # enemy role
            else:
                y_index = 1
                for ship in role.ships:
                    ship.x = 6
                    ship.y = y_index
                    ship.direction = role.direction
                    y_index += 1

        self.send('roles_in_battle_map', roles_in_new_map)
        enemy_conn.send('roles_in_battle_map', roles_in_new_map)

        # send disappear message to other roles in my previous map
        names_of_roles_that_disappeared = []
        names_of_roles_that_disappeared.append(self.my_role.name)
        names_of_roles_that_disappeared.append(enemy_role.name)

        for name, conn in self.factory.users[my_previous_map].items():
            conn.send('roles_disappeared', names_of_roles_that_disappeared)

    # can't
    else:
        self.send('target_too_far')

def exit_battle(self, message_obj):
    # if no loser

    # gets
    enemy_name = self.my_role.enemy_name
    enemy_conn = self.factory.users[self.my_role.map][enemy_name]
    enemy_role = enemy_conn.my_role
    my_role = self.my_role
    my_previous_map = self.my_role.map

    # sets
    my_role.map = 'sea'
    enemy_role.map = 'sea'

    # change users dict state
    del self.factory.users[my_previous_map]
    print(self.factory.users)

    self.factory.users['sea'][my_role.name] = self
    self.factory.users['sea'][enemy_role.name] = enemy_conn

    # send roles_in_new_map to my client and enemy client
    roles_in_new_map = {}
    for name, conn in self.factory.users['sea'].items():
        roles_in_new_map[name] = conn.my_role

    self.send('roles_in_new_map', roles_in_new_map)
    enemy_conn.send('roles_in_new_map', roles_in_new_map)

    # send new role message to other roles in new map
    new_roles_from_battle = {}
    new_roles_from_battle[self.my_role.name] = self.my_role
    new_roles_from_battle[enemy_role.name] = enemy_role

    for name, conn in self.factory.users['sea'].items():
        if name != enemy_name and name != self.my_role.name:
            conn.send('new_roles_from_battle', new_roles_from_battle)

    # if someone lost

####################### call backs ###########################
def on_create_character_got_result(self, is_ok):
    if is_ok:
        self.send('new_role_created')
    else:
        self.send('name_exists')

def on_register_got_result(self, is_ok):
    if is_ok:
        print('register success!')
        self.send('register_ok')
    else:
        print("account exists!")
        self.send('account_exists')

def on_login_got_result(self, account):
    # ok
    if account:
        print('login success!', account)
        self.account = account
        d = threads.deferToThread(self.factory.db.get_character_data, account)
        d.addCallback(self.on_get_character_data_got_result)

    # not ok
    else:
        print("login failed!")
        self.send('login_failed')

def on_get_character_data_got_result(self, role):
    # ok
    if role != False:
        # store role here and in users
        self.my_role = role
        self.factory.users[role.map][role.name] = self
        Role.users = self.factory.users

        # tell other clients in same map of new role
        for name, conn in self.factory.users[role.map].items():
            if name != role.name:
                conn.send('new_role', role)

        # send to client other_roles
        other_roles = []
        for name, conn in self.factory.users[role.map].items():
            if name != role.name:
                other_roles.append(conn.my_role)

        self.send('your_role_data_and_others', [role, other_roles])

    # not ok
    else:
        self.send('no_role_yet')