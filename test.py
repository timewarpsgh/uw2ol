from hashes.hash_ports_meta_data import hash_ports_meta_data

now_position_on_board = (1, 2)

# get all buildings' positions in this map
dict = {
    (1, 2): 'market',
    (2, 3): 'bar',
}

# is now position in buildings' positions
if now_position_on_board in dict:
    print("enter", dict[now_position_on_board])