from tkinter import Tk
from  tkinter import messagebox

root = Tk()
# 当点击右上角退出时，执行的程序
def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

root.config(cursor='dotbox #ff0000 #ff0000')

# WM_DELETE_WINDOW 不能改变，这是捕获命令
root.protocol('WM_DELETE_WINDOW', on_closing)
root.mainloop()
