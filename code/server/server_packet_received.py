from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, threads, defer

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
from protocol import MyProtocol
from DBmanager import Database
from role import Role, Port
import role
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data
from hashes.look_up_tables import nation_2_nation_id
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

        my_ships_hps = [s.now_hp for s in self.my_role.ships]


        print(f"{self.my_role.name}  ships hps:", my_ships_hps)

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

    # already logged in
    if self.account:
        account = self.account
        d = threads.deferToThread(self.factory.db.create_character, account, name)
        d.addCallback(self.on_create_character_got_result)
    else:
        self.send('must_login_first', '')

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
    now_x = messgage_obj[2]
    now_y = messgage_obj[3]

    # change my grid
    map = self.factory.aoi_manager.get_map_by_player(self.my_role)
    map.move_player_conn_to_new_grid(self, new_grid_id)

    # get new and delete grids
    new_grids, delete_grids = map.get_new_and_delete_grids_after_movement(new_grid_id, direction)

    # for me

        # tell client new roles in new grids
    roles_appeared = {}
    for grid in new_grids:
        for name, conn in grid.roles.items():
            if name.isdigit():
                roles_appeared[name] = conn
            else:
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
            if name.isdigit():
                pass
            else:
                conn.send('role_disappeared', self.my_role.name)

        # tell roles in new girds someone appeared
    for grid in new_grids:
        for name, conn in grid.roles.items():
            if name.isdigit():
                pass
            else:
                conn.send('new_role', self.my_role)

    # tell roles in new grids that i started moving
    process_packet(self, 'start_move', [now_x, now_y, direction])


def change_map(self, message_obj):
    # get now_map and target_map
    now_map = self.my_role.map
    target_map = message_obj[0]

    # to sea
    if target_map == 'sea':
        _change_map_to_sea(self, now_map)

    # to port
    elif target_map.isdigit():
        _change_map_to_port(self, target_map, message_obj)

    # change users() state
    prev_map = self.factory.aoi_manager.get_map_by_player(self.my_role)
    nearby_players_in_old_map = prev_map.get_nearby_players_by_player(self.my_role)

    self.my_role.map = target_map
    print("map changed to:", self.my_role.map)
    next_map = self.factory.aoi_manager.get_map_by_player(self.my_role)
    if target_map != 'sea':
        self.my_role.price_index = next_map.price_index
        self.my_role.nation = next_map.nation
        self.my_role.port_economy = next_map.economy
        self.my_role.port_industry = next_map.industry

    prev_map.remove_player(self.my_role)
    next_map.add_player_conn(self)

    # send roles_in_new_map to my client
    roles_in_new_map = {}
    nearby_players_in_new_map = next_map.get_nearby_players_by_player(self.my_role)
    for name, conn in nearby_players_in_new_map.items():
        if name.isdigit():
            roles_in_new_map[name] = conn
        else:
            roles_in_new_map[name] = conn.my_role

    roles_in_new_map[self.my_role.name] = self.my_role

    self.send('roles_in_new_map', roles_in_new_map)

    # send disappear message to other roles in my previous map
    for name, conn in nearby_players_in_old_map.items():
        if name.isdigit():
            pass
        else:
            conn.send('role_disappeared', self.my_role.name)

    # send new_role to other roles in my current map
    for name, conn in nearby_players_in_new_map.items():
        if name.isdigit():
            pass
        else:
            conn.send('new_role', self.my_role)

def _change_map_to_sea(self, now_map):
    # set pos
    port_tile_x = hash_ports_meta_data[int(now_map) + 1]['x']
    port_tile_y = hash_ports_meta_data[int(now_map) + 1]['y']

    self.my_role.x = port_tile_x * c.PIXELS_COVERED_EACH_MOVE
    self.my_role.y = port_tile_y * c.PIXELS_COVERED_EACH_MOVE

    matrix = self.factory.world_map_matrix
    deltas = c.TILES_AROUND_PORTS
    for delta in deltas:
        test_tile_x = port_tile_x + delta[1]
        test_tile_y = port_tile_y + delta[0]
        if int(matrix[test_tile_y, test_tile_x]) in c.SAILABLE_TILES:
            sailable = True
            three_nearby_tiles = c.THREE_NEARBY_TILES_OF_UP_LEFT_TILE
            for tile in three_nearby_tiles:
                if not int(matrix[test_tile_y + tile[1], test_tile_x + tile[0]]) in c.SAILABLE_TILES:
                    sailable = False
                    break

            if sailable:
                self.my_role.x = test_tile_x * c.PIXELS_COVERED_EACH_MOVE
                self.my_role.y = test_tile_y * c.PIXELS_COVERED_EACH_MOVE

    # set speed
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

    # store prev port map id
    self.my_role.prev_port_map_id = int(target_map)

def try_to_fight_with(self, message_obj):
    """enter battle with someone"""
    enemy_name = message_obj[0]

    if enemy_name.isdigit():
        _try_to_fight_with_npc(self, enemy_name)
    else:
        _try_to_fight_with_player(self, enemy_name)

def _try_to_fight_with_player(self, enemy_name):
    # gets
    my_map = self.factory.aoi_manager.get_map_by_player(self.my_role)
    nearby_players = my_map.get_nearby_players_by_player(self.my_role)
    enemy_conn = nearby_players[enemy_name]
    enemy_role = enemy_conn.my_role
    my_role = self.my_role

    # sets
    my_role.enemy_name = enemy_name
    enemy_role.enemy_name = my_role.name

    # can fight
    if enemy_role.ships:
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

        # change map states
        enemy_map = my_map
        my_map.remove_player(self.my_role)
        enemy_map.remove_player(enemy_role)

        battle_map = self.factory.aoi_manager.create_battle_map_by_name(battle_map_name)
        battle_map.add_player_conn(self)
        battle_map.add_player_conn(enemy_conn)

        # each ship needs to know role
        for ship in self.my_role.ships:
            ship.ROLE = self.my_role
        for ship in enemy_role.ships:
            ship.ROLE = enemy_role

        # flagship.steps_left
        flagship = self.my_role.ships[0]
        flagship.steps_left = flagship._calc_max_steps()

        # send roles_in_new_map to my client and enemy client
        roles_in_new_map = {}
        for name, conn in battle_map.get_all_players_inside().items():
            roles_in_new_map[name] = conn.my_role

            # init all ships positions in battle
        _init_all_ships_positions_in_battle(my_name, roles_in_new_map)

            # send
        self.send('roles_in_battle_map', roles_in_new_map)
        enemy_conn.send('roles_in_battle_map', roles_in_new_map)

        # send disappear message to other roles in my previous map
        del nearby_players[enemy_name]

        names_of_roles_that_disappeared = []
        names_of_roles_that_disappeared.append(my_role.name)
        names_of_roles_that_disappeared.append(enemy_role.name)

        for name, conn in nearby_players.items():
            if name.isdigit():
                pass
            else:
                conn.send('roles_disappeared', names_of_roles_that_disappeared)

    # can't
    else:
        self.send('target_too_far')

def _try_to_fight_with_npc(self, enemy_name):
    # gets
    enemy_role = self.factory.npc_manager.get_npc_by_name(enemy_name)
    my_role = self.my_role
    sea_map = self.factory.aoi_manager.get_sea_map()
    nearby_players = sea_map.get_nearby_players_by_player(my_role)

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
        sea_map.remove_player(my_role)
        sea_map.remove_player(enemy_role)

        battle_map = self.factory.aoi_manager.create_battle_map_by_name(battle_map_name)
        battle_map.add_player_conn(self)
        battle_map.add_npc(enemy_role)

        # each ship needs to know role
        for ship in self.my_role.ships:
            ship.ROLE = self.my_role
        for ship in enemy_role.ships:
            ship.ROLE = enemy_role

        # flagship.steps_left
        flagship = self.my_role.ships[0]
        flagship.steps_left = flagship._calc_max_steps()

        # send roles_in_new_map to my client and enemy client
        roles_in_new_map = {}

        roles_in_new_map[my_name] = my_role
        roles_in_new_map[enemy_name] = enemy_role

        # init all ships positions in battle
        _init_all_ships_positions_in_battle(my_name, roles_in_new_map)

        # send
        self.send('roles_in_battle_map', roles_in_new_map)

        # send disappear message to other roles in my previous map
        names_of_roles_that_disappeared = []
        names_of_roles_that_disappeared.append(my_role.name)
        names_of_roles_that_disappeared.append(enemy_role.name)

        for name, conn in nearby_players.items():
            if name.isdigit():
                pass
            else:
                conn.send('roles_disappeared', names_of_roles_that_disappeared)

    # can't
    else:
        self.send('target_too_far')


def _init_all_ships_positions_in_battle(my_name, roles_in_battle):
    for role in roles_in_battle.values():
        # my role
        if role.name == my_name:
            for id, ship in enumerate(role.ships):
                if id <= 4:
                    ship.x = 1
                    ship.y = id
                else:
                    ship.x = 0
                    ship.y = id - 5

                ship.direction = role.direction
        # enemy role
        else:
            for id, ship in enumerate(role.ships):
                if id <= 4:
                    ship.x = 8
                    ship.y = id
                else:
                    ship.x = 9
                    ship.y = id - 5

                ship.direction = role.direction

def exit_battle(self, message_obj):
    my_ships = self.my_role.ships
    enemy_ships = self.my_role.get_enemy_role().ships

    # won or lost
    if not my_ships or not enemy_ships:
        role.exit_battle(self, message_obj)
    # in battle escape
    elif self.my_role.can_escape():
        role.exit_battle(self, message_obj)

def get_npc_info(self, message_obj):
    nation = message_obj[0]
    fleet_type = message_obj[1]

    # get id list
    nation_id = nation_2_nation_id[nation]
    fleet_id_list_for_one_nation = list(range((nation_id - 1) * c.FLEET_COUNT_PER_NATION + 1,
                                              nation_id * c.FLEET_COUNT_PER_NATION + 1))

    fleet_id_list_for_one_type = []
    if fleet_type == 'merchant':
        fleet_id_list_for_one_type.append(fleet_id_list_for_one_nation[0])
        fleet_id_list_for_one_type.append(fleet_id_list_for_one_nation[1])
    elif fleet_type == 'convoy':
        fleet_id_list_for_one_type.append(fleet_id_list_for_one_nation[2])
        fleet_id_list_for_one_type.append(fleet_id_list_for_one_nation[3])
    elif fleet_type == 'battle':
        fleet_id_list_for_one_type.append(fleet_id_list_for_one_nation[4])
        fleet_id_list_for_one_type.append(fleet_id_list_for_one_nation[5])

    # npc list
    npc_list = []
    for id in fleet_id_list_for_one_type:
        npc = self.factory.npc_manager.get_npc_by_name(str(id))
        npc_list.append(npc)

    # prepare dic to send
    dic = {}
    for npc in npc_list:
        # destination
        destination_port_id = None
        if npc.out_ward:
            destination_port_id = npc.end_port_id
        else:
            destination_port_id = npc.start_port_id

        des_port = Port(destination_port_id - 1)
        destination = des_port.name

        # cargo name
        cargo_names = list(npc.ships[-1].cargoes.keys())
        cargo_name = 'nothing'
        if cargo_names:
            cargo_name = cargo_names[0]

        # dic
        dic[npc.name] = {
            'mate_name': npc.mates[0].name,
            'position': [npc.x, npc.y],
            'destination': destination,
            'cargo_name': cargo_name,
        }

    self.send('npc_info', dic)

def get_allied_ports_and_pi(self, message_obj):
    port_map = self.factory.aoi_manager.get_map_by_player(self.my_role)
    nation = port_map.nation

    port_maps_set = self.factory.aoi_manager.nations_ports[nation]
    d = {}
    for port_map in port_maps_set:
        pi = port_map.price_index
        economy = port_map.economy
        industry = port_map.industry

        map_id = port_map.map_id
        if map_id <= 99:
            d[map_id] = [pi, economy, industry]

    self.send('allied_ports_and_pi', d)

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
        map = self.factory.aoi_manager.get_map_by_player(role)
        map.add_player_conn(self)

        self.my_role.price_index = map.price_index
        self.my_role.nation = map.nation
        self.my_role.port_economy = map.economy
        self.my_role.port_industry = map.industry

        # tell other clients nearby of new role
        nearby_players = map.get_nearby_players_by_player(role)
        for name, conn in nearby_players.items():
            conn.send('new_role', role)

        # send to client his role and other_roles nearby
        other_roles = []
        nearby_players = map.get_nearby_players_by_player(role)
        for name, conn in nearby_players.items():
            other_roles.append(conn.my_role)

        self.send('your_role_data_and_others', [role, other_roles])

    # not ok
    else:
        self.send('no_role_yet')



