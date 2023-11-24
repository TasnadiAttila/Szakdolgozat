import socket
import threading
import os
import secrets

host = '127.0.0.1'
port = 5555

server_running = True

# A dictionary to store secret keys for each device
secret_keys = {}

def register_device(device_id):
    # Generate a secret key for the device
    secret_key = secrets.token_hex(16)
    secret_keys[device_id] = secret_key
    return secret_key

def smart_watch():
    global server_running
    watch_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    watch_server.bind((host, port))
    watch_server.listen()

    print("Smart Watch Server listening...")

    while server_running:
        try:
            client, address = watch_server.accept()
            print(f"Connection from {address} has been established!")

            client_id = client.recv(1024).decode()
            if client_id in secret_keys:
                client.send("Authenticated".encode())

                # Here, the smartwatch only sends data and does not receive or process any data
                data_to_send = "Data from smartwatch."
                sent = client.send(data_to_send.encode())
                print(f"Smart watch sent {sent} bytes of data.")

            client.close()
        except socket.error:
            break

    watch_server.close()


def mobile_device():
    global server_running

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect((host, port))

    client.send("MobileDevice_ID".encode())

    response = client.recv(1024).decode()
    print(f"Server response to mobile device: {response}")

    if response == "Registered":
        print("Mobile device already registered.")
        client.close()
        return

    if response == "Authenticated":
        received_key = client.recv(1024).decode()
        print(f"Received key: {received_key}")

        # Check if the received key matches the registered key for the mobile device
        if received_key in secret_keys.values():
            if secret_keys["MobileDevice_ID"] == received_key:
                data_received = client.recv(1024).decode()
                print(f"Mobile device received data: {data_received}")
                # Process the received data as needed
            else:
                print("Unauthorized key used by mobile device. Closing connection.")
        else:
            print("Key not found in registered devices. Closing connection.")
            os._exit


def attacker():
    global server_running

    attacker_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    attacker_client.connect((host, port))

    # Attacker does not attempt to send any key, assuming no authentication
    attacker_client.send("Malicious_Attacker".encode())
    response = attacker_client.recv(1024).decode()
    print(f"Server response to attacker: {response}")

    # The attacker is aware of not being authenticated, no further actions are attempted

    print("The attacker attempted authentication. Closing connection.")
    attacker_client.close()
    os._exit(0)

     


# Registering the smartwatch device to get the secret key
register_device("SmartWatch_ID")

# Register the mobile device to get the secret key
register_device("MobileDevice_ID")

# Run smart_watch() as a separate thread acting as a server
watch_server_thread = threading.Thread(target=smart_watch)
watch_server_thread.start()

# Run mobile_device() and attacker() as clients
mobile_device_thread = threading.Thread(target=mobile_device)
attacker_thread = threading.Thread(target=attacker)

attacker_thread.start()
mobile_device_thread.start()

#TODO: The phone is authenticated but not its not registered
