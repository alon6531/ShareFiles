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
import logging

class Server:
    def __init__(self, host='127.0.0.1', port=65432, udp_port=12345, save_dir="Groups"):
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

        # Set up logging
        self.setup_logging()

        # Print all users from the database (for debugging)
        self.sql_data_base.print_all_users()

        # Set up the server socket and start listening for incoming connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.logger.info(f"Server listening on {self.host}:{self.port}...")

        # Start accepting incoming connections in a loop
        self.logger.info("Server is running...")
        self.connected_users = {}
        self.listen_for_clients()

    def setup_logging(self):
        """Setup a basic logging configuration."""
        self.logger = logging.getLogger('ServerLogger')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('server_logs.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

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
            self.logger.info(f"Connection established with {client_address}")
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
                    self.logger.error(f"Decryption error with client {client_address}: {e}")
                    message = client_socket.recv(1024).decode()

                data = json.loads(message)  # Decode the JSON data

                action = data.get("action")
                self.logger.info(f"Action received: {action}")

                if action == 'login':
                    self.handle_login(data, client_socket)

                elif action == 'register':
                    self.handle_register(data, client_socket)
                elif action == 'receiveFile':
                    self.receive_file(data, client_socket)
                elif action == 'sendAllFiles':
                    self.send_all_files(data["group_name"], client_socket)
                elif action == "removeFile":
                    self.remove_file(data["group_name"], data["filename"])
                elif action == 'sendAllGroups':
                    self.send_groups(client_socket)
                elif action == 'addGroup':
                    self.json_data_base.add_group(data["group_name"], data["group_password"])
                elif action == "verifyGroupPassword":
                    self.verify_password(client_socket, data["group_name"],  data["password"])

                elif action == 'disconnect':
                    self.handle_disconnect(data, client_socket)
                elif action == 'logout':
                    self.handle_logout(data, client_socket)

        except Exception as e:
            self.logger.error(f"Error with client {client_address}: {e}")

        finally:
            client_socket.close()
            self.logger.info(f"Closed connection with {client_address}")

    def handle_login(self, data, client_socket):
        """
        Handle user login by checking credentials.
        """
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            self.logger.warning("Error: Missing username or password.")
            client_socket.send(b'False')
            return

        self.logger.info(f"Login attempt for {username}")

        if self.sql_data_base.check_credentials(username, password):
            client_socket.send(b'True')
        else:
            client_socket.send(b'False')

    def handle_register(self, data, client_socket):
        """
        Handle user registration and store new user in the database.
        """
        username = data.get('username')
        password = data.get('password')

        self.logger.info(f"Registering user {username}")

        if self.sql_data_base.create_user(username, password):
            client_socket.send(b'Registration successful')
        else:
            client_socket.send(b'Registration failed')

    def handle_logout(self, data, client_socket):
        """
        Handle client logout and remove the player from the players list.
        """
        try:
            if data["username"] in self.connected_users:
                del self.connected_users[data["username"]]
                self.logger.info(f"User {data['username']} has been logged out.")
            else:
                self.logger.warning(f"User {data['username']} not found in the connected users list.")

        except Exception as e:
            self.logger.error(f"Error during logout: {e}")

    def handle_disconnect(self, data, client_socket):
        """
        Handle disconnection request.
        """
        username = data.get("username")
        if username in self.connected_users:
            del self.connected_users[username]
            self.logger.info(f"User {username} disconnected.")
        else:
            self.logger.warning(f"User {username} not found for disconnection.")

    def send_groups(self, client_socket):
        """Send all groups to the connected client."""
        groups = self.json_data_base.get_all_groups()
        formatted_groups = [{"name": group} for group in groups]
        groups_data = json.dumps({"groups": formatted_groups})

        data_length = f"{len(groups_data):<10}"
        client_socket.sendall(data_length.encode())
        client_socket.sendall(groups_data.encode())

    def verify_password(self, client_socket, group_name, password):
        """Verify the group password."""
        self.logger.info(f"Verifying password for group: {group_name}")
        if self.json_data_base.verify_password(group_name, password):
            client_socket.send(b"True")
        else:
            client_socket.send(b"False")

    def receive_file(self, data, client_socket):
        """
        Receive a file from the client and save it into a folder corresponding to the group name.
        """
        try:
            filename = data.get('filename')
            filesize = data.get('filesize')
            group_name = data.get('group_name')

            if not filename or not filesize or not group_name:
                raise ValueError("Missing filename, filesize, or group name.")

            self.logger.info(f"Receiving file: {filename} ({filesize} bytes) for group '{group_name}'")

            group_folder_path = os.path.join(self.save_dir, group_name)
            os.makedirs(group_folder_path, exist_ok=True)

            save_path = os.path.join(group_folder_path, filename)

            with open(save_path, "wb") as f:
                bytes_received = 0
                while bytes_received < filesize:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        raise Exception("Connection lost during file transfer.")
                    f.write(chunk)
                    bytes_received += len(chunk)

            self.logger.info(f"File '{filename}' received successfully and saved to {save_path}")

        except Exception as e:
            self.logger.error(f"Error receiving file: {e}")
            if os.path.exists(save_path):
                os.remove(save_path)

    def send_all_files(self, group_name, client_socket):
        """
        Send all files from a specific group folder to the client.
        """
        try:
            group_folder_path = os.path.join(self.save_dir, group_name)
            if not os.path.exists(group_folder_path):
                client_socket.send(b'0')
                return

            files = [f for f in os.listdir(group_folder_path) if os.path.isfile(os.path.join(group_folder_path, f))]
            client_socket.send(str(len(files)).encode())

            if files:
                for filename in files:
                    file_path = os.path.join(group_folder_path, filename)
                    filesize = os.path.getsize(file_path)

                    metadata = {"action": "sendFile", "filename": filename, "filesize": filesize, "group_name": group_name}
                    metadata_json = json.dumps(metadata).encode()

                    client_socket.sendall(len(metadata_json).to_bytes(4, 'big'))
                    client_socket.sendall(metadata_json)

                    with open(file_path, "rb") as file:
                        while chunk := file.read(4096):
                            client_socket.sendall(chunk)

                self.logger.info(f"All files for group '{group_name}' sent successfully.")

        except Exception as e:
            self.logger.error(f"Error sending files: {e}")
            client_socket.send(b'0')

# Main entry point for the server
if __name__ == "__main__":
    server = Server()
