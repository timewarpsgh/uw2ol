import random
import time
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

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))


class Role:
    """
    contains portable data for a player (transmitted from DB to server to client)
    and setters(also protocols sent to and from server)
    must only pass one argument called params(a list)

    """

    # in server
    users = None

    # in client
    GAME = None

    def __init__(self, x, y, name, gold=2000):

        # basics
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
        self.in_building_type = None
        self.battle_timer = 0
        self.your_turn_in_battle = True
        self.max_days_at_sea = 0
        self.additioanl_days_at_sea = 0
        self.speak_msg = ''
        self.gold = gold
        self.bank_gold = 2000
        self.target_name = ''

        # assistants
        self.accountant = None
        self.first_mate = None
        self.chief_navigator = None

        # quests (3 types)
        self.quest_discovery = None
        self.quest_trade = None
        self.quest_fight = None

        # other classes i contain
        self.ships = []
        self.mates = []
        self.discoveries = {}
        self.bag = Bag(self)
        self.body = Body()

        # main events sequence
        self.main_events_ids = list(range(1, len(events_dict) + 1))
        self.main_events_ids = list(reversed(self.main_events_ids))

        # conn
        self.conn = None

        # set at client, when client first gets role from server(when got packet 'your_role_data')
        self.in_client = False

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
            self.main_events_ids.pop()

    def _get_other_role_by_name(self, name):

        # in client
        if self.GAME:
            if name in self.GAME.other_roles:
                target_role = self.GAME.other_roles[name]
                print("target is:", target_role.name)
                return target_role
            else:
                print("target is:", self.GAME.my_role.name)
                return self.GAME.my_role

        # in server
        else:
            # npc
            if str(name).isdigit():
                target_role = Role.users[self.map][name]
                return target_role

            # player
            else:
                target_role = Role.users[self.map][name].my_role
                return target_role

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
        reactor.callLater(1, self._speak_clear_msg)

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

    def unequip(self, params):
        item_id = params[0]

        item = Item(item_id)
        self.body.unequip(item)
        self.bag.add_item(item_id)

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


    def move(self, params):
        direction = params[0]

        # basic 4 directions
        if direction == 'up':
            self.y -= c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'up'
        elif direction == 'down':
            self.y += c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'down'
        elif direction == 'left':
            self.x -= c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'left'
        elif direction == 'right':
            self.x += c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'right'
        # additional 4 directions
        elif direction == 'ne':
            self.y -= c.PIXELS_COVERED_EACH_MOVE
            self.x += c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'ne'
        elif direction == 'nw':
            self.y -= c.PIXELS_COVERED_EACH_MOVE
            self.x -= c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'nw'
        elif direction == 'se':
            self.y += c.PIXELS_COVERED_EACH_MOVE
            self.x += c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'se'
        elif direction == 'sw':
            self.y += c.PIXELS_COVERED_EACH_MOVE
            self.x -= c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'sw'

        # change image
        self.person_frame *= -1

        # east and west edge detection
        if self.map == 'sea':
            if self.x < 160:
                self.x = c.WORLD_MAP_X_LENGTH -160
            if self.x > c.WORLD_MAP_X_LENGTH - 160:
                self.x = 160

        # prints
        # print("now x:", self.x)
        # print("new y:", self.y)
        # print("new direction:", self.direction)

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
            y = int(self.x / 16)
            x = int(self.y / 16)

            # basic 4 directions
            if direction == 'up':
                if int(piddle[x - 1, y]) in c.SAILABLE_TILES:
                    return True
            elif direction == 'down':
                if int(piddle[x + 2, y]) in c.SAILABLE_TILES:
                    return True
            elif direction == 'left':
                if int(piddle[x + 1, y - 1]) in c.SAILABLE_TILES:
                    return True
            elif direction == 'right':
                if int(piddle[x + 1, y + 2]) in c.SAILABLE_TILES:
                    return True

            # additional 4 directions
            elif direction == 'ne':
                if int(piddle[x - 1, y + 1]) in c.SAILABLE_TILES:
                    return True
            elif direction == 'nw':
                if int(piddle[x - 1, y - 1]) in c.SAILABLE_TILES:
                    return True
            elif direction == 'se':
                if int(piddle[x + 1, y + 1]) in c.SAILABLE_TILES:
                    return True
            elif direction == 'sw':
                if int(piddle[x + 1, y - 1]) in c.SAILABLE_TILES:
                    return True

            # ret
            return False

    def get_port(self):
        map_id = int(self.map)
        port = Port(map_id)
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

    def add_mates_attribute(self, params):
        mate_num = params[0]
        attribute = params[1]

        mate = self.mates[mate_num]
        mate.add_attribute(attribute)

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

    # at sea
    def discover(self, params):
        # discovery_id = random.randint(0, 10)
        discovery_id = params[0]
        if discovery_id in self.discoveries:
            if self.is_in_client_and_self():
                self.GAME.button_click_handler.make_message_box("Have seen this.")
        else:
            if self.quest_discovery == discovery_id or True:
                self.discoveries[discovery_id] = 1
                self.mates[0].exp += 100

                # give random item
                rand_seed_num = self.x + self.y + discovery_id
                random.seed(rand_seed_num)
                item_id = random.choice(range(1,len(hash_items) + 1))
                self.bag.add_item(item_id)

                if self.is_in_client_and_self():
                    discovery = Discovery(discovery_id)
                    item = Item(item_id)
                    self.GAME.button_click_handler.make_message_box(f'We found {discovery.name} and {item.name}!')
            else:
                if self.is_in_client_and_self():
                    self.GAME.button_click_handler.make_message_box("Can't find anything.")

    def enter_battle_with(self, params):

        # enemy
        enemy_name = params[0]
        enemy_role = self._get_other_role_by_name(enemy_name)
        enemy_role.map = 'battle'
        enemy_role.target_name = self.name
        enemy_role.battle_timer = 0

        # me
        self.map = 'battle'
        self.battle_timer = 50
        self.target_name = enemy_name

        # timer
        timer = Timer(1, self._change_battle_timer, args=[enemy_role])
        timer.start()

    def _change_battle_timer(self, enemy_role):

        # while in battle
        while self.map == 'battle':

            # self
            if self.battle_timer > 0:
                self.battle_timer -= 1
                if self.battle_timer == 0:
                    enemy_role.battle_timer = 50

            # enemy
            if enemy_role.battle_timer > 0:
                enemy_role.battle_timer -= 1
                if enemy_role.battle_timer == 0:
                    self.battle_timer = 50

            # sleep 1s
            time.sleep(1)

    # def _exit_battle(self):
    #     self.map = 'sea'
    #     target_role = self._get_other_role_by_name(self.target_name)
    #     target_role.map = 'sea'

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
        if my_ship.attack_method is None or my_ship.attack_method == 'shoot':
            d_dead = my_ship.try_to_shoot(target_ship)
        elif my_ship.attack_method == 'engage':
            d_dead = my_ship.try_to_engage(target_ship)

        d_dead.addCallback(self._call_back_for_shoot_or_engage, enemy_ships, target_ship_id, deferred)

        # ret deferred
        return deferred

    def _call_back_for_shoot_or_engage(self, d_dead, enemy_ships, target_ship_id, deferred):

        # target dead
        if d_dead:
            if enemy_ships[target_ship_id].now_hp <= 0:
                del enemy_ships[target_ship_id]

            # if flag ship dead
            if target_ship_id == 0:
                # all enemy mates relieve duty
                enemy_role = self._get_other_role_by_name(self.enemy_name)
                for mate in enemy_role.mates:
                    if mate.duty in ['accountant', 'first_mate', 'chief_navigator']:
                        mate.relieve_duty(enemy_role)
                    else:
                        mate.relieve_duty()

                # get all enemy ships
                self.ships.extend(enemy_ships)
                enemy_ships.clear()

                # get all enemy gold
                self.gold += enemy_role.gold
                enemy_role.gold = 0
                print('battle ended. press e to exit battle.')

                # if enemy is npc
                if str(enemy_role.name).isdigit():
                    # npc rebirth
                    if self.is_in_server():
                        Role.users['sea']['npcs'].npcs[enemy_role.name] = init_one_default_npc(enemy_role.name)

                # if i am npc and enemy is player
                if self.is_npc() and not enemy_role.is_npc():
                    if self.is_in_server():
                        new_role = init_one_default_npc(self.name)
                        new_role.x = self.x
                        new_role.y = self.y
                        Role.users['sea']['npcs'].npcs[self.name] = new_role

                deferred.callback(False)
                # return deferred
            else:
                deferred.callback('next_ship')
                # return deferred

        # not dead
        else:
            deferred.callback('next_ship')
            # return deferred

    def all_ships_operate(self, params):

        if self.your_turn_in_battle:

            # all ships know my_role
            Ship.ROLE = self

            # get my and enemy ships
            enemy_ships = self._get_other_role_by_name(self.enemy_name).ships
            my_ships = self.ships

            print(enemy_ships)

            # flag ship attacks
            self._pick_one_ship_to_attack([0, enemy_ships])

            # stop my turn
            self.your_turn_in_battle = False

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

        for ship in self.ships:
            ship.attack_method = attack_method

    def _change_turn(self):
        self._get_other_role_by_name(self.enemy_name).your_turn_in_battle = True

    def _pick_one_ship_to_attack(self, params):
        # get params
        i = params[0]
        enemy_ships = params[1]

        # pick

            # calculate random target id
        rand_seed_num = enemy_ships[0].now_hp + len(enemy_ships)
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
                print("target id:", random_target_ship_id)

        # attack
        d_result = self.attack_ship([i, random_target_ship_id])
        d_result.addCallback(self._call_back_for_attack_ship, i, enemy_ships)

    def _call_back_for_attack_ship(self, result, i, enemy_ships):
        # not won
        if result == 'next_ship':
            # if self lost all crew:
            if self.ships[0].crew <= 0:
                # lose all my ships
                enemy_ships.extend(self.ships)
                self.ships.clear()

                # exit if in client and have ships left (the winner sends exit_battle message to server)
                if Role.GAME and Role.GAME.my_role.ships:
                    reactor.callLater(1, Role.GAME.connection.send, 'exit_battle', [])

            # else
            else:
                # my next ship
                if (i+1) <= (len(self.ships) - 1):
                    reactor.callLater(1, self._pick_one_ship_to_attack, [i+1, enemy_ships])
                # enemy turn
                else:
                    reactor.callLater(1, self._change_turn)
        # won battle
        else:
            # player won
            if Role.GAME and Role.GAME.my_role.ships:
                reactor.callLater(1, Role.GAME.connection.send, 'exit_battle', [])

            # server controled npc won
            if self.is_in_server() and self.is_npc():
                enemy_conn = Role.users[self.map][self.enemy_name]
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
                    self.ships.append(ship)
                    self.gold -= ship.price

                    print('now ships:', len(self.ships))

    def sell_ship(self, params):
        num = params[0]

        if self.ships[num] and len(self.ships) >= 2:
            self.gold += int(self.ships[num].price / 2)
            if self.ships[num].captain:
                self.ships[num].captain.relieve_duty()
            del self.ships[num]
            print('now ships:', len(self.ships))

    def repair_all(self, params):
        for ship in self.ships:
            ship.now_hp = ship.max_hp

    def remodel_ship_capacity(self, params):
        ship_num = params[0]
        max_crew = params[1]
        max_guns = params[2]

        self.ships[ship_num].remodel_capacity(max_crew, max_guns)

    # bar
    def hire_crew(self, params):
        count = params[0]
        to_which_ship = params[1]

        ship = self.ships[to_which_ship]
        # if can hold crew
        if ship.crew + count <= ship.max_crew:
            ship.add_crew(count)
            print(self.name, "ship", to_which_ship, "now has crew:", self.ships[to_which_ship].crew)

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
                self.GAME.button_click_handler.make_message_box("Lv too low.")
                self.GAME.button_click_handler.make_message_box("Lv too low.")
            return

        # leadership must be enough
        if int(self.mates[0].leadership / 10) <= len(self.mates):
            if self.is_in_client_and_self():
                self.GAME.button_click_handler.make_message_box("Leadership not enough.")
                self.GAME.button_click_handler.make_message_box("Leadership not enough.")
            return

        # can't hire same mate twice
        for mate_t in self.mates:
            if mate_t.name == name:
                print('have this guy already.')
                if self.is_in_client_and_self():
                    self.GAME.button_click_handler.make_message_box("Already have this guy.")
                    self.GAME.button_click_handler.make_message_box("Already have this guy.")
                return


        # do hire
        self.mates.append(mate)

        print('now mates:', len(self.mates))

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

        buy_price_modifier = (100 - (mate.knowledge + mate.accounting * 20) / 4) / 100
        return buy_price_modifier

    def get_sell_price_modifier(self):
        mate = None
        if self.accountant:
            mate = self.accountant
        else:
            mate = self.mates[0]

        sell_price_modifier = (50 + mate.intuition + mate.accounting * 10) / 100
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
                # add cargo
                ship.add_cargo(cargo_name, count)

                # cut gold
                unit_price = port.get_commodity_buy_price(cargo_name)
                buy_price_modifier = self.get_buy_price_modifier()
                unit_price = int(unit_price * buy_price_modifier)

                # has tax permit
                if c.TAX_FREE_PERMIT_ID in self.bag.get_all_items_dict():
                    self.gold -= count * unit_price
                    self.bag.remove_item(c.TAX_FREE_PERMIT_ID)
                else:
                    self.gold -= int(count * unit_price * 1.2)

                print(self.name, "ship", to_which_ship, "cargoes", self.ships[to_which_ship].cargoes)
                print(self.name, "gold:", self.gold)

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
                self.gold += count * unit_price

                # add exp
                self.mates[0].exp += int(count * unit_price / 100)

                print(self.name, "ship", from_which_ship, "cargoes", self.ships[from_which_ship].cargoes)
                print(self.name, "gold:", self.gold)

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
            self.mates[0].exp += 100
            self.gold += 5000
            self.quest_discovery = None

            # client does
            if self.is_in_client_and_self():
                self.GAME.button_click_handler.make_message_box("Quest complete!")

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
            self.bag.remove_item(item_id)
            item = Item(item_id)
            self.gold += int(item.price / 2)

    def buy_items(self, params):
        item_id = params[0]
        count = params[1]

        now_port = Port(int(self.map))
        if item_id in now_port.get_available_items_ids_for_sale():
            total_charge = Item(item_id).price * count
            if self.gold >= total_charge:
                if self.bag.add_multiple_items(item_id, count):
                    self.gold -= total_charge


class Ship:
    ROLE = None
    shooting_img = ''

    def __init__(self, name, type):
        # necessary params
        self.name = name
        self.type = type

        # init from hash
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

        # others
        self.useful_capacity = self.capacity - self.max_guns - self.max_crew
        self.x = 10
        self.y = 10
        self.direction = 'up'
        self.target = None
        self.attack_method = None
        self.state = ''
        self.damage_got = ''

        # mate
        self.captain = None

        # crew
        self.crew = 5

        # cargo and supply
        self.cargoes = {}
        self.supplies = {
            'Food':20,
            'Water':20,
            'Lumber':0,
            'Shot':0
        }

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

            return speed
        # no captain
        else:
            return 1

    def move(self, direction):
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

        # collide with any of my ships?
        for ship in Ship.ROLE.ships:
            if ship.x == future_x and ship.y == future_y:
                return False

        # collide with any of enemy ships?
        enemy_name = Ship.ROLE.enemy_name
        enemy_role = Ship.ROLE._get_other_role_by_name(enemy_name)
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
        self.steps_left = c.MAX_STEPS_IN_BATTLE

        # check
        if ship.crew > 0 and self.crew > 0:
            self.shoot_or_move_closer(ship, deferred)
        else:
            deferred.callback(False)

        # ret
        return deferred

    def shoot_or_move_closer(self, ship, deferred):
        # if in range
        if abs(self.x - ship.x) + abs(self.y - ship.y) <= c.SHOOT_RANGE_IN_BATTLE:
            # engage
            result = self.shoot(ship)

            # call back
            deferred.callback(result)

        # not in range
        else:
            # move closer
            moved = self.move_closer(ship, deferred)

            if moved:
                # if have steps
                if self.steps_left >= 1:
                    reactor.callLater(0.5, self.shoot_or_move_closer, ship, deferred)
                # no more steps
                else:
                    deferred.callback(False)

    def move_closer(self, ship, deferred):
        if self.x < ship.x:
            if self.can_move('right'):
                self.move('right')
            elif self.can_move('up'):
                self.move('up')
            elif self.can_move('down'):
                self.move('down')
            else:
                deferred.callback(False)
                return False
        elif self.x > ship.x:
            if self.can_move('left'):
                self.move('left')
            elif self.can_move('up'):
                self.move('up')
            elif self.can_move('down'):
                self.move('down')
            else:
                deferred.callback(False)
                return False

        elif self.y < ship.y:
            if self.can_move('down'):
                self.move('down')
            elif self.can_move('left'):
                self.move('left')
            elif self.can_move('right'):
                self.move('right')
            else:
                deferred.callback(False)
                return False
        elif self.y > ship.y:
            if self.can_move('up'):
                self.move('up')
            elif self.can_move('left'):
                self.move('left')
            elif self.can_move('right'):
                self.move('right')
            else:
                deferred.callback(False)
                return False

        return True

    def shoot(self, ship):
        # change states
        self.state = 'shooting'
        reactor.callLater(1, self._clear_shooting_state, ship)

        # damage based on attributes
        damage = 0
            # if no first mate
        if not self.captain.first_mate:
            damage = c.SHOOT_DAMAGE * int((self.max_guns + int(self.captain.swordplay / 2) + self.captain.gunnery * 20) / 10)
            # if have first mate
        else:
            damage = c.SHOOT_DAMAGE * int(
                (self.max_guns + int(self.captain.first_mate.swordplay / 2) + self.captain.first_mate.gunnery * 20) / 10)

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

        ship.now_hp -= damage
        ship.damage_got = str(damage)

        # no negative hp
        if ship.now_hp < 0:
            ship.now_hp = 0

        # ret
        return ship.now_hp <= 0

    def engage(self, ship):
        # change states
        self.state = 'engaging'
        ship.state = 'engaged'
        reactor.callLater(1, self._clear_state, ship)

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

        # self.damage_got = str(c.ENGAGE_DAMAGE)
        # ship.damage_got = str(c.ENGAGE_DAMAGE)

        # no negative values
        if self.crew < 0:
            self.crew = 0
        if ship.crew < 0:
            ship.crew = 0

        # ret
        return ship.crew <= 0

    def try_to_engage(self, ship):
        """returns a deferred"""
        # inits a deffered
        deferred = defer.Deferred()

        # init max steps
        self.steps_left = c.MAX_STEPS_IN_BATTLE

        # check
        if ship.crew > 0 and self.crew > 0:
            self.engage_or_move_closer(ship, deferred)
        else:
            deferred.callback(False)

        # ret
        return deferred

    def engage_or_move_closer(self, ship, deferred):
        # if in range
        if abs(self.x - ship.x) <= 1 and abs(self.y - ship.y) <= 1:
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
                    reactor.callLater(0.5, self.engage_or_move_closer, ship, deferred)
                # no more steps
                else:
                    deferred.callback(False)

    def _clear_shooting_state(self, ship):
        self.state = ''
        ship.state = 'shot'
        reactor.callLater(0.3, self._clear_state, ship)

    def _clear_state(self, ship):
        self.state = ''
        ship.state = ''

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
        mate_dict = hash_mates[id]

        # basics
        self.name = mate_dict['name']
        self.nation = mate_dict['nation']

        self.image_x = mate_dict['image_x']
        self.image_y = mate_dict['image_y']

        self.exp = 0
        self.lv = mate_dict['lv']

        self.duty = None

        self.points = 0

        # attributes
        self.leadership = mate_dict['leadership']

        self.seamanship = mate_dict['seamanship']
        self.luck = mate_dict['luck']
        self.knowledge = mate_dict['knowledge']
        self.intuition = mate_dict['intuition']
        self.courage = mate_dict['courage']
        self.swordplay = mate_dict['swordplay']

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
        if self.exp >= 100:
            self.exp -= 100
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

    def __init__(self, map_id):
        self.id = map_id + 1
        self.economy_id = hash_ports_meta_data[self.id]['economyId']
        self.name = hash_ports_meta_data[self.id]['name']

    def get_available_ships(self):
        available_ships = hash_region_to_ships_available[self.economy_id]
        return available_ships

    def get_availbale_goods_dict(self):
        # normal goods
        available_goods_dict = hash_markets_price_details[self.economy_id]['Available_items']

        # special goods
        specialty_name = hash_special_goods[self.id]['specialty']
        buy_price = hash_special_goods[self.id]['price']
        if specialty_name != '0':
            available_goods_dict[specialty_name] = [buy_price, 0]

        return available_goods_dict

    def get_commodity_buy_price(self, commodity_name):
        buy_price = self.get_availbale_goods_dict()[commodity_name][0]
        return buy_price

    def get_commodity_sell_price(self, commodity_name):
        sell_price = hash_markets_price_details[self.economy_id][commodity_name][1]
        return sell_price

    def get_available_items_ids_for_sale(self):
        id_list = hash_ports_meta_data[self.id]['itemShop']['regular']
        return id_list


def init_one_default_npc(name):
    # now role
    npc = Role(14400, 4208, name)
    npc.map = 'sea'

    # add mate and ship
    mate0 = Mate(1)
    ship0 = Ship('Reagan', 'Frigate')
    ship0.crew = 20
    npc.ships.append(ship0)
    mate0.set_as_captain_of(ship0)
    npc.mates.append(mate0)

    mate1 = Mate(2)
    ship1 = Ship('Reagan1', 'Frigate')
    ship1.crew = 20
    npc.ships.append(ship1)
    mate1.set_as_captain_of(ship1)
    npc.mates.append(mate1)

    # ret
    return npc

def exit_battle(self, message_obj):
    """self is server echo"""
    # if enemy is npc
    if self.my_role.is_enemy_npc():
        _exit_battle_when_enemy_is_npc(self)
    # if enemy is player
    else:
        _exit_battle_when_enemy_is_player(self)

def _exit_battle_when_enemy_is_player(self):
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
        if name == 'npcs':
            for npc_name, npc in self.factory.users['sea'][name].npcs.items():
                roles_in_new_map[npc_name] = npc
        else:
            roles_in_new_map[name] = conn.my_role

    self.send('roles_in_new_map', roles_in_new_map)
    enemy_conn.send('roles_in_new_map', roles_in_new_map)

    # send new role message to other roles in new map
    new_roles_from_battle = {}
    new_roles_from_battle[self.my_role.name] = self.my_role
    new_roles_from_battle[enemy_role.name] = enemy_role

    for name, conn in self.factory.users['sea'].items():
        if name != enemy_name and name != self.my_role.name and name != 'npcs':
            conn.send('new_roles_from_battle', new_roles_from_battle)

def _exit_battle_when_enemy_is_npc(self):
    # gets
    enemy_name = self.my_role.enemy_name
    enemy_role = self.factory.users[self.my_role.map][enemy_name]
    my_role = self.my_role
    my_previous_map = self.my_role.map

    # sets
    my_role.map = 'sea'
    enemy_role.map = 'sea'

    # change users dict state
    del self.factory.users[my_previous_map]
    print(self.factory.users)

    self.factory.users['sea'][my_role.name] = self

    # send roles_in_new_map to my client and enemy client
    roles_in_new_map = {}
    for name, conn in self.factory.users['sea'].items():
        if name == 'npcs':
            for npc_name, npc in self.factory.users['sea'][name].npcs.items():
                roles_in_new_map[npc_name] = npc
        else:
            roles_in_new_map[name] = conn.my_role

    self.send('roles_in_new_map', roles_in_new_map)

    # send new role message to other roles in new map
    new_roles_from_battle = {}
    new_roles_from_battle[self.my_role.name] = self.my_role
    if enemy_role.ships:
        new_roles_from_battle[enemy_role.name] = self.factory.users['sea']['npcs'].npcs[enemy_role.name]
    else:
        new_roles_from_battle[enemy_role.name] = self.factory.users['sea']['npcs'].npcs[enemy_role.name]

    for name, conn in self.factory.users['sea'].items():
        if name != enemy_name and name != self.my_role.name and name != 'npcs':
            conn.send('new_roles_from_battle', new_roles_from_battle)

if __name__ == '__main__':
    # new role
    alex = init_one_default_npc('alex')
    print(alex.name)





