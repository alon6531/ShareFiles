import threading
import time
import os
import platform
import subprocess
from State import State
import tkinter as tk
from tkinter import PhotoImage
from tkinterdnd2 import DND_FILES, TkinterDnD
import shutil

class GroupState(State):
    def __init__(self, engine, group_name):
        super().__init__(engine)
        self.group_name = group_name

        # Enable DnD support
        self.engine.root.drop_target_register(DND_FILES)

        # List to store file paths (full paths for opening later)
        self.file_paths = []

        # Main frame
        self.frame = tk.Frame(self.engine.root, bg="#ECECEC")
        self.frame.place(relwidth=1, relheight=1)

        # Title bar
        title_bar = tk.Frame(self.frame, bg="#1E88E5", height=50)
        title_bar.pack(fill="x")

        title_label = tk.Label(title_bar, text=f"📁 Group: {group_name}", font=("Helvetica", 16, "bold"),
                               bg="#1E88E5", fg="white")
        title_label.pack(side="left", padx=20)

        back_button = tk.Button(title_bar, text="← Back", font=("Helvetica", 10),
                                bg="#1565C0", fg="white", command=self.back_clicked)
        back_button.pack(side="right", padx=10, pady=5)

        # Content area
        content_frame = tk.Frame(self.frame, bg="#ECECEC")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Folder drop area (left side)
        folder_area = tk.Frame(content_frame, bg="#ECECEC")
        folder_area.pack(side="left", fill="y", padx=10)

        folder_img = PhotoImage(file="Assets/folder.png")
        self.folder_label = tk.Label(folder_area, image=folder_img, bg="#ECECEC", cursor="hand2")
        self.folder_label.image = folder_img
        self.folder_label.pack(pady=10)

        drop_hint = tk.Label(folder_area, text="Drop files here", font=("Helvetica", 12, "italic"),
                             bg="#ECECEC", fg="#555")
        drop_hint.pack(pady=5)

        # File list panel (right side)
        list_panel = tk.Frame(content_frame, bg="#FFFFFF", bd=1, relief="solid")
        list_panel.pack(side="left", fill="both", expand=True, padx=10)

        list_title = tk.Label(list_panel, text="Files", font=("Helvetica", 14, "bold"),
                              bg="#F5F5F5", anchor="w", padx=10)
        list_title.pack(fill="x")

        # Scrollable listbox for files
        listbox_frame = tk.Frame(list_panel, bg="#FFFFFF")
        listbox_frame.pack(fill="both", expand=True)

        self.file_listbox = tk.Listbox(listbox_frame, font=("Helvetica", 12),
                                       bg="white", fg="#333", bd=0, highlightthickness=0, activestyle="none")
        self.file_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(listbox_frame, command=self.file_listbox.yview)
        scrollbar.pack(side="right", fill="y")

        self.file_listbox.config(yscrollcommand=scrollbar.set)

        remove_button = tk.Button(list_panel, text="🗑️ Remove Selected File", font=("Helvetica", 12),
                                  bg="#E53935", fg="white", command=self.remove_selected_file)
        remove_button.pack(fill="x", padx=10, pady=10)

        # Bind drop event
        self.engine.root.dnd_bind('<<Drop>>', self.on_file_drop)

        # Bind double-click to open file
        self.file_listbox.bind("<Double-Button-1>", self.open_selected_file)

        # Periodically call receive_files_from_group every 5 seconds
        self.schedule_file_reception()

    def schedule_file_reception(self):
        """
        Schedule file reception every 5 seconds.
        """
        self.receive_files_from_group()
        # Schedule next call in 5 seconds
        threading.Timer(5, self.schedule_file_reception).start()

    def receive_files_from_group(self):
        """
        Receive all files from the group and display them in the file list, replacing the current list.
        """
        try:
            print(f"Attempting to receive files from group: {self.group_name}")

            # Call the method to receive files from the server
            self.engine.client.receive_all_files(self.group_name)

            # Path to the group's folder
            group_folder_path = os.path.join(self.engine.client.save_dir, self.group_name)
            print(f"Group folder path: {group_folder_path}")

            if os.path.exists(group_folder_path):
                print(f"Folder found, listing files...")

                # Clear the current list
                self.file_listbox.delete(0, tk.END)
                self.file_paths.clear()

                # List and add files
                for filename in os.listdir(group_folder_path):
                    full_file_path = os.path.join(group_folder_path, filename)
                    print(f"Adding file: {filename} at {full_file_path}")

                    self.file_listbox.insert(tk.END, f"📄 {filename}")
                    self.file_paths.append(full_file_path)

                print(f"All files listed.")
            else:
                print(f"Error: Folder {group_folder_path} does not exist.")

        except Exception as e:
            print(f"Error receiving files: {e}")

    def on_file_drop(self, event):
        files = self.engine.root.tk.splitlist(event.data)
        for file_path in files:
            if file_path not in self.file_paths:  # Avoid duplicate files
                self.engine.client.send_file(file_path, self.group_name)
                filename = os.path.basename(file_path)

                # Copy file to the local save_dir/group_name
                group_folder_path = os.path.join(self.engine.client.save_dir, self.group_name)
                os.makedirs(group_folder_path, exist_ok=True)
                destination_path = os.path.join(group_folder_path, filename)
                shutil.copy2(file_path, destination_path)

                # Add to listbox and path list
                self.file_listbox.insert(tk.END, f"📄 {filename}")
                self.file_paths.append(destination_path)

    def open_selected_file(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            file_path = self.file_paths[index]
            self.open_file(file_path)

    def open_file(self, path):
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:  # Linux or other
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print(f"Failed to open {path}: {e}")

    def remove_selected_file(self):
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            file_path = self.file_paths[index]

            # Remove from listbox and file_paths
            self.file_listbox.delete(index)
            del self.file_paths[index]

            # Remove the file locally
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed file: {file_path}")
            else:
                print(f"File {file_path} not found on disk.")

            # (Optional) notify server about file removal
            # self.engine.client.remove_file(self.group_name, file_path)
        else:
            print("No file selected.")

    def handle_events(self, event):
        pass

    def update(self):
        pass

    def back_clicked(self):
        self.destroy()
        self.engine.pop_state()

    def destroy(self):
        self.frame.destroy()
