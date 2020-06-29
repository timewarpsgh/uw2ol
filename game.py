import pygame
import sys
from twisted.internet import reactor
import constants as c
from role import Role, Ship, Mate

EVENT_MOVE = pygame.USEREVENT + 5


class Game():
    # init
    def __init__(self):
        # pygame
        pygame.init()
        pygame.display.set_caption(c.CAPTION)
        self.screen_surface = pygame.display.set_mode([c.WINDOW_WIDTH, c.WINODW_HIGHT])

        # connection
        self.connection = None

        # my role (data)
        self.my_role = None
        self.other_roles = {}

        # load assets
        self.font = None
        self.images = {}
        self.load_assets()

        # test looping event
        # pygame.time.set_timer(EVENT_MOVE, 50)
        self.move_direction = 1
        self.move_count = 0

    def load_assets(self):
        # maps
        self.images['port'] = pygame.image.load("./assets/port.png").convert_alpha()
        self.images['sea'] = pygame.image.load("./assets/sea.png").convert_alpha()
        self.images['battle'] = pygame.image.load("./assets/battle.png").convert_alpha()

        # sprite
        self.images['ship_at_sea'] = pygame.image.load("./assets/ship_at_sea.png").convert_alpha()
        self.images['person_in_port'] = pygame.image.load("./assets/person_in_port.png").convert_alpha()

        # font
        self.font = pygame.font.SysFont("fangsong", 24)

    # update
    def update(self):
        """called each frame"""
        self.process_input_events()
        self.draw()

    def process_input_events(self):
        # get events
        events = pygame.event.get()

        # iterate events
        for event in events:
            # quit
            if event.type == pygame.QUIT:
                pygame.quit()
                reactor.stop()
                sys.exit()

            # key
            elif event.type == pygame.KEYDOWN:

                # return (focus text entry)
                if event.key == ord('p'):
                    print(self.my_role.name)
                elif event.key == ord('l'):
                    self.connection.send('login', ['1', '1'])
                elif event.key == ord('w'):
                    self.change_and_send('move', ['up'])
                elif event.key == ord('s'):
                    self.change_and_send('move', ['down'])
                elif event.key == ord('a'):
                    self.change_and_send('move', ['left'])
                elif event.key == ord('d'):
                    self.change_and_send('move', ['right'])

            elif event.type == EVENT_MOVE:
                # print("got move event")

                if self.my_role:
                    if self.move_direction == 1:
                        self.change_and_send('move', ['right'])
                    else:
                        self.change_and_send('move', ['left'])

                    self.move_count += 1

                    if self.move_count >= 15:
                        self.move_count = 0
                        self.move_direction *= -1

    def draw(self):
        # fill
        self.screen_surface.fill(c.BLACK)

        # if logged in
        if self.my_role:

            # draw map
            now_map = self.my_role.map
            self.screen_surface.blit(self.images[now_map], (0, 0))

            # draw my role
            self.screen_surface.blit(self.images['person_in_port'], (self.my_role.x, self.my_role.y))

            # draw other roles
            for role in self.other_roles.values():
                self.screen_surface.blit(self.images['person_in_port'], (role.x, role.y))

        # not logged in
        else:
            text_surface = self.font.render('Please Login', True, c.WHITE)
            self.screen_surface.blit(text_surface, (5, 5))

        # flip
        pygame.display.flip()

    def get_connection(self, obj):
        """get protocol object to access network functions"""
        self.connection = obj

    def pck_received(self, pck_type, message_obj):

        if pck_type == 'your_role_data_and_others':
            # my role
            print("got my role data")
            my_role = message_obj[0]
            self.my_role = my_role
            print("my role's x y:", my_role.x, my_role.y, my_role.map, my_role.name)

            # other roles
            other_roles = message_obj[1]
            for role in other_roles:
                self.other_roles[role.name] = role
            print(other_roles)

        elif pck_type == 'new_role':
            new_role = message_obj
            self.other_roles[new_role.name] = new_role
            print("got new role named:", new_role.name)

        elif pck_type == 'logout':
            name_of_logged_out_role = message_obj
            del self.other_roles[name_of_logged_out_role]

        # sync packets
        elif pck_type in Role.__dict__:
            list = message_obj
            name = list.pop()
            func_name = pck_type
            role = self.other_roles[name]
            print("trying", func_name, list, "for", name)
            func = getattr(role, func_name)
            func(list)


    def change_and_send(self, protocol_name, params_list):
        self.connection.send(protocol_name, params_list)
        func = getattr(self.my_role, protocol_name)
        func(params_list)
