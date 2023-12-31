import socket
import threading
import time
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# Server settings
host_server = '127.0.0.1'
port_server = 6666

# Locks for thread synchronization
phone_lock = threading.Lock()
watch_lock = threading.Lock()

# Shared data
data_from_smartwatch = None

# AES-GCM Key
aes_key = get_random_bytes(16)  # 128-bit key

# AES-GCM Encrypt/Decrypt Functions
def aes_gcm_encrypt(key, plaintext):
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce, ciphertext, tag

def aes_gcm_decrypt(key, nonce, ciphertext, tag):
    cipher = AES.new(key, AES.MODE_GCM, nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext

# Main server function
def main_server():
    global running, server, data_from_smartwatch

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host_server, port_server))
    server.listen()
    server.settimeout(1)

    print("Main server listening...")

    running = True
    while running:
        try:
            client, address = server.accept()
            print(f"Connection from {address} has been established!")

            client_type = client.recv(1024).decode()

            # Authentication Challenge
            challenge = get_random_bytes(16)
            client.send(challenge)

            # Receive and verify the challenge response
            response = client.recv(1024)
            nonce, ciphertext, tag = response[:16], response[16:-16], response[-16:]
            try:
                decrypted_challenge = aes_gcm_decrypt(aes_key, nonce, ciphertext, tag)
                if decrypted_challenge != challenge:
                    raise ValueError("Authentication failed")
            except Exception as e:
                print(f"Authentication failed: {e}")
                client.send(b"Authentication failed")
                client.close()
                continue

            client.send(b"Authentication successful")

            if client_type == "smartwatch":
                with watch_lock:
                    encrypted_data = client.recv(1024)
                    nonce, ciphertext, tag = encrypted_data[:16], encrypted_data[16:-16], encrypted_data[-16:]
                    decrypted_data = aes_gcm_decrypt(aes_key, nonce, ciphertext, tag)
                    data_from_smartwatch = decrypted_data.decode('utf-8')
                    print(f"Data received from smartwatch: {data_from_smartwatch}")

            client.close()

        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error occurred: {e}")
            break

# Stop server function
def stop_server():
    global running, server

    running = False
    time.sleep(1)

    if server:
        server.close()
        print("Server stopped.")

# Smartwatch client function
def smartwatch_client():
    try:
        smartwatch_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        smartwatch_client_socket.connect((host_server, port_server))

        smartwatch_client_socket.send("smartwatch".encode())

        challenge = smartwatch_client_socket.recv(1024)
        nonce, ciphertext, tag = aes_gcm_encrypt(aes_key, challenge)
        smartwatch_client_socket.send(nonce + ciphertext + tag)

        auth_response = smartwatch_client_socket.recv(1024).decode()
        if auth_response == "Authentication successful":
            data_to_send = "Sensitive data from smartwatch."
            nonce, ciphertext, tag = aes_gcm_encrypt(aes_key, data_to_send.encode('utf-8'))
            smartwatch_client_socket.send(nonce + ciphertext + tag)
        else:
            print("Authentication failed.")

        smartwatch_client_socket.close()
    except Exception as e:
        print(f"Error occurred in smartwatch client: {e}")

# Phone client function
def phone_client():
    try:
        phone_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        phone_client_socket.connect((host_server, port_server))

        phone_client_socket.send("phone".encode())

        challenge = phone_client_socket.recv(1024)
        nonce, ciphertext, tag = aes_gcm_encrypt(aes_key, challenge)
        phone_client_socket.send(nonce + ciphertext + tag)

        auth_response = phone_client_socket.recv(1024).decode()
        if auth_response == "Authentication successful":
            encrypted_data = phone_client_socket.recv(1024)
            nonce, ciphertext, tag = encrypted_data[:16], encrypted_data[16:-16], encrypted_data[-16:]
            decrypted_data = aes_gcm_decrypt(aes_key, nonce, ciphertext, tag)
            print(f"Data received from server: {decrypted_data.decode('utf-8')}")
        else:
            print("Authentication failed.")

        phone_client_socket.close()
    except Exception as e:
        print(f"Error occurred in phone client: {e}")

# Attacker client function
def attacker_client():
    try:
        attacker_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attacker_client_socket.connect((host_server, port_server))

        attacker_client_socket.send("attacker".encode())

        challenge = attacker_client_socket.recv(1024)
        # Attacker attempts to authenticate (this should fail)
        nonce, ciphertext, tag = aes_gcm_encrypt(aes_key, challenge)
        attacker_client_socket.send(nonce + ciphertext + tag)

        auth_response = attacker_client_socket.recv(1024).decode()
        if auth_response == "Authentication successful":
            print("Attacker unexpectedly authenticated successfully.")
        else:
            print("Attacker authentication failed as expected.")

        attacker_client_socket.close()
    except Exception as e:
        print(f"Error occurred in attacker client: {e}")

# Start the server thread
main_server_thread = threading.Thread(target=main_server)
main_server_thread.start()

# Start the smartwatch, phone, and attacker client threads
smartwatch_client_thread = threading.Thread(target=smartwatch_client)
phone_client_thread = threading.Thread(target=phone_client)
attacker_client_thread = threading.Thread(target=attacker_client)

smartwatch_client_thread.start()
phone_client_thread.start()
attacker_client_thread.start()

# Allow the server to run for a while before stopping
time.sleep(10)
stop_server()
