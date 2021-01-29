from role import Role, Ship, Mate


def init_npcs():
    npcs = {}
    npc_count = 100 #max is 150 atm due to max protocol size
    for i in range(1,(npc_count + 1)):
        # now role
        npc = Role(14400, 4208, str(i))
        npc.map = 'sea'

        # add mate and ship
        mate0 = Mate(1)
        ship0 = Ship('Reagan', 'Frigate')
        ship0.crew = 20
        npc.ships.append(ship0)
        mate0.set_as_captain_of(ship0)
        npc.mates.append(mate0)

        mate1 = Mate(2)
        ship1 = Ship('Reagan1', 'Frigate')
        ship1.crew = 20
        npc.ships.append(ship1)
        mate1.set_as_captain_of(ship1)
        npc.mates.append(mate1)

        # store in dict
        npcs[str(i)] = npc

    return npcs
