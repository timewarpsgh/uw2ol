import pygame as pg
from image_processor import get_image
from twisted.internet import reactor, threads, defer


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


class EngageMark(pg.sprite.Sprite):
    def __init__(self, game, ship_id, x, y):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        self.image = game.images['engage_sign']
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.ship_id = ship_id

    def update(self):
        self._change_state()
        self._draw()

    def _change_state(self):
        pass

    def _draw(self):
        self.game.screen_surface.blit(self.image, self.rect)

    def clicked(self):
        ship_id = self.ship_id
        self.game.change_and_send('flag_ship_engage', [ship_id])
        self.game.think_time_in_battle = c.THINK_TIME_IN_BATTLE
        self.game.my_role._clear_marks()


class ShootMark(pg.sprite.Sprite):
    def __init__(self, game, ship_id, x, y):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        self.image = game.images['shoot_mark']
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.ship_id = ship_id

    def update(self):
        self._change_state()
        self._draw()

    def _change_state(self):
        pass

    def _draw(self):
        self.game.screen_surface.blit(self.image, self.rect)

    def clicked(self):
        ship_id = self.ship_id
        self.game.change_and_send('flag_ship_shoot', [ship_id])
        self.game.think_time_in_battle = c.THINK_TIME_IN_BATTLE
        self.game.my_role._clear_marks()


class MoveMark(pg.sprite.Sprite):
    def __init__(self, game, direct, x, y):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        if direct == 'no_move':
            self.image = game.images['no_move_mark']
        else:
            self.image = game.images['move_mark']
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direct = direct

    def update(self):
        self._change_state()
        self._draw()

    def _change_state(self):
        pass

    def _draw(self):
        self.game.screen_surface.blit(self.image, self.rect)

    def clicked(self):
        self.game.change_and_send('flagship_move', [self.direct])


class ShipDot():
    def __init__(self, color):
        self.image = pg.Surface((c.SHIP_DOT_SIZE, c.SHIP_DOT_SIZE))
        self.image.fill(color)
        self.rect = self.image.get_rect()

class BattleMiniMap(pg.sprite.Sprite):
    def __init__(self, game):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        self.image = pg.Surface((100, 100)).convert_alpha()
        self.image.fill(c.TRANS_GRAY)

        self.rect = self.image.get_rect()
        self.rect.x = 15
        self.rect.y = 250

        self.my_ship_dot = ShipDot(c.YELLOW)
        self.enemy_ship_dot = ShipDot(c.RED)

    def update(self):
        self._change_state()
        self._draw()

    def _change_state(self):
        # clear
        self.image.fill(c.TRANS_GRAY)

        # draw my ships dots
        for ship in self.game.my_role.ships:
            x = (ship.x - 35) * 3
            y = (ship.y - 35) * 3

            self.image.blit(self.my_ship_dot.image,
                            (x, y), self.my_ship_dot.rect)

        # draw enemy ships dots
        for ship in self.game.my_role.get_enemy_role().ships:
            x = (ship.x - 35) * 3
            y = (ship.y - 35) * 3

            self.image.blit(self.enemy_ship_dot.image,
                            (x, y), self.enemy_ship_dot.rect)

    def _draw(self):
        self.game.screen_surface.blit(self.image, self.rect)


class Text():
    def __init__(self, game, text, color=c.BLACK):
        self.image = game.font.render(text, True, color)
        self.rect = self.image.get_rect()

class BattleStates(pg.sprite.Sprite):
    def __init__(self, game):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        self.image = pg.Surface((c.WINDOW_WIDTH, c.WINDOW_HIGHT)).convert_alpha()
        self.image.fill(c.TRANS_BLANK)

        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0

    def update(self):
        self._change_state()
        self._draw()

    def _change_state(self):
        self.image.fill(c.TRANS_BLANK)
        self.__draw_my_ships_states()
        self.__draw_enemy_ships_states()

    def __draw_my_ships_states(self):
        # my timer
        my_timer_text = None
        if self.game.my_role.your_turn_in_battle:
            my_timer_text = 'Your Turn ' + str(self.game.think_time_in_battle)
        else:
            my_timer_text = 'Please Wait...'

        timer_text = Text(self.game, my_timer_text, c.YELLOW)
        timer_text.rect.x = 20
        timer_text.rect.y = 5
        self.image.blit(timer_text.image, timer_text.rect)

        # ships states
        for id, ship in enumerate(self.game.my_role.ships):
            # all ships
            num_text = Text(self.game, str(id), c.BLACK)
            num_text.rect.x = 10
            num_text.rect.y = (id + 2) * 20

            hp_text = Text(self.game, str(ship.now_hp), c.YELLOW)
            hp_text.rect.x = 30
            hp_text.rect.y = (id + 2) * 20

            crew_text = Text(self.game, str(ship.crew), c.WHITE)
            crew_text.rect.x = 50
            crew_text.rect.y = (id + 2) * 20

            for item in [num_text, hp_text, crew_text]:
                self.image.blit(item.image,
                                item.rect)

            # non flag ships
            if id != 0:
                strategy_text = Text(self.game, str(ship.attack_method), c.ORANGE)
                strategy_text.rect.x = 80
                strategy_text.rect.y = (id + 2) * 20

                target_text = Text(self.game, str(ship.target), c.CRIMSON)
                target_text.rect.x = 130
                target_text.rect.y = (id + 2) * 20

                for item in [strategy_text, target_text]:
                    self.image.blit(item.image,
                                    item.rect)

    def __draw_enemy_ships_states(self):
        # timer
        enemy_timer_text = None
        if self.game.other_roles[self.game.my_role.enemy_name].your_turn_in_battle:
            enemy_timer_text = 'Enemy Turn'
        else:
            enemy_timer_text = 'Please Wait...'

        enemy_timer_img = self.game.font.render(enemy_timer_text, True, c.YELLOW)
        self.image.blit(enemy_timer_img, (c.WINDOW_WIDTH - 150, 5))


        # ships states
        for id, ship in enumerate(self.game.my_role.get_enemy_role().ships):
            num_text = Text(self.game, str(id), c.BLACK)
            num_text.rect.x = c.WINDOW_WIDTH - 80
            num_text.rect.y = (id + 2) * 20

            hp_text = Text(self.game, str(ship.now_hp), c.YELLOW)
            hp_text.rect.x = c.WINDOW_WIDTH - 80 + 20
            hp_text.rect.y = (id + 2) * 20

            crew_text = Text(self.game, str(ship.crew), c.WHITE)
            crew_text.rect.x = c.WINDOW_WIDTH - 80 + 40
            crew_text.rect.y = (id + 2) * 20

            for item in [num_text, hp_text, crew_text]:
                self.image.blit(item.image,
                                item.rect)

    def _draw(self):
        self.game.screen_surface.blit(self.image, self.rect)


class ShipInBattle(pg.sprite.Sprite):
    """not used"""
    def __init__(self, game, id, direction, x, y, is_enemy=False):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        self.id = id
        self.direction = direction

        self.image = self.game.images['ship_in_battle'][direction]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self._change_state()
        self._draw()

    def _change_state(self):
        pass

    def _draw(self):
        self.game.screen_surface.blit(self.image, self.rect)

if __name__ == '__main__':
    ex = Explosion()