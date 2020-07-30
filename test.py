import time

def aa(b):
    print(b)

def foo(b):
    print(b)
    time.sleep(1)
    aa(b)

a = foo(5)
print(a)