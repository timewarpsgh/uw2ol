import random

import itertools

d = {1: 2, 3: 4, 5: 6}

a = dict(itertools.islice(d.items(), 4))

print(a)
print(len(d))
