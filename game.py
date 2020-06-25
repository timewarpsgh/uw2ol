import pygame
import sys
from twisted.internet import reactor
import constants as c


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

        # load assets
        self.font = None
        self.images = {}
        self.load_assets()

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
        # different responses
        if pck_type == 'your_role_data':
            print("got my role data")
            role = message_obj
            self.my_role = role
            print("my role's x y:", role.x, role.y, role.map)


