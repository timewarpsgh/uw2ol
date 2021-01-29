from role import Role, Ship, Mate


def init_npcs():
    npcs = {}
    npc_count = 2 #max is 150 atm due to max protocol size
    for i in range(1,(npc_count + 1)):
        npc = Role(14400, 4208, str(i))
        npc.map = 'sea'
        npcs[str(i)] = npc

    return npcs
