import socket
import os
import json
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from  Engine import *
from ftplib import FTP


class Client:
    def __init__(self, server_host='127.0.0.1', tcp_port=65432):
        """
        Initialize the Client by generating keys, connecting to the server,
        and starting the application engine.
        """
        self.save_dir = "ClientFiles"
        self.server_host = server_host
        self.tcp_port = tcp_port
        self.running = False
        # Generate RSA keys
        self.private_key, self.public_key = self.make_keys()
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Create TCP socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((server_host, tcp_port))
            print(f"Connected to server at {server_host}:{tcp_port}")

            self.client_socket.send(self.public_key_pem)
            public_server_key_pem = self.client_socket.recv(1024)
            self.public_server_key = load_pem_public_key(public_server_key_pem)

            self.username = None

            app = Engine(self)
            app.run()
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.client_socket.close()
            raise

    def make_keys(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        return private_key, public_key

    def encrypt(self, text):
        return self.public_server_key.encrypt(
            text.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def log_in(self, login_username, login_password):
        try:
            # Create a dictionary to hold the login details
            login_data = {
                "action": "login",
                "username": login_username,
                "password": login_password
            }

            # Convert the dictionary to a JSON string
            json_data = json.dumps(login_data)

            # Send the JSON data (encrypted, if necessary)
            encrypted_data = self.encrypt(json_data)  # Assuming encrypt method exists
            self.client_socket.send(encrypted_data)

            # Receive the server's response
            response = self.client_socket.recv(1024).decode('utf-8')

            # Check if login was successful
            if response == 'True':
                print("Login successful!")
                self.username = login_username
                self.running = True
                return True
            else:
                print("Login failed!")
                return False

        except Exception as e:
            print(f"Error during login: {e}")
            return False
        except (socket.error, ConnectionResetError) as e:
            print(f"Server connection lost: {e}")
            return False

    def register(self, username, password):
        try:
            # Create a dictionary to represent the registration data
            registration_data = {
                "action": "register",
                "username": username,
                "password": password
            }

            # Convert the dictionary to a JSON string
            json_registration_data = json.dumps(registration_data)

            # Encrypt the JSON string (if encryption is necessary)
            encrypted_data = self.encrypt(json_registration_data)

            # Send the encrypted data to the serve
            self.client_socket.send(encrypted_data)  # Send encrypted registration data

            # Receive the server's response
            response = self.client_socket.recv(1024).decode('utf-8')
            print(response)  # Print the server's response

        except Exception as e:
            print(f"Error during registration: {e}")
        except (socket.error, ConnectionResetError) as e:
            print(f"Server connection lost: {e}")

    def get_user(self):
        return self.username

    def send_file(self, file_path, group_name):
        """
        Send a file to the server using FTP.
        """
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            return

        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)

        try:
            print(f"Sending file: {filename} ({filesize} bytes)")

            # Connect to the FTP server
            ftp = FTP(self.server_host)
            ftp.login()  # Assuming anonymous login or modify for user authentication

            # Change to the target directory (optional, based on your setup)
            # ftp.cwd('/target/directory')

            # Open the file and upload it using FTP
            with open(file_path, "rb") as file:
                ftp.storbinary(f"STOR {filename}", file)

            print(f"File {filename} sent successfully!")

            # Close FTP connection
            ftp.quit()

        except Exception as e:
            print(f"Error sending file via FTP: {e}")

    def log_out(self):
        receive_num_data = {
            "action": "logout",
            "username": self.username
        }

        log_out_json = json.dumps(receive_num_data)
        encrypted_data = self.encrypt(log_out_json)  # Assuming encrypt method exists
        self.client_socket.send(encrypted_data)

    def disconnect(self):
        disconnect = {
            "action": "disconnect",
            "username": self.username
        }

        log_out_json = json.dumps(disconnect)
        encrypted_data = self.encrypt(log_out_json)  # Assuming encrypt method exists
        self.client_socket.send(encrypted_data)

    def add_group(self, group_name,  group_password):
        add_group = {
            "action": "addGroup",
            "group_name": group_name,
            "group_password": group_password
        }
        add_group_json = json.dumps(add_group)
        encrypted_data = self.encrypt(add_group_json)
        self.client_socket.send(encrypted_data)

    def verify_group_password(self, group_name, password):
        try:
            # יצירת נתונים של בקשת אימות הסיסמה
            password_data = {
                "action": "verifyGroupPassword",
                "group_name": group_name,
                "password": password
            }

            # המרת הנתונים למבנה JSON
            password_json = json.dumps(password_data)

            # הצפנת הנתונים
            encrypted_data = self.encrypt(password_json)

            # שליחה לשרת
            self.client_socket.send(encrypted_data)

            # קבלת התשובה מהשרת (נכון או לא נכון)
            response = self.client_socket.recv(1024).decode('utf-8')

            # אם התשובה היא 'True', הסיסמה נכונה
            if response == 'True':
                print("Password verified successfully!")
                return True
            else:
                print("Incorrect password.")
                return False

        except Exception as e:
            print(f"Error verifying group password: {e}")
            return False

    def receive_groups(self):
        """Connect to the server and receive group data."""
        receive_groups_data = {
            "action": "sendAllGroups",
            "username": self.username
        }
        receive_groups_json = json.dumps(receive_groups_data)
        encrypted_data = self.encrypt(receive_groups_json)  # Assuming encrypt method exists
        self.client_socket.send(encrypted_data)

        try:
            # Receive the length of the incoming message
            data_length = self.client_socket.recv(10).decode().strip()  # Read the first 10 bytes to get the data length
            if not data_length.isdigit():
                raise ValueError("Received invalid data length")

            # Receive the actual data based on the length
            data = self.client_socket.recv(int(data_length)).decode()

            # Parse the JSON data
            groups = json.loads(data).get("groups", [])
            if not groups:
                print("No groups found.")
            return groups

        except Exception as e:
            print(f"Error receiving groups: {e}")
            return []

    def receive_all_files(self, group_name):
        """
        Receive all files for a specific group from the FTP server.
        """
        try:
            print(f"Requesting files for group: {group_name}")

            # Connect to the FTP server
            ftp = FTP(self.server_host)
            ftp.login()  # Assuming anonymous login or modify for user authentication

            # List files in the target directory (optional, modify based on your setup)
            files = ftp.nlst()  # List file names in the FTP server's current directory
            print(f"Found {len(files)} files on server.")

            if len(files) == 0:
                print("No files found.")
                ftp.quit()
                return

            for filename in files:
                print(f"Receiving file: {filename}")

                # Open the local file for writing
                with open(filename, "wb") as file:
                    ftp.retrbinary(f"RETR {filename}", file.write)

                print(f"File {filename} received successfully!")

            # Close FTP connection
            ftp.quit()

        except Exception as e:
            print(f"Error receiving files via FTP: {e}")

    def remove_file(self, group_name, file_path):
        """
        Remove a file from the local group folder and notify the server.
        """
        try:
            # Get filename only
            filename = os.path.basename(file_path)

            # Prepare the request to delete from server
            request_data = {
                "action": "removeFile",
                "group_name": group_name,
                "filename": filename
            }
            self.client_socket.send(self.encrypt(json.dumps(request_data)))

            # Remove the file locally
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File {file_path} removed locally.")
            else:
                print(f"File {file_path} not found locally.")

        except Exception as e:
            print(f"Error removing file: {e}")



# Main entry point
if __name__ == "__main__":
    try:
        client = Client()
    except Exception as e:
        print(f"Client failed to start: {e}")
