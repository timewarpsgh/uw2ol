x = {'a': 1}

y = {'b': 3, 'c': 4}

z = {'d':5}

grids = [x, y, z]

dic = {}
for grid in grids:
    dic = {**dic, **grid}


print(dic)