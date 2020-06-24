from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

PORT = 8100


class Echo(Protocol):
    def connectionMade(self):
        print("new connection!")

    def connectionLost(self, reason):
        print("connection lost!")

    def dataReceived(self, data):
        print("got", data)
        self.transport.write(data)


class EchoFactory(Factory):
    def __init__(self):
        self.users = {}

    def buildProtocol(self, addr):
        return Echo()


reactor.listenTCP(PORT, EchoFactory())
reactor.run()