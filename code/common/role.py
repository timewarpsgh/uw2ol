import random
import time
import copy
import itertools
import numpy
import math


from threading import Timer
from twisted.internet import reactor, task, defer
import constants as c
from hashes.hash_ship_name_to_attributes import hash_ship_name_to_attributes
from hashes.hash_villages import villages_dict
from hashes.hash_mates import hash_mates
from hashes.hash_events import events_dict
from hashes.hash_items import hash_items

# for port
from hashes.hash_ports_meta_data import hash_ports_meta_data
from hashes.hash_region_to_ships_available import hash_region_to_ships_available
from hashes.hash_markets_price_details import hash_markets_price_details
from hashes.hash_special_goods import hash_special_goods
from hashes.hash_paths import hash_paths
from hashes.look_up_tables import capital_2_port_id
from hashes.hash_maids import hash_maids
from hashes.look_up_tables import nation_2_nation_id, nation_2_capital, lv_2_exp_needed_to_next_lv
from hashes.look_up_tables import capital_map_id_2_nation, nation_2_tax_permit_id
from hashes.look_up_tables import now_direction_to_next_left_move, now_direction_to_next_right_move
from hashes.look_up_tables import ship_direction_2_vector, ship_direction_2_next_pos_delta, \
    direct_2_dx_and_dy, direct_2_sea_move_collision_tiles
from hashes.hash_cannons import hash_cannons


# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'client'))

from sprites import Explosion, CannonBall, EngageSign, ShootDamageNumber, EngageMark, ShootMark
from sprites import MoveMark
from helpers import Point


class Role:
    """
    contains portable data for a player (transmitted from DB to server to client)
    and setters(also protocols sent to and from server)
    must only pass one argument called params(a list)

    """

    # class attribute in server
    AOI_MANAGER = None

    # classs attribute in client
    GAME = None

    def __init__(self, x, y, name, gold=2000):
        self._init_basics(x, y, name, gold)
        self._init_instance_containers()
        self._init_quests()

        self._init_current_ports_states()
        self._init_path_for_npc()

    def _init_basics(self, x, y, name, gold):
        self.x = x
        self.y = y
        self.direction = 'up'
        self.moving = False
        self.speed = 20
        self.speed_counter = 0
        self.speed_counter_max = int(200 / self.speed)
        self.person_frame = -1
        self.name = name
        self.enemy_name = None
        self.map = '29'
        self.prev_port_map_id = int(self.map)
        self.in_building_type = None
        self.your_turn_in_battle = False
        self.max_days_at_sea = 0
        self.additioanl_days_at_sea = 0
        self.speak_msg = ''
        self.gold = gold
        self.bank_gold = 2000
        self.target_name = ''


    def _init_instance_containers(self):
        self.ships = []
        self.mates = []
        self.discoveries = {}
        self.bag = Bag(self)
        self.body = Body()

        # both role and mates[0] have these
        self.accountant = None
        self.first_mate = None
        self.chief_navigator = None

    def _init_quests(self):
        # side quests
        self.quest_discovery = None
        self.quest_trade = None
        self.quest_fight = None

        # main quests sequence, last one is the next event
        self.main_events_ids = list(range(1, len(events_dict) + 1))
        self.main_events_ids = list(reversed(self.main_events_ids))
        self.main_quest_port = None
        self.main_quest_building = None

    def _init_current_ports_states(self):
        self.price_index = None
        self.nation = None
        self.port_economy = None
        self.port_industry = None

    def _init_path_for_npc(self):
        if self.is_npc():
            self.point_in_path_id = 0
            self.out_ward = True
            self.start_port_id = random.choice(list(hash_paths.keys()))
            self.end_port_id = None

    # anywhere
    def get_pending_event(self):
        if self.main_events_ids:
            event_id = self.main_events_ids[-1]
            event = Event(event_id)
            return event
        else:
            return None

    def trigger_quest(self, params):
        """when an event is triggered, delete event id"""
        if self.main_events_ids:
            # delete this event
            self.main_events_ids.pop()

            # set next quest tip
            if self.main_events_ids:
                next_event_id = self.main_events_ids[-1]
                next_event = Event(next_event_id)
                self.main_quest_port = next_event.port
                self.main_quest_building = next_event.building

    def get_enemy_role(self):
        enemy_name = self.enemy_name
        enemy_role = self._get_other_role_by_name(enemy_name)
        return enemy_role

    def _get_other_role_by_name(self, name):
        # in client
        if self.GAME:
            if name in self.GAME.other_roles:
                target_role = self.GAME.other_roles[name]
                return target_role
            else:
                return self.GAME.my_role

        # in server
        else:
            # npc
            if str(name).isdigit():
                target_role = Role.FACTORY.npc_manager.get_npc_by_name(name)
                return target_role

            # player
            else:
                my_map = Role.AOI_MANAGER.get_map_by_player(self)
                nearby_players = my_map.get_nearby_players_by_player(self)
                target_role = nearby_players[name].my_role
                return target_role

    def is_in_client(self):
        if self.GAME:
            return True
        else:
            return False

    def is_in_client_and_self(self):
        if self.GAME and self.GAME.my_role.name == self.name:
            return True
        else:
            return False

    def is_in_server(self):
        if not self.GAME:
            return True
        else:
            return False

    def is_in_port(self):
        if str(self.map).isdigit():
            return True
        else:
            return False

    def is_in_battle(self):
        if not self.is_in_port() and not self.is_at_sea():
            return True
        else:
            return False

    def is_in_supply_port(self):
        if self.is_in_port():
            if int(self.map) >= 100:
                return True
            else:
                return False
        else:
            return False

    def is_at_sea(self):
        if self.map == 'sea':
            return True
        else:
            return False

    def is_npc(self):
        if str(self.name).isdigit():
            return True
        else:
            return False

    def have_quest(self):
        if self.quest_discovery:
            return True
        else:
            return False

    def get_port_id(self):
        return self.get_map_id() + 1

    def get_map_id(self):
        return int(self.map)

    def get_x_and_y_tile_position(self):
        x_tile_pos = int(self.x / c.PIXELS_COVERED_EACH_MOVE)
        y_tile_pos = int(self.y / c.PIXELS_COVERED_EACH_MOVE)
        return x_tile_pos, y_tile_pos

    def get_npc_fleet_type(self):
        fleet_sequence = (int(self.name) - 1) % c.FLEET_COUNT_PER_NATION
        if fleet_sequence == 0 or fleet_sequence == 1:
            return 'merchant'
        elif fleet_sequence == 2 or fleet_sequence == 3:
            return 'convoy'
        elif fleet_sequence == 4 or fleet_sequence == 5:
            return 'battle'

    def is_enemy_npc(self):
        enemy_role = self._get_other_role_by_name(self.enemy_name)
        if enemy_role.is_npc():
            return True
        else:
            return False

    def speak(self, params):
        msg = params[0]
        self.speak_msg = msg

        # clear msg after 1s
        reactor.callLater(3, self._speak_clear_msg)

    def _speak_clear_msg(self):
        self.speak_msg = ''
        print("speak msg cleared!")

    def set_target(self, params):
        target_name = params[0]
        self.enemy_name = target_name
        print("target_name:", self.enemy_name)

    def set_speed(self, params):
        speed = params[0]
        self.speed = int(speed)
        self.speed_counter_max = int(200/self.speed)

    def get_fleet_speed(self, params):
        # have ships
        if self.ships:
            # get fleet speed
            speed_list = []
            index = 0
            for ship in self.ships:
                speed = None
                if index == 0:
                    speed = ship.get_speed(self)
                else:
                    speed = ship.get_speed()
                speed_list.append(speed)
                index += 1

            fleet_speed = min(speed_list)

            # modifiers
            if self.body.container['telescope']:
                fleet_speed += 1
            if self.body.container['instrument']:
                item_id = self.body.container['instrument']
                item = Item(item_id)
                fleet_speed += item.effects

            return fleet_speed

        # no ship
        else:
            return 1

    def _get_total_crew(self):
        total_crew = 0
        for ship in self.ships:
            total_crew += ship.crew
        return total_crew

    def equip(self, params):
        item_id = params[0]

        item = Item(item_id)

        # slot has equipment
        if self.body.container[item.type]:
            on_equipment_id = self.body.container[item.type]
            self.bag.add_item(on_equipment_id)
            self.bag.remove_item(item_id)
            self.body.equip(item)

        # empty slot
        else:
            self.body.equip(item)
            self.bag.remove_item(item_id)

        # sound
        if self.is_in_client_and_self():
            self.GAME.sounds['equip'].play()

    def unequip(self, params):
        item_id = params[0]

        item = Item(item_id)
        self.body.unequip(item)
        self.bag.add_item(item_id)

        # sound
        if self.is_in_client_and_self():
            self.GAME.sounds['equip'].play()

    # in port
    def start_move(self, params):
        # get params
        x = params[0]
        y = params[1]
        direction = params[2]

        # hard reset position
        self.x = x
        self.y = y

        # repeat move
        self.direction = direction
        self.moving = True

        # self.move_timer = task.LoopingCall(self.move, [direction])
        # self.move_timer.start(0.15)

    def stop_move(self, params):
        x = params[0]
        y = params[1]

        self.x = x
        self.y = y
        self.moving = False

        # self.move_timer.stop()

    def start_moving_out(self, params):
        """npc only"""
        end_port_id = params[0]
        self.out_ward = True
        self.end_port_id = end_port_id

    def start_moving_back(self, params):
        """npc only"""
        self.out_ward = False

    def move(self, params):
        direction = params[0]

        # dx and dy
        dx = direct_2_dx_and_dy[direction][0]
        dy = direct_2_dx_and_dy[direction][1]
        self.x += dx * c.PIXELS_COVERED_EACH_MOVE
        self.y += dy * c.PIXELS_COVERED_EACH_MOVE
        self.direction = direction

        # change image
        self.person_frame *= -1

        # east and west edge detection
        if self.map == 'sea':
            if self.x < 160:
                self.x = c.WORLD_MAP_X_LENGTH -160
            if self.x > c.WORLD_MAP_X_LENGTH - 160:
                self.x = 160

    def can_move(self, direction):
        # in port
        if self.map.isdigit():

            # get piddle
            piddle = self.GAME.port_piddle

            # perl piddle and python numpy(2d array) are different
            y = int(self.x / 16)
            x = int(self.y / 16)

            # basic 4 directions
            if direction == 'up':

                # not in asia
                if int(self.map) < 94:
                    if piddle[x, y] in c.WALKABLE_TILES and piddle[x, y + 1] in c.WALKABLE_TILES:
                        if self.y > 0:
                            return True
                # in asia
                else:
                    if piddle[x, y] in c.WALKABLE_TILES_FOR_ASIA and piddle[x, y + 1] in c.WALKABLE_TILES_FOR_ASIA:
                        if self.y > 0:
                            return True

            elif direction == 'down':
                if piddle[x + 2, y] in c.WALKABLE_TILES and piddle[x + 2, y + 1] in c.WALKABLE_TILES:
                    if self.y < c.PIXELS_COVERED_EACH_MOVE * (c.PORT_TILES_COUNT - 3):
                        return True
            elif direction == 'left':
                if piddle[x + 1, y - 1] in c.WALKABLE_TILES:
                    return True
            elif direction == 'right':
                if self.x < c.PIXELS_COVERED_EACH_MOVE * (c.PORT_TILES_COUNT - 3):
                    if piddle[x + 1, y + 2] in c.WALKABLE_TILES:
                        return True

            # ret
            return False

        # at sea
        elif self.map == 'sea':
            # get piddle
            piddle = self.GAME.map_maker.world_map_piddle

            # perl piddle and python numpy(2d array) are different
            y = int(self.x / c.PIXELS_COVERED_EACH_MOVE)
            x = int(self.y / c.PIXELS_COVERED_EACH_MOVE)

            tile_list = direct_2_sea_move_collision_tiles[direction]
            for tile in tile_list:
                dx = tile[0]
                dy = tile[1]
                tile_id = int(piddle[x + dx, y + dy])
                if not tile_id in c.SAILABLE_TILES:
                    print(tile_id)
                    return False

            return True

    def get_port(self):
        map_id = int(self.map)
        port = Port(map_id, self)
        return port

    def calculate_max_days_at_sea(self):
        # when no ship
        if not self.ships:
            return 1

        # get all supplies
        all_food = 0
        all_water = 0
        for ship in self.ships:
            all_food += ship.supplies['Food']
            all_water += ship.supplies['Water']
        all_supply = min(all_food, all_water)

        # get all crew
        all_crew = 0
        for ship in self.ships:
            all_crew += ship.crew

        # calculate max days
        max_days = None
        if c.DEVELOPER_MODE_ON:
            max_days = 1000
        else:
            max_days = int(all_supply / (all_crew * c.SUPPLY_CONSUMPTION_PER_PERSON))

        # equipments
        if self.body.container['pet']:
            max_days += 2
        if self.body.container['watch']:
            max_days += 2

        # ret
        return max_days

    def set_mates_duty(self, params):
        """as captain"""
        mate_num = params[0]
        ship_num = params[1]

        if self.is_in_port():
            mate = self.mates[mate_num]
            ship = self.ships[ship_num]
            mate.set_as_captain_of(ship)

    def set_mate_as_hand(self, params):
        """one of 3 kinds of duties"""
        mate_num = params[0]
        position_name = params[1]

        if self.is_in_port():
            mate = self.mates[mate_num]
            mate.set_as_hand(position_name, self)

    def relieve_mates_duty(self, params):
        mate_num = params[0]

        mate = self.mates[mate_num]
        if mate.duty:
            if mate.duty in ['accountant', 'first_mate', 'chief_navigator']:
                mate.relieve_duty(self)
            else:
                mate.relieve_duty()

    def add_mates_lv(self, params):
        mate_num = params[0]

        mate = self.mates[mate_num]
        mate.add_lv()

        if self.is_in_client_and_self():
            self.GAME.sounds['lv_up'].play()

    def add_mates_attribute(self, params):
        mate_num = params[0]
        attribute = params[1]

        mate = self.mates[mate_num]
        mate.add_attribute(attribute)

        if self.is_in_client_and_self():
            self.GAME.sounds['attribute_up'].play()

    def give_exp_to_other_mates(self, params):
        mate_num = params[0]
        amount = params[1]

        if mate_num != 0 and amount <= self.mates[0].exp:
            self.mates[0].exp -= amount
            mate = self.mates[mate_num]
            mate.get_exp(amount)

    def swap_ships(self, params):
        from_ship_num = params[0]
        to_ship_num = params[1]

        if self.is_in_port():
            ships = self.ships
            ships[from_ship_num], ships[to_ship_num] = ships[to_ship_num], ships[from_ship_num]

    def defect(self, params):
        # can
        if self.gold >= c.DEFECT_COST and self.mates[0].lv >= c.DEFECT_LV:
            self.mates[0].nation = capital_map_id_2_nation[self.get_map_id()]
            self.gold -= c.DEFECT_COST

            if self.is_in_client_and_self():
                msg = "You are one of us now!"
                self.GAME.button_click_handler.building_speak(msg)

        # can't
        else:
            if self.is_in_client_and_self():
                msg = "You don't qualify to be one of us. Sorry."
                self.GAME.button_click_handler.building_speak(msg)

    # at sea
    def discover(self, params):
        # discovery_id = random.randint(0, 10)
        discovery_id = params[0]
        # have seen
        if discovery_id in self.discoveries:
            if self.is_in_client_and_self():
                self.GAME.button_click_handler.i_speak("Have seen this.")
        # have not seen
        else:
            if self.quest_discovery == discovery_id or True:
                self.discoveries[discovery_id] = 1
                self.mates[0].exp += c.EXP_PER_DISCOVERY

                # give random item
                rand_seed_num = self.x + self.y + discovery_id
                random.seed(rand_seed_num)
                item_id = random.choice(range(1,len(hash_items) + 1))
                if item_id in c.EXPENSIVE_EQUIPMENTS_IDS:
                    item_id = 1

                self.bag.add_item(item_id)

                # client alert
                if self.is_in_client_and_self():
                    discovery = Discovery(discovery_id)
                    item = Item(item_id)
                    self.GAME.button_click_handler.i_speak(f'We found {discovery.name} '
                                      f'and {item.name}! Got {c.EXP_PER_DISCOVERY} exp.')
                    self.GAME.sounds['discover'].play()
            else:
                if self.is_in_client_and_self():
                    self.GAME.button_click_handler.i_speak("Can't find anything.")

    def consume_potion(self, params):
        potion_id = params[0]

        if self.additioanl_days_at_sea == 0:
            if potion_id in self.bag.get_all_items_dict():
                self.bag.remove_item(potion_id)
                item = Item(potion_id)
                self.additioanl_days_at_sea = item.effects

                if self.is_in_client_and_self():
                    self.GAME.max_days_at_sea += item.effects

    # in battle
    def move_ship(self, params):
        which_ship = params[0]
        direction = params[1]

        self.ships[which_ship].move(direction)
        ship = self.ships[which_ship]
        print(self.name, "'s ship", which_ship, "moved to ", ship.x, ship.y)

    def attack_ship(self, params):
        """returns a deferred"""
        # inits deferred
        deferred = defer.Deferred()

        # get ids
        my_ship_id = params[0]
        target_ship_id = params[1]

        # get ships
        my_ship = self.ships[my_ship_id]
        enemy_ships = self._get_other_role_by_name(self.enemy_name).ships
        target_ship = enemy_ships[target_ship_id]

        # choose attack method
        d_dead = False
        if self.is_npc():
            attack_method = 'shoot'
        else:
            attack_method = self._choose_attack_method(my_ship, target_ship)

        # npc or my other ships
        if self.is_npc() or my_ship_id >= 1:
            # in good condition
            if my_ship.now_hp >= 20 and my_ship.crew >= 50 and my_ship.captain:
                d_dead = self._operate_based_on_attack_method(my_ship, target_ship, attack_method)
            # not good -> escape
            else:
                d_dead = my_ship.try_to_escape(target_ship)
        # my flag ship
        else:
            d_dead = self._operate_based_on_attack_method(my_ship, target_ship, attack_method)

        d_dead.addCallback(self._call_back_for_shoot_or_engage, enemy_ships, target_ship_id, deferred)

        # ret deferred
        return deferred

    def _operate_based_on_attack_method(self, my_ship, target_ship, attack_method):
        if attack_method == 'shoot':
            d_dead = my_ship.try_to_shoot(target_ship)
        elif attack_method == 'engage':
            d_dead = my_ship.try_to_engage(target_ship)
        else:
            d_dead = my_ship.try_to_escape(target_ship)

        return d_dead

    def _choose_attack_method(self, my_ship, target_ship):
        # already set
        if my_ship.attack_method:
            pass
        # not set
        else:
            seed = my_ship.now_hp + my_ship.crew + \
                   target_ship.now_hp + target_ship.crew
            random.seed(seed)
            rand_num = random.randint(0,1)
            if rand_num:
                my_ship.attack_method = 'engage'
            else:
                my_ship.attack_method = 'shoot'

        return my_ship.attack_method

    def _call_back_for_shoot_or_engage(self, d_dead, enemy_ships, target_ship_id, deferred):
        # target dead
        if d_dead:
            # if hp <= 0
            if enemy_ships[target_ship_id].now_hp <= 0:
                del enemy_ships[target_ship_id]

            # if flag ship dead
            if target_ship_id == 0:
                self.__do_when_enemy_lost(enemy_ships, deferred)
            else:
                deferred.callback('next_ship')

        # not dead
        else:
            deferred.callback('next_ship')

    def __do_when_enemy_lost(self, enemy_ships, deferred):
        # all enemy mates relieve duty
        enemy_role = self._get_other_role_by_name(self.enemy_name)
        for mate in enemy_role.mates:
            if mate.duty in ['accountant', 'first_mate', 'chief_navigator']:
                mate.relieve_duty(enemy_role)
            else:
                mate.relieve_duty()

        # all npc enemy ships get rid of captain(one cap for all ships)
        if enemy_role.is_npc():
            for s in enemy_ships:
                s.captain = None

        # get all enemy ships
        self.ships.extend(enemy_ships)
        enemy_ships.clear()
        if len(self.ships) > 10:
            self.ships = self.ships[:10]

        # get all enemy gold
        self.gold += enemy_role.gold
        enemy_role.gold = 0
        print('battle ended. press e to exit battle.')

        # call deferred
        deferred.callback(False)

    def flagship_move(self, params):
        movement = params[0]

        flagship = self.ships[0]
        if flagship.steps_left >= 1:
            # try to move
            if movement == 'continue':
                if flagship._can_move_continue():
                    flagship.move_continue()
            elif movement == 'left':
                if flagship._can_move_to_left():
                    flagship.move_to_left()
            elif movement == 'right':
                if flagship._can_move_to_right():
                    flagship.move_to_right()

            # show marks
            self._show_marks()

        else:
            self.all_ships_operate([False])

    def _show_marks(self):
        self._show_shoot_mark()
        self._show_engage_mark()
        self._show_move_mark()

    def _clear_marks(self):
        game = self.GAME
        if game.mark_sprites:
            for s in game.mark_sprites:
                s.kill()

    def _show_shoot_mark(self):
        if self.is_in_client_and_self():
            game = self.GAME

            self._clear_marks()

            # get start pos
            flag_ship = self.ships[0]
            x = game.screen_surface_rect.centerx
            y = game.screen_surface_rect.centery

            # get ships in range
            ship_ids_in_shoot_range = []
            for id, ship in enumerate(self.get_enemy_role().ships):
                if flag_ship._is_target_ship_in_distance_range(ship):
                    ship_ids_in_shoot_range.append(id)

            # draw mark for each ship
            for id in ship_ids_in_shoot_range:
                d_x = (self.get_enemy_role().ships[id].x - flag_ship.x) * c.BATTLE_TILE_SIZE
                d_y = (self.get_enemy_role().ships[id].y - flag_ship.y) * c.BATTLE_TILE_SIZE

                # draw
                shoot_mark = ShootMark(game, id, x + d_x + 4, y + d_y + 4)
                game.mark_sprites.add(shoot_mark)


    def _show_engage_mark(self):
        if self.is_in_client_and_self():
            game = self.GAME

            # get start pos
            flag_ship = self.ships[0]
            x = game.screen_surface_rect.centerx
            y = game.screen_surface_rect.centery

            # get ships in range
            ship_ids_in_engage_range = []
            for id, ship in enumerate(self.get_enemy_role().ships):
                if flag_ship._is_target_ship_in_engage_range(ship):
                    ship_ids_in_engage_range.append(id)

            # draw mark for each ship
            for id in ship_ids_in_engage_range:
                d_x = (self.get_enemy_role().ships[id].x - flag_ship.x) * c.BATTLE_TILE_SIZE
                d_y = (self.get_enemy_role().ships[id].y - flag_ship.y) * c.BATTLE_TILE_SIZE

                # kill shoot mark on same ship
                for s in game.mark_sprites:
                    if s.ship_id == id:
                        s.kill()

                engage_mark = EngageMark(game, id, x + d_x + 4, y + d_y + 4)
                game.mark_sprites.add(engage_mark)

    def _show_move_mark(self):
        if self.is_in_client_and_self():
            game = self.GAME

            # get start pos
            flag_ship = self.ships[0]
            x = game.screen_surface_rect.centerx
            y = game.screen_surface_rect.centery

            # get ships in range
            available_directs = []
            if flag_ship._can_move_continue():
                available_directs.append('continue')
            if flag_ship._can_move_to_left():
                available_directs.append('left')
            if flag_ship._can_move_to_right():
                available_directs.append('right')

            dict = ship_direction_2_next_pos_delta[flag_ship.direction]
            for direct in available_directs:
                d_x = dict[direct][0] * c.BATTLE_TILE_SIZE
                d_y = dict[direct][1] * c.BATTLE_TILE_SIZE

                if flag_ship.steps_left < 1:
                    move_mark = MoveMark(game, 'no_move', x + d_x, y + d_y)
                    game.mark_sprites.add(move_mark)
                else:
                    move_mark = MoveMark(game, direct, x + d_x, y + d_y)
                    game.mark_sprites.add(move_mark)

    def flag_ship_engage(self, params):
        target_ship_id = params[0]
        enemy_ships = self.get_enemy_role().ships
        self.ships[0].target = target_ship_id
        self.ships[0].attack_method = 'engage'
        self.all_ships_operate([])

    def flag_ship_shoot(self, params):
        target_ship_id = params[0]
        enemy_ships = self.get_enemy_role().ships
        self.ships[0].target = target_ship_id
        self.ships[0].attack_method = 'shoot'
        self.all_ships_operate([])

    def can_escape(self):
        enemy_flagship = self.get_enemy_role().ships[0]
        my_flagship = self.ships[0]
        x1 = my_flagship.x
        y1 = my_flagship.y
        x2 = enemy_flagship.x
        y2 = enemy_flagship.y

        dist = math.hypot(x2 - x1, y2 - y1)
        if dist >= c.ESCAPE_DISTANCE:
            return True
        else:
            return False

    def all_ships_operate(self, params):
        # include flagship ?
        include_flagship = True
        if len(params) > 0:
            if params[0] == False:
                include_flagship = False

        # clear marks
        if self.is_in_client_and_self():
            self._clear_marks()
            self.GAME.reset_think_time_in_battle()

        # do operate
        if self.your_turn_in_battle:
            self._all_ships_do_operate(include_flagship)

    def _all_ships_do_operate(self, include_flagship):
        # stop my turn
        self.your_turn_in_battle = False

        # get my and enemy ships
        enemy_ships = self._get_other_role_by_name(self.enemy_name).ships
        my_ships = self.ships

        # flag ship attacks
        if include_flagship:
            self._pick_one_ship_to_attack([0, enemy_ships])
        else:
            if len(my_ships) >= 2:
                my_ships[0].steps_left = 0
                self._pick_one_ship_to_attack([1, enemy_ships])
            else:
                self._change_turn()

    def set_one_ships_strategy(self, params):
        # params
        ship_id = params[0]
        target_id = params[1]
        attack_method = params[2]

        # set target
        ship = self.ships[ship_id]
        ship.target = target_id

        # set strategy
        if attack_method == 0:
            ship.attack_method = 'shoot'
        elif attack_method == 1:
            ship.attack_method = 'engage'
        elif attack_method == 2:
            ship.attack_method = 'escape'
        else:
            pass

    def set_all_ships_target(self, params):
        target_id = params[0]
        for ship in self.ships:
            ship.target = target_id

    def set_all_ships_attack_method(self, params):
        attack_method_id = params[0]
        attack_method = None
        if attack_method_id == 0:
            attack_method = 'shoot'
        elif attack_method_id == 1:
            attack_method = 'engage'
        elif attack_method_id == 2:
            attack_method = 'escape'

        for ship in self.ships:
            ship.attack_method = attack_method

    def _change_turn(self):
        enemy_role = self.get_enemy_role()
        enemy_role.your_turn_in_battle = True

        if enemy_role.ships:
            enemy_role.ships[0].steps_left = enemy_role.ships[0]._calc_max_steps()

    def _pick_one_ship_to_attack(self, params):
        # calc rand target ship id
        i = params[0]
        enemy_ships = params[1]
        random_target_ship_id = self._calc_rand_target_ship_id(i, enemy_ships)

        # attack
        d_result = self.attack_ship([i, random_target_ship_id])
        self.ships[i].target = random_target_ship_id
        d_result.addCallback(self._call_back_for_attack_ship, i, enemy_ships)

    def _calc_rand_target_ship_id(self, i, enemy_ships):
        # calculate random target id
        rand_seed_num = self.ships[i].x + self.ships[i].y
        random.seed(rand_seed_num)

        enemy_ships_range = range(len(enemy_ships))
        random_target_ship_id = random.choice(enemy_ships_range)
        while enemy_ships[random_target_ship_id].crew <= 0:
            random_target_ship_id = random.choice(enemy_ships_range)

        # reset target id if have it
        target_id = self.ships[i].target
        if not (target_id is None):
            if target_id <= (len(enemy_ships) - 1) and enemy_ships[target_id].crew > 0:
                random_target_ship_id = target_id

        return random_target_ship_id

    def _call_back_for_attack_ship(self, result, i, enemy_ships):
        # not won
        if result == 'next_ship':
            self._not_won_after_attack_ship(i, enemy_ships)
        # won battle
        else:
            self._won_after_attack_ship()

    def _not_won_after_attack_ship(self, i, enemy_ships):
        # if i lost
        if not self.ships or self.ships[0].crew <= 0:
            # lose all my ships
            enemy_ships.extend(self.ships)
            self.ships.clear()

            if len(enemy_ships) > 10:
                enemy_ships = enemy_ships[:10]

            # exit if in client and have ships left (the winner sends exit_battle message to server)
            if Role.GAME:
                reactor.callLater(1, Role.GAME.connection.send,
                                  'exit_battle', [])

        # else
        else:
            # my next ship
            if (i + 1) <= (len(self.ships) - 1):
                reactor.callLater(c.NEXT_SHIP_TIME_INVERVAL,
                                  self._pick_one_ship_to_attack,
                                  [i + 1, enemy_ships])
            # enemy turn
            else:
                reactor.callLater(c.NEXT_SHIP_TIME_INVERVAL, self._change_turn)

    def _won_after_attack_ship(self):
        # player won
        if Role.GAME and Role.GAME.my_role.ships:
            reactor.callLater(1, Role.GAME.connection.send, 'exit_battle', [])
            reactor.callLater(1.5, Role.GAME.button_click_handler.show_victory_window)

        # server controled npc won
        elif self.is_in_server() and self.is_npc():
            print('exiting battle!!!!!!!')
            battle_map = Role.AOI_MANAGER.get_battle_map_by_player_map(self.map)
            all_players_in_battle = battle_map.get_all_players_inside()
            enemy_conn = all_players_in_battle[self.enemy_name]
            exit_battle(enemy_conn, '')

        # server controlled player won
        elif self.is_in_server() and not self.is_npc():
            print('exiting battle!!!!!!!')
            battle_map = Role.AOI_MANAGER.get_battle_map_by_player_map(self.map)
            all_players_in_battle = battle_map.get_all_players_inside()
            enemy_conn = all_players_in_battle[self.enemy_name]
            exit_battle(enemy_conn, '')

    # ship yard
    def buy_ship(self, params):
        type = params[0]
        name = params[1]

        port = self.get_port()
        # if port has this ship
        if type in port.get_available_ships():
            # max 10 ships
            if len(self.ships) <= 9:
                ship = Ship(name, type)
                # if can afford
                if ship.price <= self.gold:
                    # buy
                    self.ships.append(ship)
                    self.gold -= ship.price

                    # sound
                    if self.is_in_client_and_self():
                        self.GAME.sounds['deal'].play()

                # can't afford
                else:
                    if self.is_in_client_and_self():
                        self.GAME.building_text = "Get the ** out of here! You can't afford this."

    def sell_ship(self, params):
        num = params[0]

        if self.ships[num] and num != 0:
            self.gold += int(self.ships[num].price / 2)
            if self.ships[num].captain:
                self.ships[num].captain.relieve_duty()
            del self.ships[num]

            # sound
            if self.is_in_client_and_self():
                self.GAME.sounds['deal'].play()

            print('now ships:', len(self.ships))

    def repair_all(self, params):
        cost = self._calc_repair_all_cost()
        if self.gold >= cost:
            self.gold -= cost
            for ship in self.ships:
                ship.now_hp = ship.max_hp

            if self.is_in_client_and_self():
                msg = "Thank you!"
                self.GAME.button_click_handler.building_speak(msg)
        else:
            if self.is_in_client_and_self():
                msg = "You can't afford to repair them."
                self.GAME.button_click_handler.building_speak(msg)

    def _calc_repair_all_cost(self):
        total_cost = 0
        for ship in self.ships:
            unit_cost = int((ship.price / ship.max_hp) *
                            (ship.max_hp - ship.now_hp) *
                            0.5)
            total_cost += unit_cost
        return total_cost

    def remodel_ship_capacity(self, params):
        ship_num = params[0]
        max_crew = params[1]
        max_guns = params[2]

        self.ships[ship_num].remodel_capacity(max_crew, max_guns)

        if self.is_in_client_and_self():
            self.GAME.sounds['remodel'].play()

    def remodel_ship_name(self, params):
        ship_num = params[0]
        name = params[1]

        self.ships[ship_num].remodel_name(name)

    def remodel_ship_gun(self, params):
        ship_id = params[0]
        gun_id = params[1]

        ship = self.ships[ship_id]
        gun = Gun(gun_id)
        total_cost = ship.max_guns * gun.price

        if self.gold >= total_cost:
            ship.remodel_gun(gun_id)
            self.gold -= total_cost
            if self.is_in_client_and_self():
                self.GAME.button_click_handler.escape_n_times(4)

        else:
            if self.is_in_client_and_self():
                msg = "We can't afford that."
                self.GAME.button_click_handler.i_speak(msg)


    # bar
    def hire_crew(self, params):
        count = params[0]
        to_which_ship = params[1]

        ship = self.ships[to_which_ship]
        # if can hold crew
        if ship.crew + count <= ship.max_crew:
            total_cost = count * c.CREW_UNIT_COST
            if total_cost <= self.gold:
                ship.add_crew(count)
                self.gold -= total_cost

    def fire_crew(self, params):
        count = params[0]
        from_which_ship = params[1]

        # if count right
        ship = self.ships[from_which_ship]
        if ship.crew >= count:
            ship.cut_crew(count)
            print("ship", from_which_ship, "now has crew:", self.ships[from_which_ship].crew)

    def hire_mate(self, params):
        id = params[0]
        mate = Mate(id)
        name = mate.name

        # lv not enough
        if self.mates[0].lv + 10 < mate.lv:
            if self.is_in_client_and_self():
                msg = "Your level is too low. Maybe I'll sail with you the next time."
                msg = self.GAME.translator.translate(msg)
                self.GAME.button_click_handler.mate_speak(mate, msg)
            return

        # leadership must be enough
        if int(self.mates[0].leadership / 10) <= len(self.mates):
            if self.is_in_client_and_self():
                msg = "I don't have enough leadership to handle so many people."
                msg = self.GAME.translator.translate(msg)
                self.GAME.button_click_handler.i_speak(msg)
            return

        # can't hire same mate twice
        for mate_t in self.mates:
            if mate_t.name == name:
                if self.is_in_client_and_self():
                    self.GAME.button_click_handler.i_speak("Already have this guy.")
                return


        # do hire
        self.mates.append(mate)

        if self.is_in_client_and_self():
            self.GAME.button_click_handler.escape_thrice()
            msg = "Thank you, captain. I'll do my best."
            reactor.callLater(0.3, self.GAME.button_click_handler.mate_speak, mate, msg)

    def quest_hire_mate(self, params):
        id = params[0]
        if id in {2, 3, 4}:
            mate = Mate(id)
            self.mates.append(mate)

    def fire_mate(self, params):
        num = params[0]

        if num == 0:
            pass
        else:
            self.relieve_mates_duty([num])
            del self.mates[num]
            print('now mates:', len(self.mates))

    # market
    def get_buy_price_modifier(self):
        mate = None
        if self.accountant:
            mate = self.accountant
        else:
            mate = self.mates[0]

        price_index = self.price_index
        buy_price_modifier = (100 - (100 - price_index) - (mate.knowledge + mate.accounting * 20) / 4) / 100
        return buy_price_modifier

    def get_sell_price_modifier(self):
        mate = None
        if self.accountant:
            mate = self.accountant
        else:
            mate = self.mates[0]

        price_index = self.price_index
        sell_price_modifier = (50 + (price_index - 100) + mate.intuition + mate.accounting * 10) / 100
        return sell_price_modifier

    def buy_cargo(self, params):
        cargo_name = params[0]
        count = params[1]
        to_which_ship = params[2]

        port = self.get_port()

        # if port has this item
        if cargo_name in port.get_availbale_goods_dict():
            # if ship has space to add cargo
            ship = self.ships[to_which_ship]
            if ship.can_add_cargo_or_supply(count):
                # get total_cost
                unit_price = port.get_commodity_buy_price(cargo_name)
                buy_price_modifier = self.get_buy_price_modifier()
                unit_price = int(unit_price * buy_price_modifier)

                    # has the right tax permit
                right_tax_permit_id = nation_2_tax_permit_id[self.nation]
                total_cost = 0
                if right_tax_permit_id in self.bag.get_all_items_dict() and \
                        self.nation == self.mates[0].nation:
                    total_cost = count * unit_price
                    self.bag.remove_item(right_tax_permit_id)
                else:
                    total_cost = int(count * unit_price * 1.2)

                # can afford
                if self.gold >= total_cost:
                    self.gold -= total_cost
                    ship.add_cargo(cargo_name, count)

                    if self.is_in_client_and_self():
                        self.GAME.sounds['deal'].play()
                        msg = "Thank you!"
                        self.GAME.button_click_handler.building_speak(msg)
                # can't afford
                else:
                    if self.is_in_client_and_self():
                        msg = "You don't have enough gold."
                        self.GAME.button_click_handler.building_speak(msg)


                print(self.name, "ship", to_which_ship, "cargoes", self.ships[to_which_ship].cargoes)
                print(self.name, "gold:", self.gold)

            # inventory full
            else:
                if self.is_in_client_and_self():
                    msg = "This ship dosen't have enough room."
                    self.GAME.button_click_handler.i_speak(msg)

    def sell_cargo(self, params):
        cargo_name = params[0]
        from_which_ship = params[1]
        count = params[2]

        ship = self.ships[from_which_ship]

        # if has cargo
        if cargo_name in ship.cargoes:
            # if count right
            if count <= ship.cargoes[cargo_name]:
                # cut cargo
                ship.cut_cargo(cargo_name, count)

                # add gold
                port = self.get_port()
                unit_price = port.get_commodity_sell_price(cargo_name)
                sell_price_modifier = self.get_sell_price_modifier()
                unit_price = int(unit_price * sell_price_modifier)
                total_gold = count * unit_price
                self.gold += total_gold

                # add exp
                total_exp = int(count * unit_price / 100) * c.EXP_GOT_MODIFIER
                self.mates[0].exp += total_exp

                if self.is_in_client_and_self():
                    msg = f"Got {total_gold} gold coins and {total_exp} exp for {count} {cargo_name}"
                    self.GAME.button_click_handler.i_speak(msg)
                    self.GAME.sounds['deal'].play()



    # harbor
    def load_supply(self, params):
        # params
        supply_name = params[0]
        count = params[1]
        to_which_ship = params[2]

        # if name right
        ship = self.ships[to_which_ship]
        if supply_name in ship.supplies:
            # if count right
            if count <= ship.get_cargo_and_supply_capacity():
                ship.load_supply(supply_name, count)
                self.gold -= count * c.SUPPLY_UNIT_COST
                print(self.name, "ship", to_which_ship, "supplies", self.ships[to_which_ship].supplies[supply_name])

    def unload_supply(self, params):
        # params
        supply_name = params[0]
        count = params[1]
        from_which_ship = params[2]

        # if name right
        ship = self.ships[from_which_ship]
        ship.unload_supply(supply_name, count)
        print(self.name, "ship", from_which_ship, "supplies", 'unloaded')

    # job house

        # discovery
    def start_discovery_quest(self, params):
        discovery_id = params[0]
        # for testing (rosetta stone near Alexandra)
        # discovery_id = 31

        if discovery_id not in self.discoveries:
            self.quest_discovery = discovery_id
            print('quset started id:', discovery_id)
        else:
            print('have been there!')

    def give_up_discovery_quest(self, params):
        self.quest_discovery = None

    def submit_discovery_quest(self, params):
        if self.quest_discovery in self.discoveries and self.quest_discovery:
            # result
            self.mates[0].exp += c.EXP_PER_DISCOVERY
            self.gold += c.GOLD_REWARD_FOR_HANDING_IN_QUEST
            self.quest_discovery = None

            # client does
            if self.is_in_client_and_self():
                self.GAME.button_click_handler.building_speak("Well done!")
                self.GAME.button_click_handler.i_speak(f"Got exp {c.EXP_PER_DISCOVERY}, "
                                                       f"gold coins {c.GOLD_REWARD_FOR_HANDING_IN_QUEST}.")

        # trade
    def set_trade_quest(self):
        pass

        # fight
    def set_fight_quest(self):
        pass

    # bank
    def deposit_gold(self, params):
        amount = params[0]

        if amount <= self.gold:
            self.gold -= amount
            self.bank_gold += amount

    def withdraw_gold(self, params):
        amount = params[0]

        if amount <= self.bank_gold:
            self.bank_gold -= amount
            self.gold += amount

    def get_max_credit(self):
        max_credit = self.mates[0].lv * 1000
        return max_credit

    def borrow(self, params):
        amount = params[0]

        if self.bank_gold <= 0:
            if amount + abs(self.bank_gold) <= self.get_max_credit():
                self.gold += amount
                self.bank_gold -= amount

    def repay(self, params):
        amount = params[0]

        if self.bank_gold <= 0:
            if amount <= self.gold:
                self.bank_gold += amount
                self.gold -= amount

    # item shop
    def sell_item(self, params):
        item_id = params[0]

        if item_id in self.bag.get_all_items_dict():
            # sell
            self.bag.remove_item(item_id)
            item = Item(item_id)
            self.gold += int(item.price / 2)

            # sound
            if self.is_in_client_and_self():
                self.GAME.sounds['deal'].play()

    def buy_items(self, params):
        item_id = params[0]
        count = params[1]

        now_port = Port(int(self.map))
        if item_id in now_port.get_available_items_ids_for_sale():
            total_charge = Item(item_id).price * count
            if self.gold >= total_charge:
                if self.bag.add_multiple_items(item_id, count):
                    self.gold -= total_charge
                    if self.is_in_client_and_self():
                        self.GAME.sounds['deal'].play()


class Ship:
    def __init__(self, name, type):
        self.name = name
        self.type = type

        self._init_attributes_from_hash(type)
        self._init_others()
        self._init_cargoes_and_supplies()
        self._init_owner_of_this_ship()

    def _init_attributes_from_hash(self, type):
        ship_dict = hash_ship_name_to_attributes[type]

        self.now_hp = ship_dict['durability']
        self.max_hp = ship_dict['durability']

        self.tacking = ship_dict['tacking']
        self.power = ship_dict['power']

        self.capacity = ship_dict['capacity']
        self.max_guns = ship_dict['max_guns']
        self.min_crew = ship_dict['min_crew']
        self.max_crew = ship_dict['max_crew']

        self.price = ship_dict['price']

    def _init_others(self):
        self.useful_capacity = self.capacity - self.max_guns - self.max_crew
        self.x = 10
        self.y = 10
        self.direction = 'up'
        self.target = None
        self.attack_method = None
        self.gun = 1

        # mate
        self.captain = None

        # crew
        self.crew = 5

    def _init_cargoes_and_supplies(self):
        self.cargoes = {}
        self.supplies = {
            'Food':5,
            'Water':5,
            'Lumber':0,
            'Shot':0
        }

    def _init_owner_of_this_ship(self):
        """instance attribute set when entered battle"""
        self.ROLE = None

    def remodel_gun(self, gun_id):
        self.gun = gun_id

    def remodel_name(self, name):
        self.name = name

    def remodel_capacity(self, max_crew, max_guns):
        type = self.type
        ship_dict = hash_ship_name_to_attributes[type]
        if max_crew <= ship_dict['max_crew'] and max_crew >= self.min_crew:
            self.max_crew = max_crew
        if max_guns <= ship_dict['max_guns'] and max_guns >= 0:
            self.max_guns = max_guns

        self.useful_capacity = self.capacity - self.max_guns - self.max_crew

    def get_cargo_and_supply_capacity(self):
        """number of empty space for cargo and supply"""
        # cargoes_count
        cargoes_count = 0
        for v in self.cargoes.values():
            cargoes_count += v

        # supplies_count
        supplies_count = 0
        for v in self.supplies.values():
            supplies_count += v

        # capacity
        capacity = self.useful_capacity - cargoes_count - supplies_count

        return capacity

    def can_add_cargo_or_supply(self, count):
        capacity = self.get_cargo_and_supply_capacity()
        if count <= capacity:
            return True
        else:
            return False

    def _calc_max_steps(self):
        # has captain
        if self.captain:
            seamanship = None
            if self.captain.chief_navigator:
                seamanship = self.captain.chief_navigator.seamanship
            else:
                seamanship = self.captain.seamanship
            max_steps = int((self.tacking + self.power + seamanship) / 40) - 1
            return max_steps

        # no captain
        else:
            return 1

    def get_speed(self, role=''):
        # have captain
        if self.captain:
            speed = 1

            # when role not passed (not flag ship)
            if not role:
                speed = int((self.tacking + self.power +
                             self.captain.seamanship + self.captain.navigation * 10)/10) - 5
            # when role is passed (flag ship)
            else:
                # if have navigator
                if role.chief_navigator:
                    speed = int((self.tacking + self.power +
                                 role.chief_navigator.seamanship + role.chief_navigator.navigation * 10) / 10) - 5
                # no navigator
                else:
                    speed = int((self.tacking + self.power +
                                 self.captain.seamanship + self.captain.navigation * 10)/10) - 5
            # modify speed
            if speed >= 20:
                speed = 20

            factor = self.crew / self.min_crew
            if factor < 1:
                speed = int(speed * factor)
                if speed < 1:
                    speed = 1

            return speed - c.SHIP_SPEED_CUT
        # no captain
        else:
            return 1

    def move_to_right(self):
        next_direct = now_direction_to_next_right_move[self.direction]
        self.move(next_direct)

    def move_to_left(self):
        next_direct = now_direction_to_next_left_move[self.direction]
        self.move(next_direct)

    def move_continue(self):
        self.move(self.direction)

    def _can_move_to_right(self):
        next_direct = now_direction_to_next_right_move[self.direction]
        return self.can_move(next_direct)

    def _can_move_to_left(self):
        next_direct = now_direction_to_next_left_move[self.direction]
        return self.can_move(next_direct)

    def _can_move_continue(self):
        return self.can_move(self.direction)

    def move(self, direction):
        # move
        if direction in {'up', 'down', 'left', 'right'}:
            self._basic_move(direction)
        else:
            self._additional_move(direction)

    def _basic_move(self, direction):
        if direction == 'up':
            self.y -= 1
            self.direction = 'up'
        elif direction == 'down':
            self.y += 1
            self.direction = 'down'
        elif direction == 'left':
            self.x -= 1
            self.direction = 'left'
        elif direction == 'right':
            self.x += 1
            self.direction = 'right'

        self.steps_left -= 1

    def _additional_move(self, direction):
        if direction == 'ne':
            self.x += 1
            self.y -= 1
            self.direction = 'ne'
        elif direction == 'nw':
            self.x -= 1
            self.y -= 1
            self.direction = 'nw'
        elif direction == 'se':
            self.x += 1
            self.y += 1
            self.direction = 'se'
        elif direction == 'sw':
            self.x -= 1
            self.y += 1
            self.direction = 'sw'

        self.steps_left -= 1.5

    def can_move(self, direction):
        # get future x,y
        future_x = self.x
        future_y = self.y
        if direction == 'up':
            future_y -= 1
        elif direction == 'down':
            future_y += 1
        elif direction == 'left':
            future_x -= 1
        elif direction == 'right':
            future_x += 1

        elif direction == 'ne':
            future_x += 1
            future_y -= 1
        elif direction == 'sw':
            future_x -= 1
            future_y += 1
        elif direction == 'nw':
            future_x -= 1
            future_y -= 1
        elif direction == 'se':
            future_x += 1
            future_y += 1

        # collide with any of my ships?
        for ship in self.ROLE.ships:
            if ship.x == future_x and ship.y == future_y:
                return False

        # collide with any of enemy ships?
        enemy_name = self.ROLE.enemy_name
        enemy_role = self.ROLE._get_other_role_by_name(enemy_name)
        for ship in enemy_role.ships:
            if ship.x == future_x and ship.y == future_y:
                return False

        # return ture
        return True

    def try_to_shoot(self, ship):
        """returns a deferred"""
        # inits a deffered
        deferred = defer.Deferred()

        # init max steps
        self.steps_left = self._calc_max_steps()

        # check
        if ship.crew > 0 and self.crew > 0:
            self.shoot_or_move_closer(ship, deferred)
        else:
            deferred.callback(False)

        # ret
        return deferred

    def shoot_or_move_closer(self, ship, deferred):
        # in range
        if self._is_target_ship_in_distance_range(ship):
            self.shoot(ship, deferred)
        # not in range
        else:
            # move closer
            moved = self.move_closer(ship, deferred)
            if moved:
                # if have steps
                if self.steps_left >= 1:
                    reactor.callLater(c.BATTLE_MOVE_TIME_INVERVAL, self.shoot_or_move_closer, ship, deferred)
                # no more steps
                else:
                    deferred.callback(False)

    def _is_target_ship_in_distance_range(self, ship):
        dist = math.hypot(self.x - ship.x, self.y - ship.y)
        if dist <= c.SHOOT_RANGE_IN_BATTLE:
            return True
        else:
            return False

    def _is_point_left_of_vector(self, A, B, M):
        """ A,B: points of the vector
            M: point to check
        """
        position = numpy.sign((B.x - A.x) * (M.y - A.y) - (B.y - A.y) * (M.x - A.x))
        return position

    def move_closer(self, ship, deferred):
        dict = ship_direction_2_vector
        target_point = Point(ship.x - self.x, self.y - ship.y)

        p0 = dict[self.direction][0]
        p1 = dict[self.direction][1]
        is_target_left = self._is_point_left_of_vector(p0, p1, target_point)

        # left
        if is_target_left != -1:
            next_direct_left = now_direction_to_next_left_move[self.direction]
            next_direct_right = now_direction_to_next_right_move[self.direction]
            if self.can_move(next_direct_left):
                self.move_to_left()
            elif self.can_move(self.direction):
                self.move_continue()
            elif self.can_move(next_direct_right):
                self.move_to_right()
            else:
                deferred.callback(False)
                return False
        # right
        elif is_target_left == -1:
            next_direct_right = now_direction_to_next_right_move[self.direction]
            next_direct_left = now_direction_to_next_left_move[self.direction]
            if self.can_move(next_direct_right):
                self.move_to_right()
            elif self.can_move(self.direction):
                self.move_continue()
            elif self.can_move(next_direct_left):
                self.move_to_left()
            else:
                deferred.callback(False)
                return False
        return True

    def move_further(self, ship, deferred):
        dict = ship_direction_2_vector
        target_point = Point(ship.x - self.x, self.y - ship.y)

        p0 = dict[self.direction][0]
        p1 = dict[self.direction][1]
        is_target_left = self._is_point_left_of_vector(p0, p1, target_point)

        # left
        if is_target_left == 1:
            next_direct_left = now_direction_to_next_left_move[self.direction]
            next_direct_right = now_direction_to_next_right_move[self.direction]
            if self.can_move(next_direct_right):
                self.move_to_right()
            elif self.can_move(self.direction):
                self.move_continue()
            elif self.can_move(next_direct_left):
                self.move_to_left()
            else:
                deferred.callback(False)
                return False
        # right
        elif is_target_left == -1:
            next_direct_right = now_direction_to_next_right_move[self.direction]
            next_direct_left = now_direction_to_next_left_move[self.direction]
            if self.can_move(next_direct_left):
                self.move_to_left()
            elif self.can_move(self.direction):
                self.move_continue()
            elif self.can_move(next_direct_right):
                self.move_to_right()
            else:
                deferred.callback(False)
                return False
        # in line
        elif is_target_left == 0:
            next_direct = self.direction
            next_direct_right = now_direction_to_next_right_move[self.direction]
            next_direct_left = now_direction_to_next_left_move[self.direction]
            if self.can_move(next_direct_left):
                self.move_to_left()
            elif self.can_move(next_direct_right):
                self.move_to_right()
            elif self.can_move(next_direct):
                self.move_continue()
            else:
                deferred.callback(False)
                return False
        return True

    def shoot(self, ship, deferred):
        # change states
        self._show_shooting_anim(ship)
        reactor.callLater(1, self._show_explosion_anim, ship)
        reactor.callLater(1.3, self._deal_shoot_damage, ship, deferred)

    def _deal_shoot_damage(self, ship, deferred):
        # damage based on attributes
        damage = 0
        gun = Gun(self.gun)

        # if no first mate
        if not self.captain.first_mate:
            damage = c.SHOOT_DAMAGE * int(( (self.max_guns * gun.damage) +
                                            int(self.captain.swordplay / 2) +
                                            self.captain.gunnery * 20) / 10)
        # if have first mate
        else:
            damage = c.SHOOT_DAMAGE * int(
                ((self.max_guns * gun.damage) +
                 int(self.captain.first_mate.swordplay / 2) +
                 self.captain.first_mate.gunnery * 20) / 10)

        # damage based on equipments

            # add damage
        if self.ROLE.body.container['weapon']:
            item_id = self.ROLE.body.container['weapon']
            item = Item(item_id)
            percent = (100 + item.effects) / 100
            damage = int(damage * percent)

            # mitigate damage
        enemy_name = self.ROLE.enemy_name
        enemy_role = self.ROLE._get_other_role_by_name(enemy_name)
        if enemy_role.body.container['armor']:
            item_id = enemy_role.body.container['armor']
            item = Item(item_id)
            percent = (100 - item.effects) / 100
            damage = int(damage * percent)

        # do damage
        if damage < 0:
            damage = 0

        random.seed(self.x + ship.y + ship.now_hp)
        ratio_rand = random.randint(30, 180) / 100
        damage = int(damage * ratio_rand)

        ship.now_hp -= damage
        self._show_shoot_damage_number(ship, damage)

        # no negative hp
        if ship.now_hp < 0:
            ship.now_hp = 0

        print("target now hp", ship.now_hp)

        my_hps = [s.now_hp for s in self.ROLE.ships]

        print(f"{self.ROLE.name} ships hps:", my_hps)


        # ret
        result = ship.now_hp <= 0
        deferred.callback(result)

    def _show_shoot_damage_number(self, ship, damage):
        # show explosion anim
        if not self.ROLE.is_in_server():

            # self is me
            if self.ROLE.is_in_client_and_self():
                game = self.ROLE.GAME

                # get start pos
                flag_ship = self.ROLE.ships[0]
                x = game.screen_surface_rect.centerx - (flag_ship.x - self.x) * c.BATTLE_TILE_SIZE
                y = game.screen_surface_rect.centery - (flag_ship.y - self.y) * c.BATTLE_TILE_SIZE

                # get target pos
                d_x = (ship.x - self.x) * c.BATTLE_TILE_SIZE
                d_y = (ship.y - self.y) * c.BATTLE_TILE_SIZE

                # draw
                damage_num = ShootDamageNumber(game, damage, x + d_x +8, y + d_y - 8)
                game.all_sprites.add(damage_num)

            # self if enemy
            else:
                game = self.ROLE.GAME

                # get start pos
                my_role = self.ROLE.get_enemy_role()
                if my_role.ships:
                    flag_ship = my_role.ships[0]
                    x = game.screen_surface_rect.centerx - (flag_ship.x - self.x) * c.BATTLE_TILE_SIZE
                    y = game.screen_surface_rect.centery - (flag_ship.y - self.y) * c.BATTLE_TILE_SIZE

                    # get target pos
                    d_x = (ship.x - self.x) * c.BATTLE_TILE_SIZE
                    d_y = (ship.y - self.y) * c.BATTLE_TILE_SIZE

                    # draw
                    damage_num = ShootDamageNumber(game, damage, x + d_x +8, y + d_y - 8)
                    game.all_sprites.add(damage_num)

    def _show_shooting_anim(self, ship):
        # show explosion anim
        if not self.ROLE.is_in_server():

            # self is me
            if self.ROLE.is_in_client_and_self():
                game = self.ROLE.GAME

                # get start pos
                flag_ship = self.ROLE.ships[0]
                x = game.screen_surface_rect.centerx - (flag_ship.x - self.x) * c.BATTLE_TILE_SIZE
                y = game.screen_surface_rect.centery - (flag_ship.y - self.y) * c.BATTLE_TILE_SIZE

                # get target pos
                d_x = (ship.x - self.x) * c.BATTLE_TILE_SIZE
                d_y = (ship.y - self.y) * c.BATTLE_TILE_SIZE

                # draw
                cannnon_ball = CannonBall(game, (x+8), (y+8), d_x, d_y)
                game.all_sprites.add(cannnon_ball)

            # self if enemy
            else:
                game = self.ROLE.GAME

                # get start pos
                my_role = self.ROLE.get_enemy_role()
                flag_ship = my_role.ships[0]
                x = game.screen_surface_rect.centerx - (flag_ship.x - self.x) * c.BATTLE_TILE_SIZE
                y = game.screen_surface_rect.centery - (flag_ship.y - self.y) * c.BATTLE_TILE_SIZE

                # get target pos
                d_x = (ship.x - self.x) * c.BATTLE_TILE_SIZE
                d_y = (ship.y - self.y) * c.BATTLE_TILE_SIZE

                # draw
                cannnon_ball = CannonBall(game, (x + 8), (y + 8), d_x, d_y)
                game.all_sprites.add(cannnon_ball)

            # sound
            reactor.callLater(0.02, self.ROLE.GAME.sounds['shoot'].play)

    def engage(self, ship):
        # change values

            # self engage
        self_damage_ratio = 0
        if not self.captain.first_mate:
            self_damage_ratio = (self.captain.swordplay + self.captain.gunnery * 20) / 100
        else:
            self_damage_ratio = (self.captain.first_mate.swordplay + self.captain.first_mate.gunnery * 20) / 100

        self_damage = int(c.ENGAGE_DAMAGE * self.crew * self_damage_ratio / 3)

                # damage based on equipments
        if self.ROLE.body.container['weapon']:
            item_id = self.ROLE.body.container['weapon']
            item = Item(item_id)
            percent = (100 + item.effects) / 100
            self_damage = int(self_damage * percent)

                # mitigate damage
        enemy_name = self.ROLE.enemy_name
        enemy_role = self.ROLE._get_other_role_by_name(enemy_name)
        if enemy_role.body.container['armor']:
            item_id = enemy_role.body.container['armor']
            item = Item(item_id)
            percent = (100 - item.effects) / 100
            self_damage = int(self_damage * percent)

        if self_damage <= 5:
            self_damage = 5

        ship.crew -= self_damage

            # enemy engage
        enemy_damage_ratio = 0
        if ship.captain:
            if not ship.captain.first_mate:
                enemy_damage_ratio = (ship.captain.swordplay + ship.captain.gunnery * 20) / 100
            else:
                enemy_damage_ratio = (ship.captain.first_mate.swordplay + ship.captain.first_mate.gunnery * 20) / 100


        enemy_damage = int(c.ENGAGE_DAMAGE * ship.crew * enemy_damage_ratio / 3)

                # damage based on equipments
        enemy_name = self.ROLE.enemy_name
        enemy_role = self.ROLE._get_other_role_by_name(enemy_name)
        if enemy_role.body.container['weapon']:
            item_id = enemy_role.body.container['weapon']
            item = Item(item_id)
            percent = (100 + item.effects) / 100
            enemy_damage = int(enemy_damage * percent)

                # mitigate damage
        if self.ROLE.body.container['armor']:
            item_id = self.ROLE.body.container['armor']
            item = Item(item_id)
            percent = (100 - item.effects) / 100
            enemy_damage = int(enemy_damage * percent)

        if enemy_damage <= 5:
            enemy_damage = 5

        self.crew -= enemy_damage

        # show anim
        self._show_engage_anim(ship, self_damage, enemy_damage)

        # no negative values
        if self.crew < 0:
            self.crew = 0
        if ship.crew < 0:
            ship.crew = 0

        # ret
        return ship.crew <= 0

    def _show_engage_anim(self, ship, self_damage, enemy_damage):
        if not self.ROLE.is_in_server():
            # self is me
            if self.ROLE.is_in_client_and_self():
                game = self.ROLE.GAME
                flag_ship = self.ROLE.ships[0]
                x = game.screen_surface_rect.centerx - (flag_ship.x - ship.x) * c.BATTLE_TILE_SIZE + 6
                y = game.screen_surface_rect.centery - (flag_ship.y - ship.y) * c.BATTLE_TILE_SIZE + 6

                # target
                engage_sign = EngageSign(game, x, y)
                game.all_sprites.add(engage_sign)

                dmg = ShootDamageNumber(game, self_damage, x, y, c.WHITE)
                game.all_sprites.add(dmg)

                # my ship
                x_1 = x + (self.x - ship.x) * c.BATTLE_TILE_SIZE
                y_1 = y + (self.y - ship.y) * c.BATTLE_TILE_SIZE
                engage_sign1 = EngageSign(game, x_1, y_1)
                game.all_sprites.add(engage_sign1)

                dmg_1 = ShootDamageNumber(game, enemy_damage, x_1, y_1, c.WHITE)
                game.all_sprites.add(dmg_1)

            # self if enemy
            else:
                game = self.ROLE.GAME
                enemy_role = self.ROLE._get_other_role_by_name(self.ROLE.enemy_name)
                flag_ship = enemy_role.ships[0]
                x = game.screen_surface_rect.centerx - (flag_ship.x - ship.x) * c.BATTLE_TILE_SIZE + 6
                y = game.screen_surface_rect.centery - (flag_ship.y - ship.y) * c.BATTLE_TILE_SIZE + 6

                # target
                engage_sign = EngageSign(game, x, y)
                game.all_sprites.add(engage_sign)

                dmg = ShootDamageNumber(game, self_damage, x, y, c.WHITE)
                game.all_sprites.add(dmg)

                # my ship
                x_1 = x + (self.x - ship.x) * c.BATTLE_TILE_SIZE
                y_1 = y + (self.y - ship.y) * c.BATTLE_TILE_SIZE
                engage_sign1 = EngageSign(game, x_1, y_1)
                game.all_sprites.add(engage_sign1)

                dmg_1 = ShootDamageNumber(game, enemy_damage, x_1, y_1, c.WHITE)
                game.all_sprites.add(dmg_1)

            # sound
            self.ROLE.GAME.sounds['engage'].play()

    def try_to_engage(self, ship):
        """returns a deferred"""
        # inits a deffered
        deferred = defer.Deferred()

        # init max steps
        self.steps_left = self._calc_max_steps()

        # check
        if ship.crew > 0 and self.crew > 0:
            self.engage_or_move_closer(ship, deferred)
        else:
            deferred.callback(False)

        # ret
        return deferred

    def engage_or_move_closer(self, ship, deferred):
        # if in range
        if self._is_target_ship_in_engage_range(ship):
            # engage
            result = self.engage(ship)

            # call back
            deferred.callback(result)

        # not in range
        else:
            # move closer
            moved = self.move_closer(ship, deferred)

            if moved:
                # if have steps
                if self.steps_left >= 1:
                    reactor.callLater(c.BATTLE_MOVE_TIME_INVERVAL, self.engage_or_move_closer, ship, deferred)
                # no more steps
                else:
                    deferred.callback(False)

    def _is_target_ship_in_engage_range(self, ship):
        if abs(self.x - ship.x) <= c.ENGAGE_RANGE and abs(self.y - ship.y) <= c.ENGAGE_RANGE:
            return True
        else:
            return False

    def _show_explosion_anim(self, ship):
        if not self.ROLE.is_in_server():
            # self is me
            if self.ROLE.is_in_client_and_self():
                game = self.ROLE.GAME
                flag_ship = self.ROLE.ships[0]
                x = game.screen_surface_rect.centerx - (flag_ship.x - ship.x) * c.BATTLE_TILE_SIZE
                y = game.screen_surface_rect.centery - (flag_ship.y - ship.y) * c.BATTLE_TILE_SIZE

                explosion = Explosion(game, x, y)
                self.ROLE.GAME.all_sprites.add(explosion)

            # self if enemy
            else:
                game = self.ROLE.GAME
                enemy_role = self.ROLE._get_other_role_by_name(self.ROLE.enemy_name)
                flag_ship = enemy_role.ships[0]
                x = game.screen_surface_rect.centerx - (flag_ship.x - ship.x) * c.BATTLE_TILE_SIZE
                y = game.screen_surface_rect.centery - (flag_ship.y - ship.y) * c.BATTLE_TILE_SIZE

                explosion = Explosion(game, x, y)
                self.ROLE.GAME.all_sprites.add(explosion)

            # sound
            self.ROLE.GAME.sounds['explosion'].play()

    def try_to_escape(self, ship):
        """returns a deferred"""
        # inits a deffered
        deferred = defer.Deferred()

        # init max steps
        self.steps_left = self._calc_max_steps()

        # check
        if ship.crew > 0 and self.crew > 0:
            self.move_away(ship, deferred)
        else:
            deferred.callback(False)

        # ret
        return deferred

    def move_away(self, ship, deferred):
        # move closer
        moved = self.move_further(ship, deferred)

        if moved:
            # if have steps
            if self.steps_left >= 1:
                reactor.callLater(c.BATTLE_MOVE_TIME_INVERVAL, self.move_away, ship, deferred)
            # no more steps
            else:
                deferred.callback(False)

    def add_crew(self, count):
        self.crew += count

    def cut_crew(self, count):
        self.crew -= count

    def add_cargo(self, cargo_name, count):
        if cargo_name in self.cargoes:
            self.cargoes[cargo_name] += count
        else:
            self.cargoes[cargo_name] = count

        return True

    def cut_cargo(self, cargo_name, count):
        self.cargoes[cargo_name] -= count
        if self.cargoes[cargo_name] <= 0:
            del self.cargoes[cargo_name]


    def load_supply(self, supply_name, count):
        if supply_name in self.supplies:
            self.supplies[supply_name] += count
        else:
            self.supplies[supply_name] = count

        return True

    def unload_supply(self, supply_name, count):
        if supply_name in self.supplies:
            self.supplies[supply_name] -= count
            if self.supplies[supply_name] < 0:
                self.supplies[supply_name] = 0


class Mate:
    def __init__(self, id):
        self._init_basics(id)
        self._init_attributes(id)
        self._init_skills_and_assistants(id)

    def _init_basics(self, id):
        mate_dict = hash_mates[id]

        self.name = mate_dict['name']
        self.nation = mate_dict['nation']
        self.image_x = mate_dict['image_x']
        self.image_y = mate_dict['image_y']

        self.exp = 0
        self.lv = mate_dict['lv']
        self.points = 0
        self.duty = None

    def _init_attributes(self, id):
        mate_dict = hash_mates[id]

        self.leadership = mate_dict['leadership']

        self.seamanship = mate_dict['seamanship']
        self.luck = mate_dict['luck']
        self.knowledge = mate_dict['knowledge']
        self.intuition = mate_dict['intuition']
        self.courage = mate_dict['courage']
        self.swordplay = mate_dict['swordplay']

    def _init_skills_and_assistants(self, id):
        mate_dict = hash_mates[id]

        # skills
        self.accounting = mate_dict['accounting']
        self.gunnery = mate_dict['gunnery']
        self.navigation = mate_dict['navigation']

        # assistants
        self.accountant = None
        self.first_mate = None
        self.chief_navigator = None

    def set_as_captain_of(self, ship):
        if not self.duty:
            if not ship.captain:
                ship.captain = self
                self.duty = ship

    def set_as_hand(self, position_name, role):
        if not self.duty:
            self.duty = position_name
            setattr(role, position_name, self)
            setattr(role.mates[0], position_name, self)

    def relieve_duty(self, role=''):
        # from hands
        if role:
            setattr(role, self.duty, None)
            setattr(role.mates[0], self.duty, None)
            self.duty = None

        # from captain
        else:
            if self.duty:
                self.duty.captain = None
                self.duty = None

    def get_exp(self, amount):
        self.exp += amount

    def add_lv(self):
        exp_needed_to_next_lv = lv_2_exp_needed_to_next_lv[self.lv]

        if self.exp >= exp_needed_to_next_lv and self.lv < c.MAX_LV:
            self.exp -= exp_needed_to_next_lv
            self.lv += 1
            self.points += 5

    def add_attribute(self, attribute_name):
        if self.points >= 1:
            self.points -= 1

            value = getattr(self, attribute_name)
            value += 1
            setattr(self, attribute_name, value)


class Discovery:
    def __init__(self, discovery_id):
        # get dic
        dic = villages_dict[discovery_id]

        # assign attributes
        self.name = dic['name']
        self.x = dic['x']
        self.y = dic['y']
        self.latitude = dic['latitude']
        self.longitude = dic['longitude']

        # not yet all done

            # defaults
        self.description = 'discovery description'
        self.image_x = random.randint(1, 16)
        self.image_y = random.randint(1, 5)

            # if have set
        if 'description' in dic:
            self.description = dic['description']
        if 'image_x' in dic:
            self.image_x = dic['image_x']
        if 'image_y' in dic:
            self.image_y = dic['image_y']

class Event:
    def __init__(self, id):
        dic = events_dict[id]

        # place where the event is triggered
        self.port = dic['port']
        self.building = dic['building']

        # sequences of dialogues
        self.dialogues = dic['dialogues']

        # figure image
        self.figure_images = dic['figure_images']

        # action if any
        self.action_to_perform = None
        if 'action_to_perform' in dic:
            self.action_to_perform = dic['action_to_perform']


class Bag:
    """owned by role, contains a list of item_ids"""
    def __init__(self, role):
        self.role = role
        if c.DEVELOPER_MODE_ON:
            self.container = {
                1:3,
                2:2,
                3:5,
                10:2,

                4:1,
                5:1,
                6:1,
                7:1,
                8:1,
                9:1,

                32:1,
                37:1,

                38:1,
                48:1,
            }
        else:
            self.container = {
                3: 1,
            }

    def add_item(self, item_id):
        if self.get_all_items_count() < c.MAX_ITEMS_IN_BAG:
            if item_id in self.container:
                self.container[item_id] += 1
            else:
                self.container[item_id] = 1
        else:
            print('max capacity reached!')


    def add_multiple_items(self, item_id, count):
        if (self.get_all_items_count() + count) <= c.MAX_ITEMS_IN_BAG:
            if item_id in self.container:
                self.container[item_id] += count
                return True
            else:
                self.container[item_id] = count
                return True
        else:
            print('max capacity reached!')
            return False

    def remove_item(self, item_id):
        if item_id in self.container:
            self.container[item_id] -= 1
            if self.container[item_id] == 0:
                del self.container[item_id]


    def get_all_items_count(self):
        count = 0

        for k in self.container.keys():
            count += self.container[k]

        return count

    def get_all_items_dict(self):
        return self.container

class Body:
    """where equipments reside"""
    def __init__(self):
        self.container = {
            'weapon': None,
            'armor': None,
            'instrument': None,
            'telescope': None,
            'watch': None,
            'pet': None,
        }

    def equip(self, item):
        self.container[item.type] = item.id

    def unequip(self, item):
        self.container[item.type] = None

    def get_all_equipments_dict(self):
        return self.container


class Item:
    """items  inside bag"""
    def __init__(self, id):
        self.id = id
        self.name = hash_items[id]['name']
        self.price = hash_items[id]['price']

        # image x, y
        self.image = [1, 1]
        if 'image' in hash_items[id]:
            self.image = hash_items[id]['image']

        # description
        self.description = 'description'
        if 'description' in  hash_items[id]:
            self.description = hash_items[id]['description']

        # effects
        if 'effects' in hash_items[id]:
            self.effects = hash_items[id]['effects']

        # effects_description
        if 'effects_description' in hash_items[id]:
            self.effects_description = hash_items[id]['effects_description']

        # type
        if 'type' in hash_items[id]:
            self.type = hash_items[id]['type']


class Port:
    """read only. holds a port's special items(ships, goods, items)"""

    def __init__(self, map_id, role=None):
        self.id = map_id + 1
        self.economy_id = hash_ports_meta_data[self.id]['economyId']
        self.name = hash_ports_meta_data[self.id]['name']
        self.x = hash_ports_meta_data[self.id]['x'] * c.PIXELS_COVERED_EACH_MOVE
        self.y = hash_ports_meta_data[self.id]['y'] * c.PIXELS_COVERED_EACH_MOVE

        if 'maid'in hash_ports_meta_data[self.id]:
            self.maid_id = hash_ports_meta_data[self.id]['maid']
        else:
            self.maid_id = None

        if role:
            self.economy = role.port_economy
            self.industry = role.port_industry


    def get_maid(self):
        if self.maid_id:
            maid = Maid(self.maid_id)
            return maid
        else:
            return None

    def get_available_ships(self):
        available_ships = hash_region_to_ships_available[self.economy_id]
        num_of_available_ships = len(available_ships)

        # get modifier
        modifier = None
        if self.industry >= 800:
            modifier = 1
        else:
            modifier = self.industry / 1000

        # get slice
        num_of_available_ships *= modifier
        num_of_available_ships = int(num_of_available_ships)
        available_ships = available_ships[:num_of_available_ships]

        return available_ships

    def get_availbale_goods_dict(self):
        # normal goods
        available_goods_dict = hash_markets_price_details[self.economy_id]['Available_items']
        temp_dict = copy.deepcopy(available_goods_dict)
        num_of_available_items = len(temp_dict)

        # get modifier
        modifier = None
        if self.economy >= 800:
            modifier = 1
        else:
            modifier = self.economy / 1000

        # get slice
        num_of_available_items *= modifier
        num_of_available_items = int(num_of_available_items)
        dic = dict(itertools.islice(temp_dict.items(), num_of_available_items))

        # special goods
        specialty_name = hash_special_goods[self.id]['specialty']
        buy_price = hash_special_goods[self.id]['price']
        if specialty_name != '0':
            dic[specialty_name] = [buy_price, 0]

        return dic

    def get_commodity_buy_price(self, commodity_name):
        buy_price = self.get_availbale_goods_dict()[commodity_name][0]
        return buy_price

    def get_commodity_sell_price(self, commodity_name):
        # normal
        sell_price = hash_markets_price_details[self.economy_id][commodity_name][1]

        # if it's special
        specialty_name = hash_special_goods[self.id]['specialty']
        if commodity_name == specialty_name:
            sell_price = int(sell_price * 0.3)

        return sell_price

    def get_available_items_ids_for_sale(self):
        id_list = hash_ports_meta_data[self.id]['itemShop']['regular']
        secret_id_list = hash_ports_meta_data[self.id]['itemShop']['secret']
        id_list.extend(secret_id_list)
        return id_list


class Path:
    """read only. holds path from one port to another"""
    def __init__(self, start_port_id, end_port_id):
        self.list_of_points = hash_paths[start_port_id][end_port_id]
        self.point_id = 0

    def get_next_point(self):
        if (self.point_id + 1) == len(self.list_of_points):
            pass
        else:
            self.point_id += 1

        point = self.list_of_points[self.point_id]

        return point

class Maid:
    def __init__(self, id):
        dic = hash_maids[id]
        self.name = dic['name']
        self.image = dic['image']


class Gun:
    def __init__(self, id):
        dic = hash_cannons[id]
        self.name = dic['name']
        self.price = dic['price']
        self.damage = dic['damage']


def init_one_default_npc(name):
    # now role
    npc = Role(14400, 4208, name)

    # add mate and ship
    mate0 = None
    if int(name) >= 50:
        mate0 = Mate(1)
        npc.mates.append(mate0)
    else:
        mate0 = Mate(int(name) + 4)
        npc.mates.append(mate0)

    # 3 types of fleet
    fleet_sequence = (int(name) - 1) % c.FLEET_COUNT_PER_NATION

    # merchant
    NUM_OF_SHIPS = 10
    if fleet_sequence == 0 or fleet_sequence == 1:
        cargo_name = _generate_rand_cargo_name()
        num_of_ships = random.randint(3, 5)
        ship_type = random.choice(['Nao', 'Carrack', 'Flemish Galleon', 'Buss', 'Sloop', 'Xebec'])
        for i in range(num_of_ships):
            ship = Ship(str(i), ship_type)
            ship.crew = int(ship.max_crew / 2)
            ship.add_cargo(cargo_name, ship.useful_capacity)
            npc.ships.append(ship)
            ship.captain = mate0

            # equipments
            armor = Item(35)
            weapon = Item(39)
            npc.body.equip(armor)
            npc.body.equip(weapon)

    # convoy
    elif fleet_sequence == 2 or fleet_sequence == 3:
        cargo_name = _generate_rand_cargo_name()
        num_of_ships = random.randint(5, 8)
        ship_type = random.choice([ 'Galleon', 'Venetian Galeass'])
        for i in range(num_of_ships):
            ship = Ship(str(i), ship_type)
            ship.gun = 4
            ship.crew = ship.max_crew
            ship.add_cargo(cargo_name, ship.useful_capacity)
            npc.ships.append(ship)
            ship.captain = mate0

            # equipments
            armor = Item(36)
            weapon = Item(43)
            npc.body.equip(armor)
            npc.body.equip(weapon)

    # battle
    else:
        cargo_name = _generate_rand_cargo_name()
        num_of_ships = random.randint(8, 10)
        ship_type = random.choice(['Frigate', 'Barge', 'Full Rigged Ship'])
        for i in range(num_of_ships):
            ship = Ship(str(i), ship_type)
            ship.gun = 6
            ship.crew = ship.max_crew
            ship.add_cargo(cargo_name, ship.useful_capacity)
            npc.ships.append(ship)
            ship.captain = mate0

            # equipments
            armor = Item(37)
            weapon = Item(48)
            npc.body.equip(armor)
            npc.body.equip(weapon)


    # diff based on nation
    for nation in nation_2_nation_id.keys():
        nation_id = nation_2_nation_id[nation]
        fleet_id_list_for_one_nation = list(range((nation_id - 1) * c.FLEET_COUNT_PER_NATION + 1,
                                                  nation_id * c.FLEET_COUNT_PER_NATION + 1))
        if int(name) >= fleet_id_list_for_one_nation[0] and int(name) <= fleet_id_list_for_one_nation[-1]:
            npc.mates[0].nation = nation
            capital = nation_2_capital[nation]
            npc.start_port_id = capital_2_port_id[capital]

    # test all england
    # npc.mates[0].nation = 'England'
    # npc.start_port_id = capital_2_port_id['london']

    port = Port((npc.start_port_id - 1))
    npc.x = port.x
    npc.y = port.y
    npc.map = 'sea'


    # ret
    return npc

def _generate_rand_cargo_name():
    cargoes = hash_markets_price_details[0]
    cargo_names = list(cargoes.keys())
    cargo_name = random.choice(cargo_names)

    if cargo_name == 'Available_items':
        cargo_name = 'Gold'

    return cargo_name

def exit_battle(self, message_obj):
    """self is server echo"""
    if not type(self) is Role:
        if self.my_role.is_in_battle():
            # if enemy is npc
            if self.my_role.is_enemy_npc():
                _exit_battle_when_enemy_is_npc(self)
            # if enemy is player
            else:
                _exit_battle_when_enemy_is_player(self)

def _exit_battle_when_enemy_is_player(self):
    # gets
    enemy_name = self.my_role.enemy_name
    battle_map = self.factory.aoi_manager.get_map_by_player(self.my_role)
    all_players_in_battle = battle_map.get_all_players_inside()
    enemy_conn = all_players_in_battle[enemy_name]
    enemy_role = enemy_conn.my_role
    my_role = self.my_role
    my_previous_map = self.my_role.map

    # sets
    my_role.map = 'sea'
    enemy_role.map = 'sea'

    # change map states
    self.factory.aoi_manager.delete_battle_map_by_name(my_previous_map)

    sea_map = self.factory.aoi_manager.get_map_by_player(self.my_role)
    sea_map.add_player_conn(self)
    sea_map.add_player_conn(enemy_conn)

    # send roles_in_new_map to my client and enemy client
    my_nearby_players = sea_map.get_nearby_players_by_player(self.my_role)
    roles_in_new_map = {}
    for name, conn in my_nearby_players.items():
        if name.isdigit():
            roles_in_new_map[name] = conn
        else:
            roles_in_new_map[name] = conn.my_role
    roles_in_new_map[my_role.name] = my_role
    self.send('roles_in_new_map', roles_in_new_map)
    enemy_conn.send('roles_in_new_map', roles_in_new_map)

    # send new role message to other roles in new map
    new_roles_from_battle = {}
    new_roles_from_battle[self.my_role.name] = self.my_role
    new_roles_from_battle[enemy_role.name] = enemy_role

    del my_nearby_players[enemy_role.name]
    for name, conn in my_nearby_players.items():
        if name.isdigit():
            pass
        else:
            conn.send('new_roles_from_battle', new_roles_from_battle)

def _exit_battle_when_enemy_is_npc(self):
    # gets
    enemy_name = self.my_role.enemy_name
    enemy_role = self.factory.npc_manager.get_npc_by_name(enemy_name)
    my_role = self.my_role
    my_previous_map = self.my_role.map

    # sets
    my_role.map = 'sea'
    enemy_role.map = 'sea'

    # change map states
    self.factory.aoi_manager.delete_battle_map_by_name(my_previous_map)

    sea_map = self.factory.aoi_manager.get_map_by_player(my_role)
    sea_map.add_player_conn(self)

    # npc gets back strength
    new_enemy_role = _generate_new_npc_after_battle(my_role, enemy_role)
    sea_map.add_npc(new_enemy_role)

    # send roles_in_new_map to my client
    nearby_players = sea_map.get_nearby_players_by_player(my_role)
    roles_in_new_map = {}
    for name, conn in nearby_players.items():
        if name.isdigit():
            roles_in_new_map[name] = conn
        else:
            roles_in_new_map[name] = conn.my_role
    roles_in_new_map[my_role.name] = my_role
    self.send('roles_in_new_map', roles_in_new_map)

    # send new role message to other roles in new map
    new_roles_from_battle = {}
    new_roles_from_battle[my_role.name] = my_role
    new_roles_from_battle[enemy_role.name] = new_enemy_role

    for name, conn in nearby_players.items():
        if name.isdigit():
            pass
        else:
            conn.send('new_roles_from_battle', new_roles_from_battle)

def _generate_new_npc_after_battle(my_role, enemy_role):
    # npc lost
    if my_role.ships and not enemy_role.ships:
        enemy_name = enemy_role.name
        Role.FACTORY.npc_manager.npcs[enemy_name] = init_one_default_npc(enemy_name)
        new_npc = Role.FACTORY.npc_manager.get_npc_by_name(enemy_name)
        return new_npc
    # tie / npc won
    else:
        for ship in enemy_role.ships:
            ship.now_hp = ship.max_hp
            ship.crew = ship.max_crew

    return enemy_role

if __name__ == '__main__':
    # new role
    pass





