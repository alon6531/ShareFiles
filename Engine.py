import tkinter as tk
from MenuState import *
from tkinterdnd2 import TkinterDnD

class Engine:
    def __init__(self, client, width=1280, height=720, title="Engine with States"):
        self.client = client
        self.width = width
        self.height = height
        self.root = TkinterDnD.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")

        self.canvas = tk.Canvas(self.root, width=width, height=height, bg="white")
        self.canvas.pack()

        self.running = True

        # State stack
        self.states = []

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Key>", self.handle_events)

        self.root.after(16, self.update)

        self.push_state(MenuState(self))

    def push_state(self, state):
        self.states.append(state)

    def pop_state(self):
        if self.states:
            self.states.pop()

    def current_state(self):
        return self.states[-1] if self.states else None

    def handle_events(self, event):
        state = self.current_state()
        if state:
            state.handle_events(event)

    def update(self):
        if not self.running:
            return

        state = self.current_state()
        if state:
            state.update()
            self.canvas.delete("all")

        self.root.after(16, self.update)

    def on_close(self):
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()

