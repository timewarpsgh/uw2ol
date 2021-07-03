from multiprocessing import Process
import time


def main():
    while 1:
        time.sleep(1)
        print(1)



class ClientProcess(Process):
    def __init__(self):
        Process.__init__(self)

    def run(self):
        main()


if __name__ == "__main__":
    # start clients
    for i in range(2, 10):
        p = ClientProcess()
        p.start()
        time.sleep(1)
