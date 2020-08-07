import random
import time
from threading import Timer
from twisted.internet import reactor, task, defer
import constants as c
from hashes.hash_ship_name_to_attributes import hash_ship_name_to_attributes
from port import Port

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
        self.x = x
        self.y = y
        self.direction = None
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
        self.days_spent_at_sea = 0
        self.speak_msg = ''
        self.gold = gold
        self.target_name = ''
        self.ships = []
        self.mates = []
        self.discoveries = {}

        self.conn = None

        # set at client, when client first gets role from server(when got packet 'your_role_data')
        self.in_client = False

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
            target_role = Role.users[self.map][name].my_role
            return target_role

    # anywhere

    def _check_days_at_sea_timer(self):
        while True:
            time.sleep(3)
            self.days_spent_at_sea += 1

            if self.days_spent_at_sea > self.max_days_at_sea:
                self.map = 'port'
                print('your fleet starved to death!')
                break

            if self.map.isdigit():
                break

    def _count_max_days_at_sea(self):

        total_crew = 0
        total_water = 0
        total_food = 0

        for ship in self.ships:
            total_crew += ship.crew
            total_water += ship.supplies['Water']
            total_food += ship.supplies['Food']

        total_supply = min(total_food, total_water)
        max_days_at_sea = int(total_supply / (total_crew * SUPPLY_CONSUMPTION_PER_DAY_PER_PERSON))

        print("max days at sea:", max_days_at_sea)
        return max_days_at_sea

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

        self.person_frame *= -1

        print("now x:", self.x)
        print("new y:", self.y)
        print("new direction:", self.direction)

    def can_move(self, direction):
        # in port
        if self.map.isdigit():

            # get piddle
            piddle = self.GAME.port_piddle

            # perl piddle and python numpy(2d array) are different
            y = int(self.x / 16)
            x = int(self.y / 16)

            # directions
            if direction == 'up':
                if piddle[x, y] in c.WALKABLE_TILES and piddle[x, y + 1] in c.WALKABLE_TILES:
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

            # directions
            if direction == 'up':
                if int(piddle[x - 1, y]) in c.WALKABLE_TILES:
                    return True
            elif direction == 'down':
                if int(piddle[x + 2, y]) in c.WALKABLE_TILES:
                    return True
            elif direction == 'left':
                if int(piddle[x + 1, y - 1]) in c.WALKABLE_TILES:
                    return True
            elif direction == 'right':
                if int(piddle[x + 1, y + 2]) in c.WALKABLE_TILES:
                    return True

            # ret
            return False

    def get_port(self):
        map_id = int(self.map)
        port = Port(map_id)
        return port

    def calculate_max_days_at_sea(self):
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

        # ret
        return max_days

    # at sea
    def discover(self, params):
        discovery_id = random.randint(0, 10)
        if discovery_id in self.discoveries:
            print(self.name, "have seen this")
        else:
            self.discoveries[discovery_id] = 1
            print(self.name, "found new stuff. now discoveris:", self.discoveries)

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

    def _exit_battle(self):
        self.map = 'sea'
        target_role = self._get_other_role_by_name(self.target_name)
        target_role.map = 'sea'

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
                self.ships.extend(enemy_ships)
                enemy_ships.clear()
                print('battle ended. press e to exit battle.')

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
            # exit
            if Role.GAME and Role.GAME.my_role.ships:
                reactor.callLater(1, Role.GAME.connection.send, 'exit_battle', [])


    # ship yard
    def buy_ship(self, params):
        name = params[0]
        type = params[1]

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

        if self.ships[num]:
            self.gold += int(self.ships[num].price / 2)
            del self.ships[num]
            print('now ships:', len(self.ships))

    def repair_all(self, params):
        for ship in self.ships:
            ship.now_hp = ship.max_hp

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
        name = params[0]
        nation = params[1]

        mate = Mate(name, nation)
        self.mates.append(mate)

        print('now mates:', len(self.mates))

    def fire_mate(self, params):
        num = params[0]

        del self.mates[num]
        print('now mates:', len(self.mates))

    # market
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
                self.gold -= count * unit_price

                print(self.name, "ship", to_which_ship, "cargoes", self.ships[to_which_ship].cargoes)
                print(self.name, "gold:", self.gold)

    def sell_cargo(self, params):
        cargo_name = params[0]
        count = params[1]
        from_which_ship = params[2]

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
                self.gold += count * unit_price

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

class Ship:
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

        # change values
        ship.now_hp -= c.SHOOT_DAMAGE
        ship.damage_got = str(c.SHOOT_DAMAGE)

        # no negatives values
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
        self.crew -= c.ENGAGE_DAMAGE
        ship.crew -= c.ENGAGE_DAMAGE
        self.damage_got = str(c.ENGAGE_DAMAGE)
        ship.damage_got = str(c.ENGAGE_DAMAGE)

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
    def __init__(self, name, nation):
        self.name = name
        self.nation = nation


class Cargo:
    def __init__(self, name, count):
        self.name = name
        self.count = count


# contains role and other visual client side stuff (only exists in client)
class Player:
    ship_in_battle_img = None

    def __init__(self, role):
        self.role = role
        self.role_img = None
        self.name_img = None
        self.speak_img = None
        self.logged_in = False


if __name__ == '__main__':
    role = Role(5, 5, 'test_name')
    a = {}
    print(type(role.map))
    a[role.map] = 123
    print(a)