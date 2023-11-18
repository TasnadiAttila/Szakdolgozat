import socket
import threading
import os

host = '127.0.0.1'
port = 5555

server_running = True

def mobile_device():
    global server_running
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((host, port))

    server.listen()

    print("Server listening...")

    while server_running:
        try:
            client, address = server.accept()
            print(f"Connection from {address} has been established!")

            client_id = client.recv(1024).decode()
            if client_id == "Valid_ID":
                client.send("Authenticated".encode())
                data = client.recv(1024).decode()
                print(f"Data received: {data}")
            else:
                client.send("Invalid ID".encode())

            client.close()
        except socket.error:
            break

    server.close()

def smart_watch():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect((host, port))

    client.send("Valid_ID".encode())

    response = client.recv(1024).decode()
    print(f"Server response: {response}")

    if response == "Authenticated":
        data_to_send = "Sensitive Patient information."
        client.send(data_to_send.encode())

    client.close()

def attacker():
    global server_running

    attacker_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    attacker_client.connect((host, port))

    attacker_client.send("Invalid_ID".encode())
    response = attacker_client.recv(1024).decode()
    print(f"Server response to attacker: {response}")

    if response == "Invalid ID":
        print("The attacker tried to interfere. Closing connection to prevent any further harm.")
        attacker_client.close()
        server_running = False  

        os._exit(0)  

server_thread = threading.Thread(target=mobile_device)
server_thread.start()

smart_watch()
attacker()
