import socket
import os
import threading
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import SqlDataBase
import json
import random
from JsonDataBase import JsonDataBase


class Server:
    def __init__(self, host='127.0.0.1', port=65432, udp_port=12345, save_dir = "Groups"):
        """
        Initialize the Server, generate keys, and start the server socket.
        """
        # Initialize the databases (SQL and JSON)
        self.sql_data_base = SqlDataBase.SqlDataBase()
        self.json_data_base = JsonDataBase()
        self.save_dir = save_dir
        # Set host and ports for the server
        self.host = host
        self.port = port
        self.udp_port = udp_port
        self.players = []

        # Generate RSA keys (private and public) for encryption/decryption
        self.private_key, self.public_key = self.make_keys()
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Print all users from the database (for debugging)
        self.sql_data_base.print_all_users()

        # Set up the server socket and start listening for incoming connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}...")


        # Start accepting incoming connections in a loop
        print("Server is running...")
        self.connected_users = {}
        self.listen_for_clients()


    def make_keys(self):
        """
        Generate a new RSA key pair (private and public).
        """
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        return private_key, public_key

    def decrypt(self, encrypted_text):
        """
        Decrypt the encrypted message using the private key.
        """
        return self.private_key.decrypt(
            encrypted_text,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def listen_for_clients(self):
        """
        Accept incoming client connections and handle them using separate threads.
        """
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection established with {client_address}\n")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()

    def handle_client(self, client_socket, client_address):
        """
        Handle communication with a connected client.
        """
        try:
            # Receive the public key of the client and send the server's public key
            public_client_key_pem = client_socket.recv(1024)
            public_client_key = load_pem_public_key(public_client_key_pem)
            client_socket.send(self.public_key_pem)

            while True:
                try:
                    message = self.decrypt(client_socket.recv(1024))
                except Exception as e:
                    print(e)
                    message = client_socket.recv(1024).decode()

                data = json.loads(message)  # Decode the JSON data


                action = data.get("action")
                print(f"Action received: {action}\n")

                if action == 'login':
                    self.handle_login(data, client_socket)

                elif action == 'register':
                    self.handle_register(data, client_socket)
                elif action == 'receiveFile':
                    self.receive_file(data, client_socket)
                elif action == 'sendAllFiles':
                    self.send_all_files(data["group_name"], client_socket)
                elif action == "removeFile":
                    group_name = data["group_name"]
                    filename = data["filename"]
                    file_path = os.path.join(self.save_dir, group_name, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"File {file_path} removed from server.")
                    else:
                        print(f"File {file_path} not found on server.")
                elif action == 'sendAllGroups':
                    self.send_groups(client_socket)
                elif action == 'addGroup':
                    self.json_data_base.add_group(data["group_name"], data["group_password"])
                elif action == "verifyGroupPassword":
                    self.verify_password(client_socket, data["group_name"],  data["password"])

                elif action == 'disconnect':
                    if data["username"] in self.connected_users:
                        del self.connected_users[data["username"]]  # Correct way to remove the user from the dictionary
                elif action == 'logout':
                    self.handle_logout(data, client_socket)

        except Exception as e:
            print(f"Error with client {client_address}: {e}\n")

        finally:
            client_socket.close()
            print(f"Closed connection with {client_address}\n")


    def handle_login(self,data, client_socket):
        """
        Handle user login by checking credentials.
        """
        username = data.get('username')
        print(username)
        password = data.get('password')

        # Ensure that both username and password are present
        if not username or not password:
            print("Error: Missing username or password.")
            client_socket.send(b'False')  # Send failure response
            return

        print(f"Login attempt for {username}\n")

        # Check the credentials in the database
        if self.sql_data_base.check_credentials(username, password):
            client_socket.send(b'True')  # Send success response
        else:
            client_socket.send(b'False')  # Send failure response



    def handle_register(self,data, client_socket):
        """
        Handle user registration and store new user in the database.
        """
        # Extract user data from the parsed JSON
        username = data.get('username')
        password = data.get('password')

        print(f"Registering user {username}\n")

        # Attempt to create the user in the database
        if self.sql_data_base.create_user(username, password):
            client_socket.send(b'Registration successful')
            self.sql_data_base.print_all_users()
        else:
            client_socket.send(b'Registration failed')

    def handle_logout(self, data, client_socket):
        """
        Handle client logout and remove the player from the players list.
        """
        try:
            # Receive the username of the player who is logging out


            # Remove the user from the connected_users dictionary
            if data["username"] in self.connected_users:
                del self.connected_users[data["username"]]  # Correct way to remove the user from the dictionary
                print(f"User {data["username"]} has been logged out and removed from the connected users list.")
            else:
                print(f"User {data["username"]} not found in the connected users list.")

            # Send response back to the client

        except Exception as e:
            print(f"Error during logout: {e}")

    def send_groups(self, client_socket):
        """Send all groups to the connected client."""
        groups = self.json_data_base.get_all_groups()
        # אם המידע הוא רשימה של שמות, הפוך את זה למילון עם מפתח "name"
        formatted_groups = [{"name": group} for group in groups]

        groups_data = json.dumps({"groups": formatted_groups})

        data_length = f"{len(groups_data):<10}"  # 10 תווים, מיושר שמאלה עם רווחים
        client_socket.sendall(data_length.encode())
        client_socket.sendall(groups_data.encode())

    def verify_password(self, client_socket, group_name, password):
        """Verify the group password."""
        print(f"Verifying password for group: {group_name}")
        if self.json_data_base.verify_password(group_name, password):
            client_socket.send(b"True")  # סיסמה נכונה
        else:
            client_socket.send(b"False")  # סיסמה שגויה


    def receive_file(self, data, client_socket):
        """
        Receive a file from the client and save it into a folder corresponding to the group name.
        """
        try:
            # Extract metadata from the data
            filename = data.get('filename')
            filesize = data.get('filesize')
            group_name = data.get('group_name')  # Get the group name from the data

            if not filename or not filesize or not group_name:
                raise ValueError("Missing filename, filesize, or group name in file transfer data.")

            # Ensure valid filename and filesize
            print(f"Receiving file: {filename} ({filesize} bytes) for group '{group_name}'")

            # Prepare path to save the file inside a group folder
            group_folder_path = os.path.join(self.save_dir, group_name)  # Create a group folder
            os.makedirs(group_folder_path, exist_ok=True)  # Make sure the group folder exists

            save_path = os.path.join(group_folder_path, filename)  # Save file inside the group folder

            # Open the file for writing received content
            with open(save_path, "wb") as f:
                bytes_received = 0
                while bytes_received < filesize:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        raise Exception("Connection lost during file transfer.")

                    f.write(chunk)
                    bytes_received += len(chunk)

                # Check if all bytes have been received
                if bytes_received != filesize:
                    raise Exception(
                        f"File transfer incomplete. Expected {filesize} bytes but received {bytes_received} bytes.")

            print(f"File '{filename}' received successfully and saved to {save_path}")

        except Exception as e:
            print(f"Error receiving file: {e}")
            # Clean up partial file if there's an error
            if os.path.exists(save_path):
                os.remove(save_path)

    def send_all_files(self, group_name, client_socket):
        """
        Send all files from a specific group folder to the client.
        """
        try:
            group_folder_path = os.path.join(self.save_dir, group_name)

            if not os.path.exists(group_folder_path):
                client_socket.send(b'0')  # No files available
                return

            files = [f for f in os.listdir(group_folder_path) if os.path.isfile(os.path.join(group_folder_path, f))]
            client_socket.send(str(len(files)).encode())  # Send number of files

            if not files:
                return

            for filename in files:
                file_path = os.path.join(group_folder_path, filename)
                filesize = os.path.getsize(file_path)

                metadata = {
                    "action": "sendFile",
                    "filename": filename,
                    "filesize": filesize,
                    "group_name": group_name
                }

                metadata_json = json.dumps(metadata).encode()

                # Send metadata length (4 bytes)
                client_socket.sendall(len(metadata_json).to_bytes(4, 'big'))
                # Send metadata content (as binary data)
                client_socket.sendall(metadata_json)

                # Send file content in chunks
                with open(file_path, "rb") as file:
                    while True:
                        chunk = file.read(4096)
                        if not chunk:
                            break
                        client_socket.sendall(chunk)

                print(f"File '{filename}' sent successfully.")

        except Exception as e:
            print(f"Error sending files: {e}")
            client_socket.send(b'0')


# Main entry point for the server
if __name__ == "__main__":
    server = Server()  # Initialize and start the server
