from role import Role, Ship, Mate


class NpcFleet(Role):
    """npc ships at sea"""
    def __init__(self, name):
        super(NpcFleet, self).__init__(16, 16, name)


if __name__ == '__main__':
    npc = NpcFleet('npc1')

    # add ships
    ship0 = Ship('Reagan', 'Frigate')
    ship1 = Ship('Reagan11', 'Balsa')

    npc.ships.append(ship0)
    npc.ships.append(ship1)

    # add mates
    mate0 = Mate(1)
    mate1 = Mate(2)

    npc.mates.append(mate0)
    npc.mates.append(mate1)


