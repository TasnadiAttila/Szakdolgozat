import os
import socket
import threading
import time

host_phone = '127.0.0.1'
port_phone = 5555

host_server = '127.0.0.1'
port_server = 6666

phone_lock = threading.Lock()
watch_lock = threading.Lock()
attacker_lock = threading.Lock()

running = True  # Flag to indicate if the threads should continue running

def diffie_hellman():
    # Publicly known prime and base values
    prime = 23
    base = 5

    # Private keys for client and server
    private_key_server = 6  # Replace with a secure random number
    private_key_client = 15  # Replace with a secure random number

    # Calculation of public keys to be exchanged
    public_key_server = (base ** private_key_server) % prime
    public_key_client = (base ** private_key_client) % prime

    # Shared secret key computation
    shared_key_server = (public_key_client ** private_key_server) % prime
    shared_key_client = (public_key_server ** private_key_client) % prime

    return shared_key_server, shared_key_client

def phone_client():
    global running
    shared_key_client, _ = diffie_hellman()  # Phone's shared key
    
    while running:
        with phone_lock:
            phone_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            phone_client_socket.connect((host_server, port_server))

            phone_client_socket.send(str(shared_key_client).encode())

            response = phone_client_socket.recv(1024).decode()
            print(f"Main server response to Phone: {response}")

            if response == "Server_Authenticated":
                data_received = phone_client_socket.recv(1024).decode()
                print(f"Data received from server: {data_received}")

            phone_client_socket.close()

def smartwatch_client():
    global running
    shared_key_client, _ = diffie_hellman()  # Smartwatch's shared key
    
    while running:
        with watch_lock:
            smartwatch_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            smartwatch_client_socket.connect((host_server, port_server))

            smartwatch_client_socket.send(str(shared_key_client).encode())

            response = smartwatch_client_socket.recv(1024).decode()
            print(f"Main server response to SmartWatch: {response}")

            if response == "Server_Authenticated":
                data_to_send = "Sensitive Patient."
                smartwatch_client_socket.send(data_to_send.encode())

            smartwatch_client_socket.close()

def main_server():
    global running
    shared_key_server, _ = diffie_hellman()  # Server's shared key
    
    while running:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host_server, port_server))
        server.listen()

        print("Main server listening...")

        while running:
            client, address = server.accept()
            print(f"Connection from {address} has been established!")

            client_key = client.recv(1024).decode()
            client_key = int(client_key) if client_key.isdigit() else None

            if client_key == shared_key_server:  # Authentication based on shared key
                client.send("Server_Authenticated".encode())
                data_to_send = "Sensitive Patient information."
                client.send(data_to_send.encode())
            else:
                client.send("Server_Invalid ID".encode())

            client.close()

        server.close()

def attacker():
    global running
    with attacker_lock:
        attacker_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attacker_client.connect((host_server, port_server))

        attacker_client.send("Attacker_ID".encode())
        response = attacker_client.recv(1024).decode()
        print(f"Main server response to attacker: {response}")

        if response == "Server_Invalid ID":
            print("The attacker tried to interfere. Closing connection to prevent any further harm.")
            attacker_client.close()

phone_client_thread = threading.Thread(target=phone_client)
phone_client_thread.start()

smartwatch_client_thread = threading.Thread(target=smartwatch_client)
smartwatch_client_thread.start()

main_server_thread = threading.Thread(target=main_server)
main_server_thread.start()

attacker()

# Wait for 10 seconds before setting the flag to stop the threads
time.sleep(1)
running = False
