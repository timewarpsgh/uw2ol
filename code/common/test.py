import random

dict_1 = dict.fromkeys(range(10))

dict_2 = dict.fromkeys(range(10))

print(dict_1, dict_2)

a = dict_1.keys() - dict_2.keys()
print(a)

if a:
    print(1)
else:
    print(2)