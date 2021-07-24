from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, threads, defer, task
from twisted.internet.task import LoopingCall

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
from player_manager import PlayerManager

# import from client
from map_maker import MapMaker

class Echo(Protocol):
    """one server for each client"""
    def __init__(self, factory):
        super(Echo).__init__()
        self.factory = factory
        self.my_role = None
        self.account = None

    def connectionMade(self):
        print("new connection!")
        # init data buffer
        self.dataBuffer = bytes()

    def connectionLost(self, reason):
        print("connection lost!")
        my_role = self.my_role
        if my_role:
            if my_role.is_in_port():
                self._log_role_out()

            elif my_role.is_at_sea():
                reactor.callLater(5, self._lost_conn_when_at_sea)

            elif my_role.is_in_battle():
                self.auto_fight_loop = LoopingCall(self.__auto_fight)
                self.auto_fight_loop.start(10)

    def _lost_conn_when_at_sea(self):
        my_role = self.my_role
        if my_role.is_at_sea() or my_role.is_in_port():
            # back to prev port
            prev_port_str = str(my_role.prev_port_map_id)
            server_packet_received.change_map(self, [prev_port_str])
            self._log_role_out()
        elif my_role.is_in_battle:
            self.auto_fight_loop = LoopingCall(self.__auto_fight)
            self.auto_fight_loop.start(10)

    def __auto_fight(self):
        if self.auto_fight_loop.running:
            my_role = self.my_role

            if my_role.is_in_battle():
                if my_role.your_turn_in_battle:
                    server_packet_received.process_packet(self, 'all_ships_operate', [])
            elif my_role.is_in_port():
                self._log_role_out()
                self.auto_fight_loop.stop()
            elif my_role.is_at_sea():
                prev_port_str = str(my_role.prev_port_map_id)
                server_packet_received.change_map(self, [prev_port_str])
                self._log_role_out()
                self.auto_fight_loop.stop()

    def _log_role_out(self):
        print(f'logging role out. {self.my_role.name}')
        # set online to false
        account = self.account
        d = threads.deferToThread(self.factory.db.set_online_to_false, account)

        # save role to DB
        if c.SAVE_ON_CONNECTION_LOST:
            account = self.account
            role_to_save = self.my_role
            d = threads.deferToThread(self.factory.db.save_character_data, account, role_to_save)

        # delete from users dict and tell nearby clients that you logged out
        map = self.factory.aoi_manager.get_map_by_player(self.my_role)
        self.send_to_other_clients('logout', self.my_role.name)
        map.remove_player(self.my_role)
        self.factory.player_manager.remove_player(self.my_role.name)

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
            self._pck_received(pck)

            # 删除已经读取的字节
            self.dataBuffer = self.dataBuffer[c.HEADER_SIZE + length_pck:]

    def _pck_received(self, pck):
        # get packet type and message object
        p = MyProtocol(pck)
        pck_type = p.get_str()
        print("got pck type from client:", pck_type)

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
        self.transport.write(bytes(data))
        print("transport just wrote:", protocol_name, content_obj)

    def send_to_other_clients(self, protocol_name, content_obj='na'):
        """send packet to nearby players"""
        map = self.factory.aoi_manager.get_map_by_player(self.my_role)
        nearby_players = map.get_nearby_players_by_player(self.my_role)

        for name, conn in nearby_players.items():
            if name.isdigit():
                pass
            elif name == self.my_role.name:
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

        # players
        self.player_manager = PlayerManager()

        # npcs
        self.npc_manager = NpcManager(self.aoi_manager)
        sea_map = self.aoi_manager.get_sea_map()
        for name, npc in self.npc_manager.get_all_npcs().items():
            sea_map.add_npc(npc)

        # npc control loop
        looping_task = task.LoopingCall(self.npc_manager.update)
        looping_task.start(0.5)

        # wind wave mgr update loop
        wind_wave_mgr = self.aoi_manager.get_sea_map().get_wind_wave_mgr()
        looping_task = task.LoopingCall(wind_wave_mgr.change)
        looping_task.start(60)

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