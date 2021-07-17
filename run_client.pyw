import os
os.chdir("code/client")

from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor, threads, defer

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'code', 'common'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'code', 'client'))


# import from common(dir)
from protocol import MyProtocol
from role import Role, Ship, Mate
from game import Game
from tk_window import TkWindow
import constants as c

from twisted.internet.task import LoopingCall
import pygame


class Echo(Protocol):
    def __init__(self, game):
        self.game = game
        # send connection to game
        self.game.get_connection(self)

    def connectionMade(self):
        print('connected')

        # init data buffer
        self.dataBuffer = bytes()

        # get user input (IO handled by thread)
        d = self._get_deferred_user_input()
        d.addCallback(self._send_and_get_next_input)

        # send version
        self.send('version', [c.VERSION])

    def _get_deferred_user_input(self):
        d = threads.deferToThread(self._get_input)
        return d

    def _get_input(self):
        got_input = input()
        return got_input

    def _send_and_get_next_input(self, user_input):
        # parse user input
        parts = user_input.split()
        pck_type = parts[0]
        message_obj = parts[1:]

        # special (convert number to str)
        if pck_type == 'change_map':
            message_obj[0] = str(message_obj[0])
            self.game.connection.send(pck_type, message_obj)
        else:
            # send to server
            self.game.change_and_send(pck_type, message_obj)

        # get user input again
        d = self._get_deferred_user_input()
        d.addCallback(self._send_and_get_next_input)

    def connectionLost(self, reason):
        print("lost connection")

    def dataReceived(self, data):
        """combine data to get packet"""
        print("got", "server data:", data)
        # append to buffer
        self.dataBuffer += data
        print("buffer size", len(self.dataBuffer))

        # if buffer size less than packet length
        if len(self.dataBuffer) < c.HEADER_SIZE:
            return

        # while there's anything in dataBuffer(may get two packets at once)
        while self.dataBuffer:

            # read length of packet
            length_pck = int.from_bytes(self.dataBuffer[:c.HEADER_SIZE], byteorder='little')

            # if buffer size < header + packet length
            if len(self.dataBuffer) < c.HEADER_SIZE + length_pck:
                return

            # get pck
            pck = self.dataBuffer[c.HEADER_SIZE:c.HEADER_SIZE + length_pck]
            print('got packet')

            # pass pck to pck_handler
            self._pck_received(pck)

            # delete already read bytes
            self.dataBuffer = self.dataBuffer[c.HEADER_SIZE + length_pck:]

    def _pck_received(self, pck):
        # get packet type and message object
        p = MyProtocol(pck)
        pck_type = p.get_str()
        print("got pck type from server:", pck_type)
        message_obj = p.get_obj()
        print("server message obj: ", message_obj)

        # send type and message to game
        self.game.pck_received(pck_type, message_obj)

    def send(self, protocol_name, content_obj):
        """send packet to server"""
        # make packet
        p = MyProtocol()
        p.add_str(protocol_name)
        p.add_obj(content_obj)
        data = p.get_pck_has_head()

        # send packet
        self.transport.write(bytes(data))
        print("sending to server:", protocol_name, content_obj)


class EchoClientFactory(ClientFactory):
    def __init__(self, game):
        self.game = game

    def buildProtocol(self, addr):
        print('Connected.')
        return Echo(self.game)

    def startedConnecting(self, connector):
        print('Started to connect.')

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)
        self.game.button_click_handler. \
            make_message_box("Lost Connection!")

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)
        self.game.button_click_handler. \
            make_message_box(
            "Failed to connect! The server isn't working. Please exit.")

def main():
    # print?
    if c.DAEMON_MODE:
        f = open(os.devnull, 'w')
        sys.stdout = f

    # init game and schedule game loop
    tk_window = TkWindow()
    game = Game()
    tk_window.game = game
    game.text_entry = tk_window.text_entry
    game.embed = tk_window.embed
    game.root = tk_window.root

    # bind return for entry
    def send_speach(event):
        msg = game.text_entry.get()
        if msg:
            # speak to nearby players
            if msg.startswith('/w'):
                print('speaking to world!')
                msg = msg[2:]
                game.connection.send('speak_to_world', [msg])
            else:
                game.change_and_send('speak', [msg])

            # clear text_entry
            game.text_entry.delete(0, "end")
            game.embed.focus()
            game.text_entry_active = False
        else:
            game.text_entry.focus()
            game.text_entry_active = True
    game.text_entry.bind_all('<Return>', send_speach)

    # ticks for tk and game
    def update_tk_and_game():
        try:
            tk_window.update()
        except:
            reactor.stop()
            self.root.quit()
            pygame.quit()
            sys.exit()
        game.update()

    tick = LoopingCall(update_tk_and_game)
    tick.start(1.0 / c.FPS)

    tick2 = LoopingCall(game.update_roles_positions)
    tick2.start(c.MOVE_TIME_INVERVAL)

    # remote or local connection
    host = None
    port = None
    if c.REMOTE_ON:
        host = c.REMOTE_HOST
        port = c.REMOTE_PORT
    else:
        host = c.HOST
        port = c.PORT

    # pass game to factory and run reactor
    reactor.connectTCP(host, port, EchoClientFactory(game))
    reactor.run()

if __name__ == "__main__":
    main()
