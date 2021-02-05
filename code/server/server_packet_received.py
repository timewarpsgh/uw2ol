from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, threads, defer

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
from protocol import MyProtocol
from DBmanager import Database
from role import Role
import role
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data
import server_packet_received


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

def grid_change(self, messgage_obj):
    new_grid_id = messgage_obj[0]
    direction = messgage_obj[1]

    # change my grid
    map_id = int(self.my_role.map)
    port_map = self.factory.aoi_manager.get_port_map_by_id(map_id)
    port_map.move_player_conn_to_new_grid(self, new_grid_id)

    # get new and delete grids
    new_grids, delete_grids = port_map.get_new_and_delete_grids_after_movement(new_grid_id, direction)

    # for me

        # tell client new roles in new grids
    roles_appeared = {}
    for grid in new_grids:
        for name, conn in grid.roles.items():
            roles_appeared[name] = conn.my_role

    if roles_appeared:
        self.send('roles_appeared', roles_appeared)

        # disappeared roles in delete grids
    names_of_roles_that_disappeared = []
    for grid in delete_grids:
        for name, conn in grid.roles.items():
            names_of_roles_that_disappeared.append(name)

    if names_of_roles_that_disappeared:
        self.send('roles_disappeared', names_of_roles_that_disappeared)

    # for others

        # tell roles in delete grids someone disappeared
    for grid in delete_grids:
        for name, conn in grid.roles.items():
            conn.send('role_disappeared', self.my_role.name)

        # tell roles in new girds someone appeared
    for grid in new_grids:
        for name, conn in grid.roles.items():
            conn.send('new_role', self.my_role)

def change_map(self, message_obj):
    # get now_map and target_map
    now_map = self.my_role.map
    target_map = message_obj[0]

    # change my map and position
    self.my_role.map = target_map
    print("map changed to:", self.my_role.map)

    # to sea
    if target_map == 'sea':
        _change_map_to_sea(self, now_map)

    # to port
    elif target_map.isdigit():
        _change_map_to_port(self, target_map, message_obj)

    # change users() state
    del self.factory.users[now_map][self.my_role.name]
    self.factory.users[target_map][self.my_role.name] = self

    # send roles_in_new_map to my client
    roles_in_new_map = {}
    for name, conn in self.factory.users[target_map].items():
        if name == 'npcs':
            for npc_name, npc in self.factory.users[target_map][name].npcs.items():
                roles_in_new_map[npc_name] = npc
        else:
            roles_in_new_map[name] = conn.my_role

    self.send('roles_in_new_map', roles_in_new_map)

    # send disappear message to other roles in my previous map
    for name, conn in self.factory.users[now_map].items():
        if name == 'npcs':
            pass
        else:
            conn.send('role_disappeared', self.my_role.name)

    # send new_role to other roles in my current map
    for name, conn in self.factory.users[target_map].items():
        if name == 'npcs':
            pass
        elif name != self.my_role.name:
            conn.send('new_role', self.my_role)

def _change_map_to_sea(self, now_map):
    self.my_role.x = hash_ports_meta_data[int(now_map) + 1]['x'] * c.PIXELS_COVERED_EACH_MOVE
    self.my_role.y = hash_ports_meta_data[int(now_map) + 1]['y'] * c.PIXELS_COVERED_EACH_MOVE

    fleet_speed = self.my_role.get_fleet_speed([])
    self.my_role.set_speed([str(fleet_speed)])
    self.my_role.set_speed([str(40)])

def _change_map_to_port(self, target_map, message_obj):
    # if days at sea is sent as a param
    days_spent_at_sea = 0
    if len(message_obj) > 1:
        days_spent_at_sea = message_obj[1]

    # cost gold based on days at sea and crew count()
    if days_spent_at_sea > 0:
        total_crew = self.my_role._get_total_crew()
        total_cost = int(days_spent_at_sea * total_crew *
                         c.SUPPLY_CONSUMPTION_PER_PERSON * c.SUPPLY_UNIT_COST)
        self.my_role.gold -= total_cost

    # normal ports
    if int(target_map) <= 99:
        self.my_role.x = hash_ports_meta_data[int(target_map) + 1]['buildings'][4]['x'] * c.PIXELS_COVERED_EACH_MOVE
        self.my_role.y = hash_ports_meta_data[int(target_map) + 1]['buildings'][4]['y'] * c.PIXELS_COVERED_EACH_MOVE
        self.my_role.set_speed(['20'])
        print("changed to", self.my_role.x, self.my_role.y)

    # supply ports
    else:
        self.my_role.x = hash_ports_meta_data[101]['buildings'][4]['x'] * c.PIXELS_COVERED_EACH_MOVE
        self.my_role.y = hash_ports_meta_data[101]['buildings'][4]['y'] * c.PIXELS_COVERED_EACH_MOVE
        self.my_role.set_speed(['20'])

    # set additional days at sea to 0 (so that potions can be used again)
    self.my_role.additioanl_days_at_sea = 0

def try_to_fight_with(self, message_obj):
    """enter battle with someone"""
    # if target is player
    if message_obj[0] in self.factory.users[self.my_role.map]:
        _try_to_fight_with_player(self, message_obj)
    # if target is npc
    else:
        _try_to_fight_with_npc(self, message_obj)

def _try_to_fight_with_player(self, message_obj):
    # gets
    enemy_name = message_obj[0]
    enemy_conn = self.factory.users[self.my_role.map][enemy_name]
    enemy_role = enemy_conn.my_role
    my_role = self.my_role

    # sets
    my_role.enemy_name = enemy_name
    enemy_role.enemy_name = my_role.name

    # can fight
    if 1:
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
            if name == 'npcs':
                pass
            else:
                conn.send('roles_disappeared', names_of_roles_that_disappeared)

    # can't
    else:
        self.send('target_too_far')

def _try_to_fight_with_npc(self, message_obj):
    # gets
    enemy_name = message_obj[0]
    enemy_role = self.factory.users[self.my_role.map]['npcs'].npcs[enemy_name]
    # enemy_conn = self.factory.users[self.my_role.map]['npcs']
    my_role = self.my_role

    # sets
    my_role.enemy_name = enemy_name
    enemy_role.enemy_name = my_role.name

    # can fight
    if 1:
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
        # del self.factory.users[my_previous_map]['npcs'].npcs[enemy_role.name]

        self.factory.users[battle_map_name] = {}
        self.factory.users[battle_map_name][my_name] = self
        self.factory.users[battle_map_name][enemy_role.name] = enemy_role

        # send roles_in_new_map to my client and enemy client
        roles_in_new_map = {}

        roles_in_new_map[my_name] = my_role
        roles_in_new_map[enemy_name] = enemy_role

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
        # enemy_conn.send('roles_in_battle_map', roles_in_new_map)

        # send disappear message to other roles in my previous map
        names_of_roles_that_disappeared = []
        names_of_roles_that_disappeared.append(self.my_role.name)
        names_of_roles_that_disappeared.append(enemy_role.name)

        for name, conn in self.factory.users[my_previous_map].items():
            if name != 'npcs':
                conn.send('roles_disappeared', names_of_roles_that_disappeared)

    # can't
    else:
        self.send('target_too_far')


def exit_battle(self, message_obj):
    role.exit_battle(self, message_obj)


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
        map_id = role.get_map_id()
        port_map = self.factory.aoi_manager.get_port_map_by_id(map_id)
        port_map.add_player_conn(self)

        # tell other clients nearby of new role
        nearby_players = port_map.get_nearby_players_by_player(role)
        for name, conn in nearby_players.items():
            conn.send('new_role', role)

        # send to client his role and other_roles nearby
        other_roles = []
        nearby_players = port_map.get_nearby_players_by_player(role)
        for name, conn in nearby_players.items():
            other_roles.append(conn.my_role)

        self.send('your_role_data_and_others', [role, other_roles])

    # not ok
    else:
        self.send('no_role_yet')