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
            self.y -= c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'n'
        elif direction == 's':
            self.y += c.PIXELS_COVERED_EACH_MOVE
            self.direction = 's'
        elif direction == 'w':
            self.x -= c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'w'
        elif direction == 'e':
            self.x += c.PIXELS_COVERED_EACH_MOVE
            self.direction = 'e'

        self.now_frame *= -1

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


if __name__ == '__main__':
    pass