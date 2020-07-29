import pygame
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data

def draw(self):
    """argument self is game"""
    # clear
    self.screen_surface.fill(c.BLACK)

    # draw
    if self.my_role:
        draw_logged_in_state(self)
    else:
        draw_not_logged_in_state(self)

    # flip
    pygame.display.flip()

def draw_logged_in_state(self):
    # draw map
    now_map = self.my_role.map

        # in port
    if now_map.isdigit():
        x = self.screen_surface_rect.centerx - self.my_role.x
        y = self.screen_surface_rect.centery - self.my_role.y
        self.screen_surface.blit(self.images['port'], (x, y))

        # at sea
    elif now_map == 'sea':
        x = -(c.PARTIAL_WORLD_MAP_TILES_IN_ONE_DIRECTION * c.PIXELS_COVERED_EACH_MOVE
              - self.screen_surface_rect.centerx + self.my_role.x
              - self.map_maker.x_tile * c.PIXELS_COVERED_EACH_MOVE)
        y = -(c.PARTIAL_WORLD_MAP_TILES_IN_ONE_DIRECTION * c.PIXELS_COVERED_EACH_MOVE
              - self.screen_surface_rect.centery + self.my_role.y
              - self.map_maker.y_tile * c.PIXELS_COVERED_EACH_MOVE)

        self.screen_surface.blit(self.images['sea'], (x, y))

        # in battle
    else:
        self.screen_surface.blit(self.images['battle'], (0, 0))

    # draw based on map

        # in building
    if self.my_role.in_building_type:
            # bg
        self.screen_surface.blit(self.images['building_bg'], (c.HUD_WIDTH, 0))
            # person
        self.screen_surface.blit(self.building_image, (c.HUD_WIDTH + 5, 5))

            # dialog box
        self.screen_surface.blit(self.images['building_chat'], (c.HUD_WIDTH + c.BUILDING_PERSON_WIDTH + 10, 0))
            # dialog
        blit_text(self.screen_surface, self.building_text, (c.HUD_WIDTH + c.BUILDING_PERSON_WIDTH + 10 + 10, 5), self.font)
        draw_hud(self)

        # not in building
    else:
            # in port
        if now_map.isdigit():
            draw_in_port(self)
            draw_hud(self)

            # at sea
        elif now_map == 'sea':
            draw_at_sea(self)
            draw_hud(self)

                # max days at sea
            draw_text(self, 'Max Days', 10, c.WINDOW_HIGHT - 140)
            draw_text(self, str(self.max_days_at_sea), 10, c.WINDOW_HIGHT - 120)

                # days spent at sea
            draw_text(self, 'Days Spent', 10, c.WINDOW_HIGHT - 100)
            draw_text(self, str(self.days_spent_at_sea), 10, c.WINDOW_HIGHT - 80)

            # in battle
        else:
            draw_in_battle(self)

    # draw speach
    draw_speech(self)

    # draw ui
    self.ui_manager.draw_ui(self.screen_surface)

def draw_hud(self):
    # left hud
    self.screen_surface.blit(self.images['hud_left'], (0, 0))
    hud_left_rect = self.images['hud_left'].get_rect()

        # gold
    text = 'Gold:' + str(self.my_role.gold)
    text_img = self.font.render(text, True, c.BLACK)
    self.screen_surface.blit(text_img, (10, c.WINDOW_HIGHT - 50))

    # right hud
    self.screen_surface.blit(self.images['hud_right'], (c.WINDOW_WIDTH - hud_left_rect.width, 0))

        # if in port
    if self.my_role.map.isdigit():
            # port name
        port_name = hash_ports_meta_data[int(self.my_role.map) + 1]['name']
        draw_text(self, port_name, c.WINDOW_WIDTH - 100, 5)

        economy_id = hash_ports_meta_data[int(self.my_role.map) + 1]['economyId']
        region_name = hash_ports_meta_data['markets'][economy_id]
        draw_text(self, region_name, c.WINDOW_WIDTH - 100, 20)

            # index
        economy_index = hash_ports_meta_data[int(self.my_role.map) + 1]['economy']
        industry_index = hash_ports_meta_data[int(self.my_role.map) + 1]['industry']

        draw_text(self, 'Economy', c.WINDOW_WIDTH - 100, 80)
        draw_text(self, str(economy_index), c.WINDOW_WIDTH - 100, 100)

        draw_text(self, 'Industry', c.WINDOW_WIDTH - 100, 120)
        draw_text(self, str(industry_index), c.WINDOW_WIDTH - 100, 140)

def draw_text(self, text, x, y, color=c.BLACK):
    text_img = self.font.render(text, True, color)
    self.screen_surface.blit(text_img, (x, y))

def draw_in_port(self):
    # draw my role

        # image
    direction = self.my_role.direction
    frame = self.my_role.person_frame
    person_rect = person_direction_2_rect_in_sprite_sheet(self, direction, frame)

    self.screen_surface.blit(self.images['person_tileset'], self.screen_surface_rect.center, person_rect)

        # name
    draw_text(self, str(self.my_role.name), c.WINDOW_WIDTH / 2, -15 + c.WINDOW_HIGHT / 2, c.YELLOW)

    # draw other roles
    for role in self.other_roles.values():
        # image
        direction = role.direction
        frame = role.person_frame
        person_rect = person_direction_2_rect_in_sprite_sheet(self, direction, frame)

        x = self.screen_surface_rect.centerx - self.my_role.x + role.x
        y = self.screen_surface_rect.centery - self.my_role.y + role.y

        self.screen_surface.blit(self.images['person_tileset'], (x, y), person_rect)

        # name
        draw_text(self, str(role.name), x, -15 + y, c.YELLOW)

def draw_at_sea(self):
    # draw my role

        # image
    direction = self.my_role.direction
    ship_rect = ship_direction_2_rect_in_sprite_sheet(self, direction)

    self.screen_surface.blit(self.images['ship-tileset'], self.screen_surface_rect.center, ship_rect)

        # name
    draw_text(self, str(self.my_role.name), c.WINDOW_WIDTH / 2, -15 + c.WINDOW_HIGHT / 2, c.YELLOW)

    # draw other roles
    for role in self.other_roles.values():
        # image
        direction = role.direction
        ship_rect = ship_direction_2_rect_in_sprite_sheet(self, direction)

        x = self.screen_surface_rect.centerx - self.my_role.x + role.x
        y = self.screen_surface_rect.centery - self.my_role.y + role.y

        self.screen_surface.blit(self.images['ship-tileset'], (x, y), ship_rect)

        # name
        draw_text(self, str(role.name), x, -15 + y, c.YELLOW)

def ship_direction_2_rect_in_sprite_sheet(self, direction):
    ship_rect = self.images['ship_at_sea'].get_rect()

    # frame 1
    if self.ship_frame == 1:
        if direction == 'right':
            ship_rect = ship_rect.move(c.SHIP_SIZE_IN_PIXEL * 2, c.SHIP_SIZE_IN_PIXEL * 1)
        elif direction == 'left':
            ship_rect = ship_rect.move(c.SHIP_SIZE_IN_PIXEL * 6, c.SHIP_SIZE_IN_PIXEL * 1)
        elif direction == 'up':
            ship_rect = ship_rect.move(c.SHIP_SIZE_IN_PIXEL * 0, c.SHIP_SIZE_IN_PIXEL * 1)
        elif direction == 'down':
            ship_rect = ship_rect.move(c.SHIP_SIZE_IN_PIXEL * 4, c.SHIP_SIZE_IN_PIXEL * 1)

    # frame 2
    else:
        if direction == 'right':
            ship_rect = ship_rect.move(c.SHIP_SIZE_IN_PIXEL * 3, c.SHIP_SIZE_IN_PIXEL * 1)
        elif direction == 'left':
            ship_rect = ship_rect.move(c.SHIP_SIZE_IN_PIXEL * 7, c.SHIP_SIZE_IN_PIXEL * 1)
        elif direction == 'up':
            ship_rect = ship_rect.move(c.SHIP_SIZE_IN_PIXEL * 1, c.SHIP_SIZE_IN_PIXEL * 1)
        elif direction == 'down':
            ship_rect = ship_rect.move(c.SHIP_SIZE_IN_PIXEL * 5, c.SHIP_SIZE_IN_PIXEL * 1)

    return ship_rect

def person_direction_2_rect_in_sprite_sheet(self, direction, frame):
    person_rect = self.images['person_in_port'].get_rect()

    # frame 1
    if frame == 1:
        if direction == 'right':
            person_rect = person_rect.move(c.SHIP_SIZE_IN_PIXEL * 2, 0)
        elif direction == 'left':
            person_rect = person_rect.move(c.SHIP_SIZE_IN_PIXEL * 6, 0)
        elif direction == 'up':
            person_rect = person_rect.move(c.SHIP_SIZE_IN_PIXEL * 0, 0)
        elif direction == 'down':
            person_rect = person_rect.move(c.SHIP_SIZE_IN_PIXEL * 4, 0)

    # frame 2
    else:
        if direction == 'right':
            person_rect = person_rect.move(c.SHIP_SIZE_IN_PIXEL * 3, 0)
        elif direction == 'left':
            person_rect = person_rect.move(c.SHIP_SIZE_IN_PIXEL * 7, 0)
        elif direction == 'up':
            person_rect = person_rect.move(c.SHIP_SIZE_IN_PIXEL * 1, 0)
        elif direction == 'down':
            person_rect = person_rect.move(c.SHIP_SIZE_IN_PIXEL * 5, 0)

    return person_rect

def draw_in_battle(self):
    draw_my_ships(self)
    draw_enemy_ships(self)
    draw_battle_timer(self)

def draw_my_ships(self):
    # my ships
    index = 0
    for ship in self.my_role.ships:
        index += 30

        # ship
        ship_rect = ship_direction_2_rect_in_sprite_sheet(self, 'up')
        self.screen_surface.blit(self.images['ship-tileset'], (10, 10 + index), ship_rect)

        # # state
        # if ship.state == 'shooting':
        #     self.screen_surface.blit(Ship.shooting_img, (60, 10 + index))
        # elif ship.state == 'shot':
        #     damage_img = g_font.render(ship.damage_got, True, COLOR_BLACK)
        #     self.screen_surface.blit(damage_img, (60, 10 + index))

        # hp
        now_hp_img = self.font.render(str(ship.now_hp), True, c.YELLOW)
        self.screen_surface.blit(now_hp_img, (20 + 20, 10 + index))

def draw_enemy_ships(self):
    # enemy ships
    index = 0
    for ship in self.other_roles[self.my_role.enemy_name].ships:
        index += 30

        # ship
        ship_rect = ship_direction_2_rect_in_sprite_sheet(self, 'up')
        self.screen_surface.blit(self.images['ship-tileset'], (c.WINDOW_WIDTH - 50, 10 + index), ship_rect)

        # # state
        # if ship.state == 'shooting':
        #     g_screen.blit(Ship.shooting_img, (WIDTH - 100, 10 + index))
        # elif ship.state == 'shot':
        #     damage_img = g_font.render(ship.damage_got, True, COLOR_BLACK)
        #     g_screen.blit(damage_img, (WIDTH - 100, 10 + index))

        # hp
        now_hp_img = self.font.render(str(ship.now_hp), True, c.YELLOW)
        self.screen_surface.blit(now_hp_img, (c.WINDOW_WIDTH - 70 - 10, 10 + index))

def draw_battle_timer(self):
    # me
    my_timer_text = None
    if self.my_role.your_turn_in_battle:
        my_timer_text = 'Your Turn ' + str(self.think_time_in_battle)
    else:
        my_timer_text = 'Please Wait...'

    my_timer_img = self.font.render(my_timer_text, True, c.YELLOW)
    self.screen_surface.blit(my_timer_img, (20, 5))

    # enemy
    enemy_timer_text = None
    if self.other_roles[self.my_role.enemy_name].your_turn_in_battle:
        enemy_timer_text = 'Your Turn'
    else:
        enemy_timer_text = 'Please Wait...'

    enemy_timer_img = self.font.render(enemy_timer_text, True, c.YELLOW)
    self.screen_surface.blit(enemy_timer_img, (c.WINDOW_WIDTH - 150, 5))

def draw_speech(self):
    # my
    my_speak_img = self.font.render(self.my_role.speak_msg, True, c.YELLOW)
    x = self.screen_surface_rect.centerx
    y = self.screen_surface_rect.centery - 40
    self.screen_surface.blit(my_speak_img, (x, y))

    # others
    for role in self.other_roles.values():
        speak_img = self.font.render(role.speak_msg, True, c.YELLOW)
        x = self.screen_surface_rect.centerx - self.my_role.x + role.x
        y = self.screen_surface_rect.centery - self.my_role.y + role.y - 40
        self.screen_surface.blit(speak_img, (x, y))

def draw_not_logged_in_state(self):
    """argument self is game"""
    # bg
    self.screen_surface.blit(self.images['login_bg'], (0,0))

    # text
    text_surface = self.font.render(self.login_state_text, True, c.BLACK)
    self.screen_surface.blit(text_surface, (5, 5))

    # arrow
    arrow_surface = self.font.render('V', True, c.BLACK)
    self.screen_surface.blit(arrow_surface, (160, c.WINDOW_HIGHT - 50))

    # ui
    self.ui_manager.draw_ui(self.screen_surface)

def blit_text(surface, text, pos, font, color=pygame.Color('black')):
    """draws text block in multiple lines"""
    words = [word.split(' ') for word in text.splitlines()]  # 2D array where each row is a list of words.
    space = font.size(' ')[0]  # The width of a space.
    # max_width, max_height = surface.get_size()
    max_width, max_height = (c.BUILDING_CHAT_WIDTH, c.BUILDING_CHAT_HIGHT)
    x, y = pos
    for line in words:
        for word in line:
            word_surface = font.render(word, 0, color)
            word_width, word_height = word_surface.get_size()
            if x + word_width >= max_width:
                x = pos[0]  # Reset the x.
                y += word_height  # Start on new row.
            surface.blit(word_surface, (x, y))
            x += word_width + space
        x = pos[0]  # Reset the x.
        y += word_height  # Start on new row.