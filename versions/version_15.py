import socket
import threading
import time
import hashlib

# Importálja az Ascon funkciókat a 'ascon.py'-ból
from ascon import ascon_hash, ascon_mac

def generate_symmetric_key(user_input=False):
    if user_input:
        password = input("Adja meg a jelszót a kulcs generálásához: ")
    else:
        password = "automatikus_jelszo"  # Az automatikus jelszó a támadónak
    return hashlib.sha256(password.encode()).digest()[:16]

# Előre megosztott titkos kulcs a szerver számára
shared_secret = generate_symmetric_key(user_input=True)

shutdown_event = threading.Event()

local = 'localhost'
port = 12345

def handle_client_connection(client_socket, addr):
    try:
        client_type = client_socket.recv(1024).decode()  # Kliens típusának olvasása
        print(f"Kapcsolódott: {client_type} ({addr})")

        timestamp = str(time.time()).encode()
        hash_challenge = ascon_hash(timestamp + b"kliens", "Ascon-Hash")
        mac = ascon_mac(shared_secret, hash_challenge, "Ascon-Mac")

        client_socket.send(timestamp + mac)

        response = client_socket.recv(1024)
        if response != mac:
            print(f"Hitelesítés sikertelen a következő kliens részéről: {client_type} ({addr})")
            return

        print(f"Kliens sikeresen hitelesítve: {client_type} ({addr})")
    except Exception as e:
        print(f"Hiba a kliens kezelésekor ({client_type}, {addr}): {e}")
    finally:
        client_socket.close()

def mainServer():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((local, port))
    server_socket.listen(5)
    server_socket.settimeout(1)
    print("Szerver várakozik a kapcsolatra...")

    while not shutdown_event.is_set():
        try:
            client_socket, addr = server_socket.accept()
        except socket.timeout:
            continue
        client_thread = threading.Thread(target=handle_client_connection, args=(client_socket, addr))
        client_thread.start()

    server_socket.close()
    print("Szerver leállt.")

def smartWatch():
    time.sleep(1)
    smartWatch_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    smartWatch_socket.connect((local, port))
    smartWatch_socket.send(b"SmartWatch")  # Kliens típusának elküldése
    print("Csatlakozva a szerverhez.")

    try:
        data = smartWatch_socket.recv(1024)
        timestamp = data[:len(data)-16]
        server_mac = data[len(data)-16:]
        hash_challenge = ascon_hash(timestamp + b"kliens", "Ascon-Hash")
        smartWatchMac = ascon_mac(shared_secret, hash_challenge, "Ascon-Mac")

        smartWatch_socket.send(smartWatchMac)
        if server_mac == smartWatchMac:
            print("SmartWatch sikeresen hitelesítve.")
        else:
            print("Hitelesítés sikertelen a SmartWatch részéről!")
    finally:
        smartWatch_socket.close()

def smartPhone():
    time.sleep(1)
    smartPhone_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    smartPhone_socket.connect((local, port))
    smartPhone_socket.send(b"SmartPhone")  # Kliens típusának elküldése
    print("Csatlakozva a szerverhez.")

    try:
        data = smartPhone_socket.recv(1024)
        timestamp = data[:len(data)-16]
        server_mac = data[len(data)-16:]
        hash_challenge = ascon_hash(timestamp + b"kliens", "Ascon-Hash")
        smartPhoneMac = ascon_mac(shared_secret, hash_challenge, "Ascon-Mac")

        smartPhone_socket.send(smartPhoneMac)
        if server_mac == smartPhoneMac:
            print("SmartPhone sikeresen hitelesítve.")
        else:
            print("Hitelesítés sikertelen a SmartPhone részéről!")
    finally:
        smartPhone_socket.close()

def attacker():
    attacker_secret = generate_symmetric_key()
    attacker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    attacker_socket.connect((local, port))
    attacker_socket.send(b"Attacker")  # Kliens típusának elküldése
    print("Támadó csatlakozva a szerverhez.")

    try:
        data = attacker_socket.recv(1024)
        timestamp = data[:len(data)-16]
        server_mac = data[len(data)-16:]
        hash_challenge = ascon_hash(timestamp + b"kliens", "Ascon-Hash")
        attacker_mac = ascon_mac(attacker_secret, hash_challenge, "Ascon-Mac")

        attacker_socket.send(attacker_mac)
        if server_mac == attacker_mac:
            print("Attacker sikeresen hitelesítve.")
        else:
            print("Hitelesítés sikertelen az Attacker részéről!")
    finally:
        attacker_socket.close()

if __name__ == "__main__":
    server_thread = threading.Thread(target=mainServer)
    server_thread.start()

    # Kliensek indítása
    time.sleep(2)
    threading.Thread(target=smartWatch).start()
    threading.Thread(target=smartPhone).start()
    threading.Thread(target=attacker).start()

    # Például 3 másodperc várakozás után
    time.sleep(3)
    shutdown_event.set()

    server_thread.join()
    print("A fő szál befejeződött.")
