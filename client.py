from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor, threads, defer


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
        a = ''
        for i in range(6000):
            a += str(i)
        a = bytes(a.encode('utf-8'))
        self.transport.write(a)
        # self.transport.write(b'hello')
        d = get_user_input()
        d.addCallback(self.send_and_get_next_input)

    def send_and_get_next_input(self, message):
        self.transport.write(message)
        d = get_user_input()
        d.addCallback(self.send_and_get_next_input)

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