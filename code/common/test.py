new_deltas = [['-1', -1], 1, 1, '1', '1']

for index, delta in enumerate(new_deltas):
    if index == 0:
        list = new_deltas[index]
        for id, inner_delta in enumerate(list):
            if isinstance(inner_delta, str):
                list[id] = int(inner_delta) * 16
    else:
        if isinstance(delta, str):
            new_deltas[index] = int(delta) * 16

print(new_deltas)