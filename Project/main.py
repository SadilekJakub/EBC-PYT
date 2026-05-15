import tkinter as tk
import ttkbootstrap as ttk

from database import *
from database_manager import *
from gui import GUI

THEME = "darkly"
if __name__ == '__main__':
    conn = sqlite3.connect('data.db')

    init_database(conn)
    setup_defaults(conn)

    root = ttk.Window(themename=THEME)
    app = GUI(root,conn)
    root.mainloop()
