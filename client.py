from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor, threads, defer

from protocol import MyProtocol


HOST = 'localhost'
PORT = 8100


def get_input():
    got_input = input()
    return bytes(got_input.encode('utf-8'))

def get_user_input():
    d = threads.deferToThread(get_input)
    return d


class Echo(Protocol):
    def connectionMade(self):
        # init data buffer
        self.dataBuffer = bytes()

        print('connected')
        a = ''
        for i in range(10000):
            a += str(i)
        # a = bytes(a.encode('utf-8'))

        self.send('test', a)


        # self.transport.write(a)
        # self.transport.write(b'hello')
        # d = get_user_input()
        # d.addCallback(self.send_and_get_next_input)

    # def send_and_get_next_input(self, message):
    #     self.transport.write(message)
    #     d = get_user_input()
    #     d.addCallback(self.send_and_get_next_input)

    def send(self, protocol_name, content_obj):
        """send packet to server"""

        # make packet
        p = MyProtocol()
        p.add_str(protocol_name)
        p.add_obj(content_obj)
        data = p.get_pck_has_head()

        # send packet
        self.transport.write(data)

    def connectionLost(self, reason):
        print("lost")

    def dataReceived(self, data):
        print("got", data)
        # d = get_user_input()
        # d = d.addCallback(self.transport.write)
        # d.addCallback(get_user_input)

class EchoClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected.')
        return Echo()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)


reactor.connectTCP(HOST, PORT, EchoClientFactory())
reactor.run()