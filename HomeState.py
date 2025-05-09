import socket
import json
import tkinter as tk
from tkinter import PhotoImage
import threading
import time
from GroupState import GroupState
from State import State


class HomeState(State):
    def __init__(self, engine):
        super().__init__(engine)

        self.frame = tk.Frame(self.engine.root, bg="#DED1D1")
        self.frame.place(relwidth=1, relheight=1)

        # Title label
        title_label = tk.Label(self.frame, text="Select Your Group", font=("Helvetica", 28, "bold"),
                               bg="#DED1D1", fg="#00B1E2")
        title_label.pack(pady=30)

        # Add Group Button
        add_group_img = PhotoImage(file="Assets/add_group.png")  # Ensure correct path for image
        add_group_button = tk.Button(self.frame,
                                     image=add_group_img,  # Set image for the button
                                     bg="#DED1D1",
                                     command=self.open_add_group_popup,
                                     activebackground="#DED1D1",
                                     bd=0)
        add_group_button.image = add_group_img  # Keep a reference to avoid garbage collection
        add_group_button.place(x=30, y=650)

        # Initialize variables to track the x and y positions of the group buttons
        self.group_x_position = 30  # Starting x-position for the first group button
        self.group_y_position = 100  # Starting y-position for the first row of group buttons
        self.groups_in_current_line = 0  # Counter for groups in the current line

        # Store the group buttons for easy tracking later if needed
        self.group_buttons = []

        # Start a background thread to refresh groups every 5 seconds
        self.start_group_refresh_thread()

    def start_group_refresh_thread(self):
        """Start a thread to refresh the groups every 5 seconds."""
        refresh_thread = threading.Thread(target=self.refresh_groups_periodically)
        refresh_thread.daemon = True  # Daemon thread will automatically close when the main program exits
        refresh_thread.start()

    def refresh_groups_periodically(self):
        """Periodically refresh groups from the server every 5 seconds."""
        while True:
            self.load_groups_from_server()
            time.sleep(5)  # Wait for 5 seconds before refreshing again

    def load_groups_from_server(self):
        """Load groups from the server and create buttons for them."""
        groups = self.engine.client.receive_groups()

        # Create a set of existing group names to avoid duplicates
        existing_groups = {button.cget("text") for button in self.group_buttons}

        for group in groups:
            print(f"Received group: {group}")  # Debug print to check the group format
            if isinstance(group, dict) and "name" in group:
                group_name = group["name"]
                if group_name not in existing_groups:
                    self.add_group_button(group_name)
                    existing_groups.add(group_name)  # Add group to the set of existing groups
                else:
                    print(f"Group '{group_name}' already exists.")  # Debug message for existing group
            else:
                print(f"Invalid group format: {group}")  # If the format is invalid

    def open_add_group_popup(self):
        self.popup = tk.Toplevel(self.engine.root)
        self.popup.title("Create Group")
        self.popup.geometry("300x220")

        label_name = tk.Label(self.popup, text="Group Name:", font=("Helvetica", 14))
        label_name.pack(pady=5)
        self.group_name_entry = tk.Entry(self.popup, font=("Helvetica", 14))
        self.group_name_entry.pack(pady=5)

        label_pass = tk.Label(self.popup, text="Password:", font=("Helvetica", 14))
        label_pass.pack(pady=5)
        self.group_password_entry = tk.Entry(self.popup, font=("Helvetica", 14), show="*")
        self.group_password_entry.pack(pady=5)

        submit_button = tk.Button(self.popup, text="Create Group", font=("Helvetica", 14),
                                  command=self.add_group_from_popup)
        submit_button.pack(pady=10)

    def add_group_from_popup(self):
        group_name = self.group_name_entry.get().strip()
        group_password = self.group_password_entry.get().strip()

        if group_name and group_password:
            self.add_group_button(group_name)
            print(f"{group_name} button added.")
            self.engine.client.add_group(group_name, group_password)
        else:
            print("Group name and password cannot be empty!")

        self.popup.destroy()

    def add_group_button(self, group_name):
        """Create and add a group button."""
        # Create a button for the group with the entered name
        group_button = tk.Button(self.frame, text=group_name, font=("Helvetica", 16), bg="#7D7979", fg="white", width=20, bd=0, activebackground="#7D7979",
                                 height=5, command=lambda group=group_name: self.on_group_click(group))

        # Place the group button at the current x and y positions
        group_button.place(x=self.group_x_position, y=self.group_y_position)

        # Add the button to the list of group buttons
        self.group_buttons.append(group_button)

        # Update the x position for the next group button (300px apart)
        self.group_x_position += group_button.winfo_width() + 300  # 20px gap between buttons
        self.groups_in_current_line += 1  # Increment the counter for the current line

        # Check if we have added 4 groups in the current row
        if self.groups_in_current_line >= 4:
            # Reset x position to start from the left again
            self.group_x_position = 30
            # Move the y position to the next row (increase by 60px for the new row)
            self.group_y_position += group_button.winfo_height() + 200  # 20px gap between rows
            # Reset the counter for groups in the current line
            self.groups_in_current_line = 0

    def on_group_click(self, group_name):
        password_popup = tk.Toplevel(self.engine.root)
        password_popup.title("Enter Password")
        password_popup.geometry("300x150")

        label = tk.Label(password_popup, text=f"Password for {group_name}:", font=("Helvetica", 14))
        label.pack(pady=10)

        password_entry = tk.Entry(password_popup, font=("Helvetica", 14), show="*")
        password_entry.pack(pady=10)

        def submit_password():
            password = password_entry.get()
            if self.engine.client.verify_group_password(group_name, password):
                password_popup.destroy()
                from GroupState import GroupState
                self.engine.push_state(GroupState(self.engine, group_name))
            else:
                print("Incorrect password")

        submit_button = tk.Button(password_popup, text="Enter", font=("Helvetica", 14), command=submit_password)
        submit_button.pack(pady=10)

    def destroy(self):
        self.frame.destroy()
