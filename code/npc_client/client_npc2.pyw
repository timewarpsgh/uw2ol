from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor, threads, defer

# 1 process for 1 client
from multiprocessing import Process

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# import from common(dir)
from protocol import MyProtocol
from role import Role, Ship, Mate
from game import Game
import constants as c

from twisted.internet.task import LoopingCall
import pygame


def get_input():
    got_input = input()
    return got_input


def get_user_input():
    d = threads.deferToThread(get_input)
    return d


class Echo(Protocol):
    def __init__(self, game):
        self.game = game
        # send connection to game
        self.game.get_connection(self)

    def connectionMade(self):
        # init data buffer
        self.dataBuffer = bytes()

        print('connected')
        d = get_user_input()
        d.addCallback(self.send_and_get_next_input)

    def send_and_get_next_input(self, user_input):
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
        d = get_user_input()
        d.addCallback(self.send_and_get_next_input)

    def connectionLost(self, reason):
        print("lost")

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

            # 截取封包
            pck = self.dataBuffer[c.HEADER_SIZE:c.HEADER_SIZE + length_pck]
            print('got packet')

            # 把封包交给处理函数
            self.pck_received(pck)

            # 删除已经读取的字节
            self.dataBuffer = self.dataBuffer[c.HEADER_SIZE + length_pck:]

    def pck_received(self, pck):
        # get packet type and message object
        p = MyProtocol(pck)
        pck_type = p.get_str()
        print("got pck type:", pck_type)
        message_obj = p.get_obj()
        print("message obj: ", message_obj)

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
        self.transport.write(data)
        print("transport just wrote:", protocol_name, content_obj)


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
            make_message_box("Failed to connect! The server isn't working. Please exit.")


def main(ac, psw):
    # print?
    if c.DAEMON_MODE:
        f = open(os.devnull, 'w')
        sys.stdout = f

    # init game and schedule game loop
    game = Game(ac, psw)

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
    try:
        reactor.connectTCP(host, port, EchoClientFactory(game))
    except:
        print("can't connect to server.")
    else:
        reactor.run()


class ClientProcess(Process):
    def __init__(self, ac, psw):
        Process.__init__(self)
        self.ac = ac
        self.psw = psw

    def run(self):
        main(self.ac, self.psw)


if __name__ == "__main__":
    # Create new threads
    for i in range(2, 9):
        p = ClientProcess(str(i), str(i))
        p.start()


