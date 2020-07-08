from protocol import MyProtocol
from timeit import timeit
import time

# make packet
protocol_name = 'start_move'
content_obj = [100, 200, 'right']

def make_packet(protocol_name, content_obj):
    p = MyProtocol()
    p.add_str(protocol_name)
    p.add_obj(content_obj)
    data = p.get_pck_has_head()

t1 = time.time()

for i in range(300000):
    make_packet(protocol_name, content_obj)



t2 = time.time()
print(t2 - t1)