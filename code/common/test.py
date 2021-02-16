import random
import time

li = list(range(10))
dic = {
    1:1,
    2:2,
    3:3,
    4:4,
    5:5,
}

# time = time.time()
# print(time)
#
# random.seed(time)

a = random.choice(list(dic.keys()))
print(a)