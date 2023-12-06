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
            try:
                phone_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                phone_client_socket.connect((host_server, port_server))

                phone_client_socket.send(str(shared_key_client).encode())

                response = phone_client_socket.recv(1024).decode()
                print(f"Main server response to Phone: {response}")

                if response == "Server_Authenticated":
                    data_received = phone_client_socket.recv(1024).decode()
                    print(f"Data received from server: {data_received}")

                phone_client_socket.close()
            except ConnectionResetError as e:
                print(f"ConnectionResetError occurred: {e}")
                continue  # Continue with the loop even after encountering the exception




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
                data_to_send = "Sensitive Patient XD."
                smartwatch_client_socket.send(data_to_send.encode())


def attacker():
    global running
    _, attacker_shared_key = diffie_hellman()  # Attacker's shared key

    with attacker_lock:
        attacker_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attacker_client.connect((host_server, port_server))

        attacker_client.send(str(attacker_shared_key).encode())
        response = attacker_client.recv(1024).decode()
        print(f"Main server response to attacker: {response}")

        if "Server_Invalid ID" in response:
            print("The attacker tried to interfere. Closing connection to prevent any further harm.")
        else:
            print("The attacker connection was not identified by the server as invalid.")

def main_server():
    global running
    shared_key_server, attacker_shared_key = diffie_hellman()  # Server's shared key and attacker's shared key

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
            elif client_key == attacker_shared_key:  # Check for attacker's key
                print(f"Detected attacker from {address}. Closing the connection.")
                client.send("Authentication failed for attacker".encode())  # Log authentication failure
                print("Authentication failed for attacker")
                client.close()  # Close the connection immediately
            else:
                client.send("Server_Invalid ID".encode())

stop_phone = threading.Event()
stop_watch = threading.Event()
stop_server = threading.Event()
stop_attacker = threading.Event()

phone_client_thread = threading.Thread(target=phone_client)
smartwatch_client_thread = threading.Thread(target=smartwatch_client)
main_server_thread = threading.Thread(target=main_server)
attacker_client_thread = threading.Thread(target=attacker)

phone_client_thread.start()
smartwatch_client_thread.start()
main_server_thread.start()

attacker_client_thread.start()

time.sleep(2)  # Wait before stopping the threads
running = False

stop_phone.set()
stop_watch.set()
stop_server.set()
stop_attacker.set()

# Join the threads to wait for them to complete
phone_client_thread.join()
smartwatch_client_thread.join()
main_server_thread.join()
attacker_client_thread.join()
