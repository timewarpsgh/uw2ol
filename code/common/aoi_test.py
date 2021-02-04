class AOIManager:
    """Area of Interest Manager reads and changes players and npcs positions(map, grid, x, y)"""
    def __init__(self):
        # each num is grid index
        self.sea = {
            0:{'xx'},
            1:{},
        }

        # map_id 0 - 130, each port has many grids
        self.ports = {}
        for i in range(131):
            self.ports[i] = {
                0:{'aa'},
                1:{},

            }

        # keys are the names of initiators
        self.battle_fields = {
            'alex':{'bb'}
        }

    def get_roles_in_sea_grid_by_id(self, grid_id):
        # dic is name : conn , conn has my_role
        dic = self.sea[grid_id]
        return dic

    def get_roles_in_port_grid_by_ids(self, map_id, grid_id):
        # dic is name : conn , conn has my_role
        dic = self.ports[map_id][grid_id]
        return dic

    def get_roles_in_battle_by_player_name(self, name):
        # dic is name : conn , conn has my_role
        dic = self.battle_fields[name]
        return dic

if __name__ == '__main__':
    aoi_manager = AOIManager()
    a = aoi_manager.get_roles_in_sea_grid_by_id(0)
    b = aoi_manager.get_roles_in_port_grid_by_ids(29, 0)
    c = aoi_manager.get_roles_in_battle_by_player_name('alex')
    print(a)
    print(b)
    print(c)