from hashes.hash_ports_meta_data import hash_ports_meta_data
from hashes.hash_region_to_ships_available import hash_region_to_ships_available


class Port:
    """read only. holds a port's special items(ships, goods, items)"""

    def __init__(self, map_id):
        self.id = map_id + 1
        self.economy_id = hash_ports_meta_data[self.id]['economyId']


    def get_available_ships(self):
        available_ships = hash_region_to_ships_available[self.economy_id]
        return available_ships

if __name__ == '__main__':
    port = Port(28)
    print(port.id)
    print(port.economy_id)
    print(port.get_available_ships())