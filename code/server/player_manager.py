# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

import random
from twisted.internet import reactor, task, defer


class PlayerManager:
    def __init__(self):
        """name : conn(echo)"""
        self.players_dic = {}

    def add_player(self, conn):
        self.players_dic[conn.my_role.name] = conn
        print('added p!')

    def remove_player(self, name):
        del self.players_dic[name]
        print('removed p')

    def get_player_conn_by_name(self, name):
        if name in self.players_dic:
            print(name, 'is online!')
            return self.players_dic[name]
        else:
            return None

    def get_all_palyers_dict(self):
        return self.players_dic
