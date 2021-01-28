from multiprocessing import Process
import time


# 定义线程类
class ClockProcess(Process):
    def __init__(self, interval):
        Process.__init__(self)
        self.interval = interval

    def run(self):
        print('子进程开始执行的时间:{}'.format(time.ctime()))
        time.sleep(self.interval)
        print('子进程结束的时间:{}'.format(time.ctime()))


if __name__ == '__main__':
    # 创建子进程
    p1 = ClockProcess(1)
    p2 = ClockProcess(2)
    # 调用子进程
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print('主进程结束')