from twisted.internet import reactor, task
import random

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data


class StaticNpc:
    def __init__(self, game, port_id, building_id, frame_1_index, frame_2_index):
        # parent
        self.game = game

        # position
        self.x = (hash_ports_meta_data[(port_id + 1)]['buildings']
                  [building_id]['x'] + 1) * c.PIXELS_COVERED_EACH_MOVE
        self.y = (hash_ports_meta_data[(port_id + 1)]['buildings']
                  [building_id]['y'] + 1) * c.PIXELS_COVERED_EACH_MOVE

        # image
        self.frame_1_index = frame_1_index
        self.frame_2_index = frame_2_index
        self.rect = self.game.images['person_in_port'].get_rect()
        self.tile_set = self.game.images['person_tileset']

    def draw(self):
        person_rect = self.rect

        # choose frame
        if self.game.ship_frame == 1:
            person_rect = person_rect.move(c.PERSON_SIZE_IN_PIXEL * self.frame_1_index, 0)
        else:
            person_rect = person_rect.move(c.PERSON_SIZE_IN_PIXEL * self.frame_2_index, 0)

        # choose location
        x = self.game.screen_surface_rect.centerx - self.game.my_role.x + self.x
        y = self.game.screen_surface_rect.centery - self.game.my_role.y + self.y

        # draw
        self.game.screen_surface.blit(self.tile_set, (x, y), person_rect)

class Dog(StaticNpc):
    """at the entrance of bars"""
    def __init__(self, game, port_id):
        super(Dog, self).__init__(game, port_id,
                                  building_id=c.DOG_BUILDING_ID,
                                  frame_1_index=c.DOG_FRAME_1_INDEX,
                                  frame_2_index=c.DOG_FRAME_2_INDEX)


class OldMan(StaticNpc):
    """at the entrance of inn"""
    def __init__(self, game, port_id):
        super(OldMan, self).__init__(game, port_id,
                                  building_id=c.OLD_MAN_BUILDING_ID,
                                  frame_1_index=c.OLD_MAN_FRAME_1_ID,
                                  frame_2_index=c.OLD_MAN_FRAME_2_ID)


class Agent(StaticNpc):
    """at the entrance of market"""
    def __init__(self, game, port_id):
        super(Agent, self).__init__(game, port_id,
                                  building_id=c.AGENT_BUILDING_ID,
                                  frame_1_index=c.AGENT_FRAME_1_ID,
                                  frame_2_index=c.AGENT_FRAME_2_ID)

def init_static_npcs(game, port_id):
    game.dog = Dog(game, port_id)
    game.old_man = OldMan(game, port_id)
    game.agent = Agent(game, port_id)



class DynamicNpc:
    def __init__(self, game, port_id, building_id):
        # parent
        self.game = game

        # pos and direction
        self.x = (hash_ports_meta_data[(port_id + 1)]['buildings']
                  [building_id]['x'] + 1) * c.PIXELS_COVERED_EACH_MOVE
        self.y = (hash_ports_meta_data[(port_id + 1)]['buildings']
                  [building_id]['y'] + 1) * c.PIXELS_COVERED_EACH_MOVE
        self.direction = 'n'
        self.direction_options = ['n', 'e', 's', 'w']

        # frames
        self.now_frame = -1
        self.frames = {
            'n':[],
            's':[],
            'e':[],
            'w':[],
        }
        self.rect = self.game.images['person_in_port'].get_rect()
        self.tile_set = self.game.images['person_tileset']

    def _move(self, direction):
        if direction == 'n':
            if self._can_move('n'):
                self.y -= c.PIXELS_COVERED_EACH_MOVE
                self.direction = 'n'
                self.now_frame *= -1
        elif direction == 's':
            if self._can_move('s'):
                self.y += c.PIXELS_COVERED_EACH_MOVE
                self.direction = 's'
                self.now_frame *= -1
        elif direction == 'w':
            if self._can_move('w'):
                self.x -= c.PIXELS_COVERED_EACH_MOVE
                self.direction = 'w'
                self.now_frame *= -1
        elif direction == 'e':
            if self._can_move('e'):
                self.x += c.PIXELS_COVERED_EACH_MOVE
                self.direction = 'e'
                self.now_frame *= -1

    def _can_move(self, direction):
        """similar to role.can_move"""
        # get piddle
        piddle = self.game.port_piddle

        # perl piddle and python numpy(2d array) are different
        y = int(self.x / 16)
        x = int(self.y / 16)

        # basic 4 directions
        if direction == 'n':
            if self.y > c.PIXELS_COVERED_EACH_MOVE * 3:
                # not in asia
                if self.game.my_role.is_in_port():
                    if int(self.game.my_role.map) < 94:
                        if piddle[x, y] in c.WALKABLE_TILES and piddle[x, y + 1] in c.WALKABLE_TILES:
                            if self.y > 0:
                                return True
                    # in asia
                    else:
                        if piddle[x, y] in c.WALKABLE_TILES_FOR_ASIA and piddle[x, y + 1] in c.WALKABLE_TILES_FOR_ASIA:
                            if self.y > 0:
                                return True
                else:
                    return False

        elif direction == 's':
            if self.y < c.PIXELS_COVERED_EACH_MOVE * (c.PORT_TILES_COUNT - 3):
                if piddle[x + 2, y] in c.WALKABLE_TILES and piddle[x + 2, y + 1] in c.WALKABLE_TILES:
                    return True
        elif direction == 'w':
            if self.x > c.PIXELS_COVERED_EACH_MOVE * 3:
                if piddle[x + 1, y - 1] in c.WALKABLE_TILES:
                    return True
        elif direction == 'e':
            if self.x < c.PIXELS_COVERED_EACH_MOVE * (c.PORT_TILES_COUNT - 3):
                if piddle[x + 1, y + 2] in c.WALKABLE_TILES:
                    return True

        # ret
        return False

    def _random_move(self):
        chosen_direction = random.choice(self.direction_options)
        self._move(chosen_direction)

    def start_looping_random_move(self):
        looping_task = task.LoopingCall(self._random_move)
        looping_task.start(0.5)

    def draw(self):
        person_rect = self.rect

        # choose frame
        now_frame_id = None
        if self.now_frame == -1:
            now_frame_id = self.frames[self.direction][0]
        else:
            now_frame_id = self.frames[self.direction][1]

        person_rect = person_rect.move(c.PERSON_SIZE_IN_PIXEL * now_frame_id, 0)

        # choose location
        x = self.game.screen_surface_rect.centerx - self.game.my_role.x + self.x
        y = self.game.screen_surface_rect.centery - self.game.my_role.y + self.y

        # draw
        self.game.screen_surface.blit(self.tile_set, (x, y), person_rect)

class Man(DynamicNpc):
    def __init__(self, game, port_id):
        super(Man, self).__init__(game, port_id,
                                  building_id=c.DOG_BUILDING_ID)
        self.frames = {
            'n':[16, 17],
            'e': [18, 19],
            's':[20, 21],
            'w':[22, 23],
        }

class Woman(DynamicNpc):
    def __init__(self, game, port_id):
        super(Woman, self).__init__(game, port_id,
                                    building_id=c.AGENT_BUILDING_ID)
        self.frames = {
            'n':[8, 9],
            'e': [10, 11],
            's':[12, 13],
            'w':[14, 15],
        }

def init_dynamic_npcs(game, port_id):
    game.man = Man(game, port_id)
    game.man.start_looping_random_move()

    game.man_1 = Man(game, port_id)
    game.man_1.start_looping_random_move()

    game.woman = Woman(game, port_id)
    game.woman.start_looping_random_move()
    game.woman_1 = Woman(game, port_id)
    game.woman_1.start_looping_random_move()

if __name__ == '__main__':
    pass