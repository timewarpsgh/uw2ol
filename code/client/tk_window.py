# add relative directory to python_path
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'code', 'common'))


import tkinter as tk
from tkinter import Entry
import platform

import constants as c


class TkWindow:
    def __init__(self):
        # root window
        self.root = tk.Tk()
        self.root.title("大航海时代2网络版")
        self.root.iconbitmap('../../assets/images/game_icon/ship.ico')
        # frame for pygame
        self.embed = tk.Frame(self.root, width=c.WINDOW_WIDTH, height=c.WINDOW_HIGHT)  # creates embed frame for pygame window
        self.embed.focus_set()
        self.embed.grid(column=0, row=0)  # Adds grid

        os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())
        if platform.system == "Windows":
            os.environ['SDL_VIDEODRIVER'] = 'windib'

        # game
        self.game = None

        # frame for entrybox
        self.uiwin = tk.Frame(self.root, width=400, height=100)
        self.uiwin.grid(row=1, column=0)

        # entry box
        self.text_entry = Entry(self.uiwin, width=20, font=('StSong', 12), foreground='black')
        self.text_entry.state = 'normal'
        self.text_entry.grid(row=0, column=0)

    def update(self):
        self.root.update()

if __name__ == '__main__':
    tk_window = TkWindow()
    tk_window.root.after(0, tk_window.game)
    tk_window.root.mainloop()