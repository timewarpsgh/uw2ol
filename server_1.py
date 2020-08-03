from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, threads, defer

from protocol import MyProtocol
from DBmanager import Database
from role import Role
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data
import server_packet_received


import os
import sys


class Echo(Protocol):
    def __init__(self, factory):
        super().__init__()
        # each connection knows the factory
        self.factory = factory

    def connectionMade(self):
        # init data buffer
        self.dataBuffer = bytes()

        print("new connection!")

    def connectionLost(self, reason):
        print("connection lost!")

        # get current map
        my_map = str(self.my_role.map)

        # if not in battle
        if my_map.isdigit() or my_map == 'sea':
            pass
        # if in battle
        else:
            server_packet_received.exit_battle(self, '')

        self.log_role_out()

    def log_role_out(self):
        # set online to false
        account = self.account
        d = threads.deferToThread(self.factory.db.set_online_to_false, account)

        # save role to DB
        if c.SAVE_ON_CONNECTION_LOST:
            account = self.account
            role_to_save = self.my_role
            d = threads.deferToThread(self.factory.db.save_character_data, account, role_to_save)

        # delete from users dict and tell clients that you logged out
        del self.factory.users[self.my_role.map][self.my_role.name]

        for conn in self.factory.users[self.my_role.map].values():
            conn.send('logout', self.my_role.name)

    def dataReceived(self, data):
        """combine data to get packet"""
        print("got", data)
        self.dataBuffer += data

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

        # process packet_type and message_object
        server_packet_received.process_packet(self, pck_type, message_obj)

    def send(self, protocol_name, content_obj='na'):
        """send packet to server"""
        # make packet
        p = MyProtocol()
        p.add_str(protocol_name)
        p.add_obj(content_obj)
        data = p.get_pck_has_head()

        # send packet
        self.transport.write(data)
        print("transport just wrote:", protocol_name, content_obj)

    def send_to_other_clients(self, protocol_name, content_obj='na'):
        """send packet to all clients in same map"""
        for name, conn in self.factory.users[self.my_role.map].items():
            if name != self.my_role.name:
                conn.send(protocol_name, content_obj)

    ###################### callbacks  ###########################
    ###################### need self when using deffered.addCallBack  ###########################
    def on_create_character_got_result(self, is_ok):
        server_packet_received.on_create_character_got_result(self, is_ok)

    def on_register_got_result(self, is_ok):
        server_packet_received.on_register_got_result(self, is_ok)

    def on_login_got_result(self, account):
        server_packet_received.on_login_got_result(self, account)

    def on_get_character_data_got_result(self, role):
        server_packet_received.on_get_character_data_got_result(self, role)


class EchoFactory(Factory):
    def __init__(self):
        # users at sea map
        self.users = {
            'sea':{},
        }

        # users in ports
        for i in range(101):
            self.users[str(i)] = {}

        # db
        self.db = Database()

    def buildProtocol(self, addr):
        return Echo(self)

def main():
    # print?
    if c.DAEMON_MODE:
        f = open(os.devnull, 'w')
        sys.stdout = f

    # reactor
    print("Listening...")
    reactor.suggestThreadPoolSize(30)
    reactor.listenTCP(c.PORT, EchoFactory())
    reactor.run()

main()