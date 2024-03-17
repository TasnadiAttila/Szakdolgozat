import socket
import threading
import time
import os
import hashlib

# Importálja az Ascon funkciókat a 'ascon.py'-ból
from ascon import ascon_hash, ascon_mac

# Kezdeti jelszó alapú kulcsgenerálás
def generate_symmetric_key():
    password = input("Adja meg a jelszót a kulcs generálásához: ")
    return hashlib.sha256(password.encode()).digest()[:16]

# Előre megosztott titkos kulcs
shared_secret = generate_symmetric_key()

def handle_client_connection(client_socket):
    try:
        # Kliens hitelesítése
        timestamp = str(time.time()).encode()
        hash_challenge = ascon_hash(timestamp + b"kliens", "Ascon-Hash")
        mac = ascon_mac(shared_secret, hash_challenge, "Ascon-Mac")

        client_socket.send(timestamp + mac)

        response = client_socket.recv(1024)
        if response != mac:
            print("Hitelesítés sikertelen a kliens részéről!")
            return

        print("Kliens sikeresen hitelesítve.")
    finally:
        client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(1)
    print("Szerver várakozik a kapcsolatra...")

    client_socket, addr = server_socket.accept()
    print(f"Kapcsolódott: {addr}")
    handle_client_connection(client_socket)

def start_client():
    time.sleep(1)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))
    print("Csatlakozva a szerverhez.")

    try:
        # Szerver hitelesítése
        data = client_socket.recv(1024)
        timestamp = data[:len(data)-16]
        server_mac = data[len(data)-16:]
        hash_challenge = ascon_hash(timestamp + b"kliens", "Ascon-Hash")
        client_mac = ascon_mac(shared_secret, hash_challenge, "Ascon-Mac")

        client_socket.send(client_mac)
        if server_mac == client_mac:
            print("Szerver sikeresen hitelesítve.")
        else:
            print("Hitelesítés sikertelen a szerver részéről!")

    finally:
        client_socket.close()


# Szerver és kliens indítása
if __name__ == "__main__":
    # Szerver szál indítása
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    # Kliens indítása
    start_client()

    # Szerver szál befejezése
    server_thread.join()
