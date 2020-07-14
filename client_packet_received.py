from role import Role, Ship, Mate


def process_packet(self, pck_type, message_obj):
    if pck_type == 'your_role_data_and_others':
        # my role
        print("got my role data")
        my_role = message_obj[0]
        self.my_role = my_role
        print("my role's x y:", my_role.x, my_role.y, my_role.map, my_role.name)

        if my_role.map.isdigit():
            port_index = int(my_role.map)
            self.port_piddle, self.images['port'] = self.map_maker.make_port_piddle_and_map(port_index)

        # other roles
        other_roles = message_obj[1]
        for role in other_roles:
            self.other_roles[role.name] = role
        print(other_roles)

    elif pck_type == 'new_role':
        new_role = message_obj
        self.other_roles[new_role.name] = new_role
        print("got new role named:", new_role.name)

    elif pck_type == 'logout':
        name_of_logged_out_role = message_obj
        del self.other_roles[name_of_logged_out_role]

    elif pck_type == 'roles_in_new_map':
        roles_in_new_map = message_obj
        self.my_role = roles_in_new_map[self.my_role.name]
        del roles_in_new_map[self.my_role.name]
        self.other_roles = roles_in_new_map

    elif pck_type == 'role_disappeared':
        name_of_role_that_disappeared = message_obj
        del self.other_roles[name_of_role_that_disappeared]

    elif pck_type == 'roles_disappeared':
        names_of_roles_that_disappeared = message_obj
        for name in names_of_roles_that_disappeared:
            del self.other_roles[name]

    elif pck_type == 'roles_in_battle_map':
        roles_in_battle_map = message_obj
        self.other_roles = {}
        for name, role in roles_in_battle_map.items():
            if name == self.my_role.name:
                self.my_role = role
            else:
                self.other_roles[name] = role

            # set game and in client to role
            role.in_client = True


    elif pck_type == 'new_roles_from_battle':
        new_roles_from_battle = message_obj
        for name, role in new_roles_from_battle.items():
            self.other_roles[name] = role

    # sync packets
    elif pck_type in Role.__dict__:
        list = message_obj
        name = list.pop()
        func_name = pck_type
        if name in self.other_roles:
            role = self.other_roles[name]
            print("trying", func_name, list, "for", name)
            func = getattr(role, func_name)
            func(list)