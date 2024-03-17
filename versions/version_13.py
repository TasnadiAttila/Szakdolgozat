import socket
import threading
import time
import os
import hashlib

# Importálja az Ascon funkciókat a 'ascon.py'-ból
from ascon import ascon_hash, ascon_mac

def generate_symmetric_key(password):
    return hashlib.sha256(password.encode()).digest()[:16]

shared_secret = generate_symmetric_key("biztonsagos_jelszo")
shutdown_event = threading.Event()

def handle_client_connection(client_socket, addr):
    try:
        print(f"Kapcsolódott: {addr}")
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
    except Exception as e:
        print(f"Hiba a kliens kezelésekor: {e}")
    finally:
        client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(5)
    server_socket.settimeout(1)  # Időtúllépés beállítása
    print("Szerver várakozik a kapcsolatra...")

    while not shutdown_event.is_set():
        try:
            client_socket, addr = server_socket.accept()
        except socket.timeout:
            continue  # Folytatja, ha időtúllépés történik
        client_thread = threading.Thread(target=handle_client_connection, args=(client_socket, addr))
        client_thread.start()

    server_socket.close()
    print("Szerver leállt.")

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

def simulate_attacker():
    attacker_secret = generate_symmetric_key("tamado_jelszo")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))
    print("Támadó csatlakozva a szerverhez.")

    try:
        # Szerver hitelesítése
        data = client_socket.recv(1024)
        timestamp = data[:len(data)-16]
        server_mac = data[len(data)-16:]
        hash_challenge = ascon_hash(timestamp + b"kliens", "Ascon-Hash")
        attacker_mac = ascon_mac(attacker_secret, hash_challenge, "Ascon-Mac")

        client_socket.send(attacker_mac)
        if server_mac == attacker_mac:
            print("Támadó sikeresen hitelesítve.")
        else:
            print("Hitelesítés sikertelen a támadó részéről!")
    finally:
        client_socket.close()

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    # Kliensek indítása
    time.sleep(2)
    threading.Thread(target=start_client).start()
    threading.Thread(target=simulate_attacker).start()

    # Például 3 másodperc várakozás után
    time.sleep(3)
    shutdown_event.set()

    server_thread.join()
    print("A fő szál befejeződött.")