import pygame as pg
from image_processor import get_image

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

import constants as c

class SpriteSheet():
    def __init__(self, image_name, collumns, rows, game):
        self.image = game.images[image_name]
        self.rect = self.image.get_rect()
        self.collumns = collumns
        self.rows = rows

        self.unit_width = int(self.rect.width / self.collumns)
        self.unit_height = int(self.rect.height / self.rows)

        self.frame_count = self.rows * self.collumns
        self.frames = [None] * self.frame_count
        for frame_id in range(self.frame_count):
            image_x = (frame_id % self.collumns) *  self.unit_width
            image_y = (frame_id // self.rows) *  self.unit_height
            self.frames[frame_id] = get_image(self.image, image_x, image_y,
                                              self.unit_width, self.unit_height)

    def get_frames(self):
        return self.frames


class Explosion(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        self.frames = SpriteSheet('explosion', 4, 4, game).get_frames()
        self.frame_index = -1

        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self._change_state()
        self._draw()

    def _change_state(self):
        if self.frame_index < len(self.frames) - 1:
            self.frame_index += 1
            self.image = self.frames[self.frame_index]
        else:
            self.kill()

    def _draw(self):
        self.game.screen_surface.blit(self.image, self.rect)


class CannonBall(pg.sprite.Sprite):
    def __init__(self, game, x, y, d_x, d_y):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        self.image = game.images['cannon']
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.d_x = d_x
        self.d_y = d_y

        self.steps_to_change = 30
        self.step_index = 0

        self.unit_x_change = int(self.d_x / self.steps_to_change)
        self.unit_y_change = int(self.d_y / self.steps_to_change)

    def update(self):
        self._change_state()
        self._draw()

    def _change_state(self):
        self.rect.x += self.unit_x_change
        self.rect.y += self.unit_y_change
        self.step_index += 1
        if self.step_index == self.steps_to_change:
            self.kill()

    def _draw(self):
        self.game.screen_surface.blit(self.image, self.rect)

class EngageSign(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        self.frames = []
        for i in range(2):
            image_0 = game.images['engage_sign']
            image_1 = game.images['engage_sign_1']

            for j in range(4):
                self.frames.append(image_1)
            for k in range(4):
                self.frames.append(image_0)

        self.frame_index = -1

        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self._change_state()
        self._draw()

    def _change_state(self):
        if self.frame_index < len(self.frames) - 1:
            self.frame_index += 1
            self.image = self.frames[self.frame_index]
        else:
            self.kill()

    def _draw(self):
        self.game.screen_surface.blit(self.image, self.rect)


class ShootDamageNumber(pg.sprite.Sprite):
    def __init__(self, game, number, x, y, color=c.YELLOW):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        self.image = self.game.font.render(str(number), True, color)
        self.rect = self.image.get_rect()

        self.frames = [None] * 60
        scale = 3
        for i in range(len(self.frames)):
            scale -= 0.03
            self.frames[i] = pg.transform.scale(self.image,
                                                (int(self.rect.width * scale),
                                                 int(self.rect.height * scale)))
        self.frame_index = -1

        self.image = self.frames[-1]

        self.rect.x = x
        self.rect.y = y

        self.x_speed = 1.4
        self.y_speed = 3
        self.d_y = 0.15

    def update(self):
        self._change_state()
        self._draw()

    def _change_state(self):
        if self.frame_index < len(self.frames) - 1:
            self.frame_index += 1
            self.image = self.frames[self.frame_index]

            self.rect.y -= self.y_speed
            self.y_speed -= self.d_y
            self.rect.x += self.x_speed
        else:
            self.kill()

    def _draw(self):
        self.game.screen_surface.blit(self.image, self.rect)



if __name__ == '__main__':
    ex = Explosion()