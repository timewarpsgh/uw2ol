from role import *

class AA:
    def __init__(self):
        self.f1 = 1

    def _get(self):
        return self.f1

    def __get(self):
        return self.f1


if __name__ == '__main__':
   a = AA()
   b = a._get()
   print(b)