from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor, threads, defer

from protocol import MyProtocol
from role import Role, Ship, Mate
from game import Game
import constants as c


from twisted.internet.task import LoopingCall
import pygame
import sys




HEADER_SIZE = 4


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

        # send to server
        self.send(pck_type, message_obj)

        # get user input again
        d = get_user_input()
        d.addCallback(self.send_and_get_next_input)

    def connectionLost(self, reason):
        print("lost")

    def dataReceived(self, data):
        """combine data to get packet"""
        print("got", data)

        # append to buffer
        self.dataBuffer += data

        # if buffer size less than packet length
        if len(self.dataBuffer) < HEADER_SIZE:
            return

        # read length of packet
        length_pck = int.from_bytes(self.dataBuffer[:HEADER_SIZE], byteorder='little')

        # if buffer size < header + packet length
        if len(self.dataBuffer) < HEADER_SIZE + length_pck:
            return

        # 截取封包
        pck = self.dataBuffer[HEADER_SIZE:HEADER_SIZE + length_pck]
        print('got packet')

        # 把封包交给处理函数
        self.pck_received(pck)

        # 删除已经读取的字节
        self.dataBuffer = self.dataBuffer[HEADER_SIZE + length_pck:]

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

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)

def main():
    # init game and schedule game loop
    game = Game()
    tick = LoopingCall(game.update)
    tick.start(1.0 / c.FPS)

    # pass game to factory and run reactor
    reactor.connectTCP(c.HOST, c.PORT, EchoClientFactory(game))
    reactor.run()

if __name__ == "__main__":
    main()