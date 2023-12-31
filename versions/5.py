import socket
import threading
import time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# Server settings
host_server = '127.0.0.1'
port_server = 6666

# Locks for thread synchronization
phone_lock = threading.Lock()
watch_lock = threading.Lock()
attacker_lock = threading.Lock()

running = True  # Flag to indicate if the threads should continue running
server = None  # Global variable to hold the server socket

# Generating RSA keys for server, phone, smartwatch, and attacker
server_key = RSA.generate(2048)
server_public_key = server_key.publickey()
phone_key = RSA.generate(2048)
phone_public_key = phone_key.publickey()
watch_key = RSA.generate(2048)
watch_public_key = watch_key.publickey()
attacker_key = RSA.generate(2048)
attacker_public_key = attacker_key.publickey()

def main_server():
    global running, server

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host_server, port_server))
    server.listen()
    server.settimeout(1)  # Set a timeout for the accept call

    print("Main server listening...")

    while running:
        try:
            client, address = server.accept()
            print(f"Connection from {address} has been established!")

            client_key = client.recv(1024)

            if client_key == phone_public_key.export_key():
                with phone_lock:
                    # Server sends data to phone without expecting data in return
                    data_to_send = "Data from server to phone."
                    cipher = PKCS1_OAEP.new(phone_key)
                    encrypted_data = cipher.encrypt(data_to_send.encode())

                    client.send(encrypted_data)

            elif client_key == watch_public_key.export_key():
                with watch_lock:
                    client.send("Server_Authenticated".encode())
                    data_received = client.recv(1024)

                    # Decrypt received data with server's private key
                    cipher = PKCS1_OAEP.new(server_key)
                    decrypted_data = cipher.decrypt(data_received)
                    print(f"Data received from smartwatch: {decrypted_data.decode()}")

            elif client_key == attacker_public_key.export_key():
                with attacker_lock:
                    client.send("Authentication failed for attacker".encode())
                    print("The attacker connection was rejected by the server due to invalid authentication.")

            else:
                client.send("Invalid client ID".encode())

            client.close()
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error occurred: {e}")
            break

def stop_server():
    global running, server

    running = False
    time.sleep(1)  # Allow time for server loop to exit

    if server:
        server.close()
        print("Server stopped.")

def phone_client():
    try:
        phone_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        phone_client_socket.connect((host_server, port_server))

        # Send phone's public key without encryption
        phone_client_socket.send(phone_public_key.export_key())

        # Receive and decrypt data from the server
        encrypted_data = phone_client_socket.recv(1024)
        cipher = PKCS1_OAEP.new(phone_key)
        decrypted_data = cipher.decrypt(encrypted_data)

        print(f"Data received from server: {decrypted_data.decode()}")

        phone_client_socket.close()
    except Exception as e:
        print(f"Error occurred: {e}")

def smartwatch_client():
    try:
        smartwatch_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        smartwatch_client_socket.connect((host_server, port_server))

        # Send smartwatch's public key without encryption
        smartwatch_client_socket.send(watch_public_key.export_key())

        response = smartwatch_client_socket.recv(1024).decode()
        print(f"Main server response to SmartWatch: {response}")

        if response == "Server_Authenticated":
            data_to_send = "Sensitive data from smartwatch."
            cipher = PKCS1_OAEP.new(server_key)
            encrypted_data = cipher.encrypt(data_to_send.encode())

            smartwatch_client_socket.send(encrypted_data)

        smartwatch_client_socket.close()
    except Exception as e:
        print(f"Error occurred: {e}")

def attacker_client():
    try:
        attacker_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attacker_client_socket.connect((host_server, port_server))

        # Send attacker's public key without encryption
        attacker_client_socket.send(attacker_public_key.export_key())

        response = attacker_client_socket.recv(1024).decode()
        print(f"Main server response to Attacker: {response}")

        attacker_client_socket.close()
    except Exception as e:
        print(f"Error occurred in attacker client: {e}")

# Initiating the server thread
main_server_thread = threading.Thread(target=main_server)
main_server_thread.start()

# Initiating client threads
phone_client_thread = threading.Thread(target=phone_client)
smartwatch_client_thread = threading.Thread(target=smartwatch_client)
attacker_client_thread = threading.Thread(target=attacker_client)

phone_client_thread.start()
smartwatch_client_thread.start()
attacker_client_thread.start()

# Sleep for 5 seconds to simulate server operation
time.sleep(5)

# Stop the server after 5 seconds
stop_server()
