from hashes.hash_ports_meta_data import hash_ports_meta_data
from hashes.hash_region_to_ships_available import hash_region_to_ships_available
from hashes.hash_markets_price_details import hash_markets_price_details
from hashes.hash_special_goods import hash_special_goods

class Port:
    """read only. holds a port's special items(ships, goods, items)"""

    def __init__(self, map_id):
        self.id = map_id + 1
        self.economy_id = hash_ports_meta_data[self.id]['economyId']


    def get_available_ships(self):
        available_ships = hash_region_to_ships_available[self.economy_id]
        return available_ships

    def get_availbale_goods_dict(self):
        # normal goods
        available_goods_dict = hash_markets_price_details[self.economy_id]['Available_items']

        # special goods
        specialty_name = hash_special_goods[self.id]['specialty']
        buy_price = hash_special_goods[self.id]['price']
        available_goods_dict[specialty_name] = [buy_price, 0]

        return available_goods_dict

    def get_commodity_buy_price(self, commodity_name):
        buy_price = self.get_availbale_goods_dict()[commodity_name][0]
        return buy_price

    def get_commodity_sell_price(self, commodity_name):
        sell_price = hash_markets_price_details[self.economy_id][commodity_name][1]
        return sell_price

if __name__ == '__main__':
    port = Port(28)
    print(port.id)
    print(port.economy_id)
    print(port.get_available_ships())