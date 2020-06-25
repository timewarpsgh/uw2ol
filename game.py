import pygame
import constants as c


class Game():
    def __init__(self):
        # pygame
        pygame.init()
        pygame.display.set_caption(c.CAPTION)
        self.screen_surface = pygame.display.set_mode([c.WINDOW_WIDTH, c.WINODW_HIGHT])

        # connection
        self.connection = None

        # my role (data)
        self.my_role = None

    def update(self):
        """called each frame"""
        # process input events
        events = pygame.event.get()
        for event in events:
            # quit
            if event.type == pygame.QUIT:
                sys.exit()

            # key
            elif event.type == pygame.KEYDOWN:

                # return (focus text entry)
                if event.key == ord('p'):
                    print(self.my_role.name)

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


