if self.game.my_role.map != 'sea' and self.game.my_role.ships:
    # make sea image
    port_tile_x = hash_ports_meta_data[int(self.game.my_role.map) + 1]['x']
    port_tile_y = hash_ports_meta_data[int(self.game.my_role.map) + 1]['y']
    print(port_tile_x, port_tile_y)

    self.game.images['sea'] = self.game.map_maker.make_partial_world_map(port_tile_x, port_tile_y)

    # send
    self.game.connection.send('change_map', ['sea'])

    # init timer at sea

    # max days at sea (local game variable, not in role)
    self.game.max_days_at_sea = self.game.my_role.calculate_max_days_at_sea()
    self.game.days_spent_at_sea = 0
    # timer
    self.game.timer_at_sea = task.LoopingCall(pass_one_day_at_sea, self.game)
    self.game.timer_at_sea.start(c.ONE_DAY_AT_SEA_IN_SECONDS)