# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data


class StaticNpc:
    def __init__(self, game):
        self.game = game
        self.x = 1
        self.y = 1
        self.frame = -1

    def update(self):
        """change frame from -1 to 1"""
        self.frame *= -1


class Dog(StaticNpc):
    """at the entrance of bars"""
    def __init__(self, game, port_id):
        super(Dog, self).__init__(game)
        self.x = hash_ports_meta_data[port_id]['buildings'][2]['x'] * c.PIXELS_COVERED_EACH_MOVE
        self.y = hash_ports_meta_data[port_id]['buildings'][2]['y'] * c.PIXELS_COVERED_EACH_MOVE

    def draw(self):
        dog_x_position_in_tile_set = 28
        person_rect = self.game.images['person_in_port'].get_rect()
        person_rect = person_rect.move(c.PERSON_SIZE_IN_PIXEL * dog_x_position_in_tile_set, 0)

        self.game.screen_surface.blit(self.game.images['person_tileset'], self.game.screen_surface_rect.center, person_rect)


class OldMan(StaticNpc):
    def __init__(self):
        pass


class Agent(StaticNpc):
    def __init__(self):
        pass


class DynamicNpc:
    def __init__(self):
        pass


if __name__ == '__main__':
    npc = Dog()
    npc.update()
    npc.update()
    print(npc.frame)
    print(npc.x)