import pygame as pg
# from images import IMAGES
from image_processor import get_image

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


if __name__ == '__main__':
    ex = Explosion()