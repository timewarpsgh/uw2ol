import pygame

EVENT_MOVE = pygame.USEREVENT + 1
EVENT_HEART_BEAT = pygame.USEREVENT + 2

def handle_pygame_event(self, event):
    """argument self is game"""
    # quit
    if event.type == pygame.QUIT:
        pygame.quit()
        reactor.stop()
        sys.exit()

    # key
    elif event.type == pygame.KEYDOWN:

        # return (focus text entry)
        if event.key == pygame.K_RETURN:
            self.text_entry.focus()
            self.text_entry_active = True

        # escape
        if event.key == pygame.K_ESCAPE:

            # pop menu_stack
            if len(self.menu_stack) > 0:
                menu_to_kill = self.menu_stack.pop()
                self.selection_list_stack.pop()
                menu_to_kill.kill()
            print(len(self.menu_stack))
            print('escape pressed!')

            # clear buttons_in_windows dict
            self.buttons_in_windows.clear()
            print('buttons_in_windows dict cleared!')

            # deactivate text entry
            self.text_entry_active = False

        # other keys
        if not self.text_entry_active:
            if event.key == ord('p'):
                print(self.my_role.name)
            elif event.key == ord('1'):
                self.connection.send('login', ['1', '1'])
            elif event.key == ord('2'):
                self.connection.send('login', ['2', '2'])
            elif event.key == ord('3'):
                self.connection.send('login', ['3', '3'])
            elif event.key == ord('4'):
                self.connection.send('login', ['4', '4'])
            elif event.key == ord('5'):
                self.connection.send('login', ['5', '5'])
            elif event.key == ord('w'):
                self.change_and_send('move', ['up'])
            elif event.key == ord('s'):
                self.change_and_send('move', ['down'])
            elif event.key == ord('a'):
                self.change_and_send('move', ['left'])
            elif event.key == ord('d'):
                self.change_and_send('move', ['right'])

            elif event.key == ord('n'):
                self.change_and_send('change_map', ['sea'])
            elif event.key == ord('m'):
                self.change_and_send('change_map', ['port'])

            elif event.key == ord('b'):
                self.change_and_send('try_to_fight_with', ['b'])
            elif event.key == ord('e'):
                self.change_and_send('exit_battle', [])
            elif event.key == ord('v'):
                self.change_and_send('try_to_fight_with', ['d'])

            elif event.key == ord('k'):
                self.change_and_send('shoot_ship', [0, 0])

    # user defined events
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

    elif event.type == EVENT_HEART_BEAT:
        self.change_and_send('heart_beat', [])