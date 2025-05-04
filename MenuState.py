from State import State
from LogInState import LogInState
from PIL import Image, ImageTk
import tkinter as tk


class MenuState(State):
    def __init__(self, engine):
        super().__init__(engine)

        # Load the background image
        image = Image.open("Assets/bgForMenu.png")
        self.bg_image = ImageTk.PhotoImage(image)

        # Create a Tkinter canvas
        self.canvas = tk.Canvas(self.engine.root, width=self.engine.width, height=self.engine.height)
        self.canvas.place(x=0, y=0)

        # Set up the background
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image)

        # Draw menu text
        self.canvas.create_text(self.engine.width // 2, self.engine.height // (4/3),
                                text="Press 'Space' to Start", font=("Arial", 24), fill="white")

        # Bind key press event to the canvas
        self.engine.root.bind("<KeyPress-space>", self.handle_events)

    def handle_events(self, event):
        if event.keysym == "space":
            print("Starting Game...")
            self.engine.push_state(LogInState(self.engine))

    def update(self):
        pass  # Nothing needs updating in the MenuState

