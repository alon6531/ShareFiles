from State import State
import tkinter as tk


class SignUpState(State):
    def __init__(self, engine):
        super().__init__(engine)

        self.frame = tk.Frame(self.engine.root, bg="#1e1e1e")
        self.frame.place(relwidth=1, relheight=1)

        # Title
        title_label = tk.Label(self.frame, text="📑 Sign Up", font=("Helvetica", 28, "bold"),
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

        # Confirm Password Label and Entry (aligned horizontally)
        self.confirm_password_var = tk.StringVar()
        confirm_password_label = tk.Label(form_frame, text="Confirm Password", font=("Helvetica", 16), fg="white", bg="#1e1e1e")
        confirm_password_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        confirm_password_entry = tk.Entry(form_frame, textvariable=self.confirm_password_var, font=("Helvetica", 16), show="*")
        confirm_password_entry.grid(row=2, column=1, padx=10, pady=5, ipadx=20, ipady=8)

        # Submit Button
        submit_button = tk.Button(self.frame, text="Create Account", font=("Helvetica", 16),
                                  bg="#00B1E2", fg="white", command=self.submit_clicked)
        submit_button.pack(pady=20, ipadx=10, ipady=5)

        # Error message label
        self.error_label = tk.Label(self.frame, text="", font=("Helvetica", 14),
                                    bg="#1e1e1e", fg="red")
        self.error_label.pack(pady=5)

        # Back Button
        back_button = tk.Button(self.frame, text="Back", font=("Helvetica", 12),
                                bg="#B71C1C", fg="white", command=self.back_clicked)
        back_button.place(x=20, y=20, width=80, height=30)

    def submit_clicked(self):
        username = self.username_var.get()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()

        print(f"Username: {username}")
        print(f"Password: {password}")

        if password != confirm_password:
            print("Passwords do not match")
            self.error_label.config(text="Passwords do not match")
        else:
            # Call client's register function (simulate account creation)
            self.engine.client.register(username, password)
            print("Account created (dummy logic)")
            self.destroy()
            self.engine.pop_state()

    def back_clicked(self):
        self.destroy()
        self.engine.pop_state()

    def handle_events(self, event):
        pass  # Tkinter widgets handle events natively

    def update(self):
        pass

    def destroy(self):
        self.frame.destroy()
