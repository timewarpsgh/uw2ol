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
    """self is Echo Protocol"""
    # responses based on different types
    if pck_type == 'register':

        # get ac and psw
        account = message_obj[0]
        password = message_obj[1]

        # register ok?
        d = threads.deferToThread(self.factory.db.register, account, password)
        d.addCallback(self.on_register_got_result)

    elif pck_type == 'login':

        # get ac and psw
        account = message_obj[0]
        password = message_obj[1]

        # try to login
        d = threads.deferToThread(self.factory.db.login, account, password)
        d.addCallback(self.on_login_got_result)

    elif pck_type == 'create_new_role':
        name = message_obj[0]
        account = self.account

        d = threads.deferToThread(self.factory.db.create_character, account, name)
        d.addCallback(self.on_create_character_got_result)

    elif pck_type == 'change_map':
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

    elif pck_type == 'try_to_fight_with':
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

    elif pck_type == 'exit_battle':
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

    elif pck_type in Role.__dict__:
        """ commands that change my role's state are broadcast to other clients in same map """
        # server changes role state
        func_name = pck_type
        func = getattr(self.my_role, func_name)
        func(message_obj)

        # send to other clients
        params_list = message_obj
        params_list.append(self.my_role.name)
        self.send_to_other_clients(func_name, params_list)