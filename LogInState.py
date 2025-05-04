from State import State
from SignUpState import SignUpState
from HomeState import HomeState
import tkinter as tk


class LogInState(State):
    def __init__(self, engine):
        super().__init__(engine)

        self.frame = tk.Frame(self.engine.root, bg="#1e1e1e")
        self.frame.place(relwidth=1, relheight=1)

        title_label = tk.Label(self.frame, text="📑 Log In", font=("Helvetica", 28, "bold"),
                               bg="#1e1e1e", fg="#00B1E2")
        title_label.pack(pady=30)

        # Create a frame for the form to align the inputs with labels
        form_frame = tk.Frame(self.frame, bg="#1e1e1e")
        form_frame.pack(pady=10)

        # Username Label and Entry (aligned horizontally)
        self.username_var = tk.StringVar()
        username_label = tk.Label(form_frame, text="Username", font=("Helvetica", 16), fg="white", bg="#1e1e1e")
        username_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        username_entry = tk.Entry(form_frame, textvariable=self.username_var, font=("Helvetica", 16))
        username_entry.grid(row=0, column=1, padx=10, pady=5, ipadx=20, ipady=8)

        # Password Label and Entry (aligned horizontally)
        self.password_var = tk.StringVar()
        password_label = tk.Label(form_frame, text="Password", font=("Helvetica", 16), fg="white", bg="#1e1e1e")
        password_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        password_entry = tk.Entry(form_frame, textvariable=self.password_var, font=("Helvetica", 16), show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=5, ipadx=20, ipady=8)

        # Submit Button
        submit_button = tk.Button(self.frame, text="Submit", font=("Helvetica", 16),
                                  bg="#00B1E2", fg="white", command=self.submit_clicked)
        submit_button.pack(pady=20, ipadx=10, ipady=5)

        # Error message label
        self.error_label = tk.Label(self.frame, text="", font=("Helvetica", 14),
                                    bg="#1e1e1e", fg="red")
        self.error_label.pack(pady=5)

        # Sign up button
        signup_button = tk.Button(self.frame, text="Don't have an account? Sign up",
                                  font=("Helvetica", 12), bg="#1e1e1e", fg="#64b5f6", borderwidth=0,
                                  command=self.signup_clicked)
        signup_button.pack(pady=10)

        # Back button
        back_button = tk.Button(self.frame, text="Back", font=("Helvetica", 12),
                                bg="#B71C1C", fg="white", command=self.back_clicked)
        back_button.place(x=20, y=20, width=80, height=30)

    def submit_clicked(self):
        username = self.username_var.get()
        password = self.password_var.get()

        print(f"Username: {username}")
        print(f"Password: {password}")

        if self.engine.client.log_in(username, password):
            self.error_label.config(text="")
            self.destroy()
            self.engine.push_state(HomeState(self.engine))
        else:
            print("Login failed")
            self.error_label.config(text="Invalid username or password")

    def back_clicked(self):
        self.destroy()
        self.engine.pop_state()

    def signup_clicked(self):
        self.destroy()
        self.engine.push_state(SignUpState(self.engine))

    def handle_events(self, event):
        pass  # No need for event binding here — Tkinter widgets handle that internally

    def update(self):
        pass  # No regular update needed here

    def destroy(self):
        self.frame.destroy()
