from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, threads, defer, task

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'client'))

# import from common(dir)
from protocol import MyProtocol
from DBmanager import Database
from role import Role
import constants as c
from hashes.hash_ports_meta_data import hash_ports_meta_data
import server_packet_received
from npc_manager import NpcManager
from AOI_manager import AOIManager

# import from client
from map_maker import MapMaker

class Echo(Protocol):
    """one server for each client"""
    def __init__(self, factory):
        super(Echo).__init__()
        self.factory = factory
        self.my_role = None

    def connectionMade(self):
        # init data buffer
        self.dataBuffer = bytes()
        print("new connection!")

    def connectionLost(self, reason):
        print("connection lost!")

        if self.my_role:

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
            if account.isdigit():
                pass
            else:
                role_to_save = self.my_role
                d = threads.deferToThread(self.factory.db.save_character_data, account, role_to_save)

        # delete from users dict and tell nearby clients that you logged out
        map = self.factory.aoi_manager.get_map_by_player(self.my_role)
        self.send_to_other_clients('logout', self.my_role.name)
        map.remove_player(self.my_role)

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
        """send packet to nearby players"""
        map = self.factory.aoi_manager.get_map_by_player(self.my_role)
        nearby_players = map.get_nearby_players_by_player(self.my_role)
        for name, conn in nearby_players.items():
            if name.isdigit():
                pass
            else:
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
        # world map matrix
        map_maker = MapMaker()
        map_maker.set_world_piddle()
        self.world_map_matrix = map_maker.world_map_piddle

        # aoi
        self.aoi_manager = AOIManager()
        Role.AOI_MANAGER = self.aoi_manager
        Role.FACTORY = self

        # npcs
        self.npc_manager = NpcManager(self.aoi_manager)
        sea_map = self.aoi_manager.get_sea_map()
        for name, npc in self.npc_manager.get_all_npcs().items():
            sea_map.add_npc(npc)

        # npc control loop
        looping_task = task.LoopingCall(self.npc_manager.update)
        looping_task.start(0.5)

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