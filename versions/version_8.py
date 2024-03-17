import socket
import threading
import time
import os
from ascon import ascon_encrypt, ascon_decrypt

def generate_random_bytes(length):
    """ Generate cryptographically strong random bytes. """
    return os.urandom(length)

# Server settings
host_server = '127.0.0.1'
port_server = 6666

# Shared data
data_from_smartwatch = None

running = True  # Flag to indicate if the threads should continue running
server = None  # Global variable to hold the server socket

# Generate key and nonce for AEAD
key = generate_random_bytes(16)
nonce = generate_random_bytes(16)

def main_server():
    global running, server, data_from_smartwatch

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host_server, port_server))
    server.listen()
    server.settimeout(1)  # Set a timeout for the accept call

    print("Main server listening...")

    while running:
        try:
            client, address = server.accept()
            if data_from_smartwatch:
                client.send(data_from_smartwatch)  # Send encrypted data to each connected client

            client.close()
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error occurred: {e}")

def stop_server():
    global running, server

    running = False
    time.sleep(1)  # Allow time for server loop to exit

    if server:
        server.close()
        print("Server stopped.")

def smartwatch_client():
    global data_from_smartwatch

    try:
        smartwatch_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        smartwatch_client_socket.connect((host_server, port_server))

        data_to_send = "Sensitive data from smartwatch."
        associated_data = b'smartwatch_data'
        encrypted_data = ascon_encrypt(key, nonce, associated_data, data_to_send.encode(), "Ascon-128")

        data_from_smartwatch = encrypted_data
        smartwatch_client_socket.send(encrypted_data)

        smartwatch_client_socket.close()
    except Exception as e:
        print(f"Error occurred in smartwatch client: {e}")

def smartphone_client():
    try:
        smartphone_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        smartphone_client_socket.connect((host_server, port_server))

        encrypted_data = smartphone_client_socket.recv(1024)
        if encrypted_data:
            associated_data = b'smartwatch_data'
            decrypted_data = ascon_decrypt(key, nonce, associated_data, encrypted_data, "Ascon-128")
            if decrypted_data is not None:
                print(f"Smartphone decrypted data: {decrypted_data.decode()}")

        smartphone_client_socket.close()
    except Exception as e:
        print(f"Error occurred in smartphone client: {e}")

def attacker_client():
    try:
        attacker_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attacker_client_socket.connect((host_server, port_server))

        encrypted_data = attacker_client_socket.recv(1024)
        if encrypted_data:
            # Attacker might try to decrypt, but we'll assume they don't have the correct key/nonce
            try:
                associated_data = b'smartwatch_data'
                decrypted_data = ascon_decrypt(key, nonce, associated_data, encrypted_data, "Ascon-128")
                print(f"Attacker decrypted data: {decrypted_data.decode()}")
            except:
                print("Attacker failed to decrypt the data.")

        attacker_client_socket.close()
    except Exception as e:
        print(f"Error occurred in attacker client: {e}")

# Initiating the server thread
main_server_thread = threading.Thread(target=main_server)
main_server_thread.start()

# Simulating smartwatch sending encrypted data
smartwatch_thread = threading.Thread(target=smartwatch_client)
smartwatch_thread.start()

# Simulating a smartphone client receiving and decrypting data
smartphone_thread = threading.Thread(target=smartphone_client)
smartphone_thread.start()

# Simulating an attacker client attempting to decrypt data
attacker_thread = threading.Thread(target=attacker_client)
attacker_thread.start()

# Stop the server after the operations
time.sleep(5)
stop_server()

