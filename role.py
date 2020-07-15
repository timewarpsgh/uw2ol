import random
import time
from threading import Timer
from twisted.internet import reactor, task
import constants as c

SUPPLY_CONSUMPTION_PER_DAY_PER_PERSON = 1

# contains portable data for a player (transmitted from DB to server to client)
# and setters(also protocols sent to and from server)
# must only pass one argument called params(a list)
class Role:

    # set at client, when client first gets role from server(when got packet 'your_role_data')
    g_all_players = None

    # set at server, when server first got connection from a client
    g_conn_pool = None

    # set at server, when server first got name of player
    g_name_to_socket_pool = None

    # in server
    users = None

    # in client
    Game = None

    def __init__(self, x, y, name, gold=2000):
        self.x = x
        self.y = y
        self.direction = None
        self.moving = False
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
        if self.in_client:
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
    def change_map(self, params):
        map_name = params[0]
        self.map = map_name

        print("map changed to sea!")
        # if to sea
        if map_name == 'sea':
            pass
            # # reset days at sea
            # self.max_days_at_sea = self._count_max_days_at_sea()
            # self.days_spent_at_sea = 0
            #
            # # sea days check timer
            # timer = Timer(1, self._check_days_at_sea_timer)
            # timer.start()

        # if to port
        elif map_name.isdigit():
            pass

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
                    return True
            elif direction == 'down':
                if piddle[x + 2, y] in c.WALKABLE_TILES and piddle[x + 2, y + 1] in c.WALKABLE_TILES:
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

    def shoot_ship(self, params):

        # get ids
        my_ship_id = params[0]
        target_ship_id = params[1]

        # get ships
        my_ship = self.ships[my_ship_id]
        enemy_ships = self._get_other_role_by_name(self.enemy_name).ships
        target_ship = enemy_ships[target_ship_id]

        print("started shooting")
        # shoot
        dead = my_ship.shoot(target_ship)
        if dead:
            del enemy_ships[target_ship_id]

            # if flag ship dead
            if target_ship_id == 0:
                self.ships.extend(enemy_ships)
                enemy_ships.clear()
                print('battle ended. press e to exit battle.')

    def all_ships_operate(self, params):

        # if timer > 1
        # if self.battle_timer > 1:

        if self.your_turn_in_battle:

            # get my and enemy ships
            enemy_ships = self._get_other_role_by_name(self.enemy_name).ships
            my_ships = self.ships

            print(enemy_ships)

            # each of my ship picks a random target ship to attack
            for i in range(len(my_ships)):
                reactor.callLater(i*2 + 1, self._pick_random_ship_to_shoot, [i, enemy_ships])
                # timer = Timer(i*2 + 1, self._pick_random_ship_to_shoot, args=[i, enemy_ships])
                # timer.start()

            # change turn
            self.your_turn_in_battle = False
            reactor.callLater(len(my_ships) * 2 + 1, self._change_turn)
            # self.your_turn_in_battle = False
            # self._get_other_role_by_name(self.enemy_name).your_turn_in_battle = True
            # # clear timer
            # timer = Timer(len(my_ships) * 2 + 1, self._clear_timer)
            # timer.start()

    def _change_turn(self):
        self._get_other_role_by_name(self.enemy_name).your_turn_in_battle = True

    def _clear_timer(self):
        self.battle_timer = 1

    def _pick_random_ship_to_shoot(self, params):
        i = params[0]
        enemy_ships = params[1]

        rand_seed_num = enemy_ships[0].now_hp + len(enemy_ships)
        random.seed(rand_seed_num)
        random_target_ship_id = random.choice(range(len(enemy_ships)))
        self.shoot_ship([i, random_target_ship_id])


    # ship yard
    def buy_ship(self, params):
        name = params[0]
        type = params[1]

        ship = Ship(name, type)
        self.ships.append(ship)

        print('now ships:', len(self.ships))

    def sell_ship(self, params):
        num = params[0]

        del self.ships[num]
        print('now ships:', len(self.ships))

    def repair_all(self, params):
        for ship in self.ships:
            ship.now_hp = ship.max_hp

    # bar
    def hire_crew(self, params):
        count = params[0]
        to_which_ship = params[1]
        print("to_which_ship:", to_which_ship)
        print(self.ships)
        self.ships[to_which_ship].add_crew(count)
        print(self.name, "ship", to_which_ship, "now has crew:", self.ships[to_which_ship].crew)

    def fire_crew(self, params):
        count = params[0]
        from_which_ship = params[1]
        self.ships[from_which_ship].cut_crew(count)
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

        can_add = self.ships[to_which_ship].add_cargo(cargo_name, count)
        if can_add:
            unit_price = 5
            self.gold -= count * unit_price

        print(self.name, "ship", to_which_ship, "cargoes", self.ships[to_which_ship].cargoes)
        print(self.name, "gold:", self.gold)

    def sell_cargo(self, params):
        cargo_name = params[0]
        count = params[1]
        from_which_ship = params[2]

        can_cut = self.ships[from_which_ship].cut_cargo(cargo_name, count)
        if can_cut:
            unit_price = 10
            self.gold += count * unit_price

        print(self.name, "ship", from_which_ship, "cargoes", self.ships[from_which_ship].cargoes)
        print(self.name, "gold:", self.gold)

    # port
    def load_supply(self, params):
        supply_name = params[0]
        count = params[1]
        to_which_ship = params[2]

        self.ships[to_which_ship].load_supply(supply_name, count)
        print(self.name, "ship", to_which_ship, "supplies", self.ships[to_which_ship].supplies[supply_name])

    def unload_supply(self, params):
        supply_name = params[0]
        count = params[1]
        from_which_ship = params[2]

        self.ships[from_which_ship].unload_supply(supply_name, count)
        print(self.name, "ship", from_which_ship, "supplies", 'unloaded')


class Ship:
    shooting_img = ''

    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.x = 10
        self.y = 10
        self.state = ''
        self.now_hp = 10
        self.damage_got = ''
        self.max_hp = 10
        self.crew = 5
        self.cargoes = {}
        self.supplies = {
            'Food':20,
            'Water':20,
        }

    def move(self, direction):
        if direction == 'up':
            self.y -= 5
        elif direction == 'down':
            self.y += 5
        elif direction == 'left':
            self.x -= 5
        elif direction == 'right':
            self.x += 5

    def shoot(self, ship):
        self.state = 'shooting'
        ship.state = 'shot'
        # timer = Timer(1, self._clear_state, args=[ship])
        # timer.start()

        ship.now_hp -= 3
        ship.damage_got = '3'
        return ship.now_hp <= 0

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
        if cargo_name in self.cargoes:
            self.cargoes[cargo_name] -= count

            if self.cargoes[cargo_name] <= 0:
                del self.cargoes[cargo_name]

            return True
        else:
            return False

    def load_supply(self, supply_name, count):
        if supply_name in self.supplies:
            self.supplies[supply_name] += count
        else:
            self.supplies[supply_name] = count

        return True

    def unload_supply(self, supply_name, count):
        if supply_name in self.supplies:
            self.supplies[supply_name] -= count
            return True
        else:
            return False


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