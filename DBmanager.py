import pymysql
import pickle
from role import Role
from role import Ship
from role import Mate


class Database:
    def __init__(self):
        self.db = pymysql.connect("127.0.0.1", "root", "dab9901025", "py_test")
        self.cursor = self.db.cursor()

    # accounts table
    def register(self, account, password):

        # check if account already exists
        sql_read = "SELECT * FROM accounts WHERE name = '{}'".format(account)
        self.cursor.execute(sql_read)
        rows = self.cursor.fetchall()

        # if exists
        if rows:
            print("account already exists!" )
            return False

        # not exist
        else:
            sql_insert = "insert into accounts(name,pw) values('{}','{}')".format(account, password)
            self.cursor.execute(sql_insert)
            self.db.commit()
            print("new account added!")
            return True

    def login(self, account, password):

        # check if such a row exists
        sql_read = "SELECT * FROM accounts WHERE name = '{}' and pw = '{}'".format(account, password)
        self.cursor.execute(sql_read)
        rows = self.cursor.fetchall()

        # if exits
        if rows:
            print("login success!" )
            id = rows[0][0]
            return id, account
        else:
            print("account or password wrong!")
            return 0, 0
        pass

    # data table
    def create_character(self, id, account, character_name):

        # exists?
        try:
            player = pickle.load(open("data/save." + account, "rb"))
            print("exists!")

        # no
        except:
            default_role = Role(5,5,character_name)
            ship0 = Ship('Reagan', 'Frigate')
            ship1 = Ship('Reagan11', 'Balsa')
            ship2 = Ship('Reagan22', 'Balsa')
            ship3 = Ship('Reagan33', 'Balsa')
            default_role.ships.append(ship0)
            default_role.ships.append(ship1)
            default_role.ships.append(ship2)
            default_role.ships.append(ship3)
            mate0 = Mate('Gus Johnson', 'England')
            mate1 = Mate('Mike Dickens', 'Holland')
            default_role.mates.append(mate0)
            default_role.mates.append(mate1)

            pickle.dump(default_role, open("data/save." + account, "wb"))
            print("new player created!")


    def get_character_data(self, account):
        try:
            player = pickle.load(open("data/save." + account, "rb"))
            return player
        except:
            return False

    def save_character_data(self, account, player):
        pickle.dump(player, open("data/save." + account, "wb"))
        print("saved!")

if __name__ == '__main__':
    db = Database()
    # db.register('test2', 'a9901025')
    id, account = db.login('test1', 'a9901025')
    db.create_character(id, account, "biteyou12")
    player = db.get_character_data(account)
    print(player.name)
    player.name = 'new_name'

    db.save_character_data(account, player)

