import os
import socket
import threading
import time
import hashlib
import string
import random
from ascon import ascon_hash, ascon_mac, ascon_encrypt, ascon_decrypt

def generate_symmetric_key(user_input=False):
    if user_input:
        password = input("Adja meg a jelszót a kulcs generálásához: ")
    else:
        password = "automatikus_jelszo"
    return hashlib.sha256(password.encode()).digest()[:16]

def generate_random_bytes(length):
    return os.urandom(length)

def get_random_string(length):
    letters = string.ascii_lowercase + string.ascii_uppercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

class MyServer:
    def __init__(self):
        self.last_encrypted_message = b''
        self.shared_secret = generate_symmetric_key(user_input=True)
        self.key = generate_random_bytes(16)
        self.nonce = generate_random_bytes(16)

    def handle_client_connection(self, client_socket, addr):
        start_time = time.time()

        try:
            client_type = client_socket.recv(1024).decode()
            print(f"Kapcsolódott: {client_type} ({addr})")

            auth_start_time = time.time()
            timestamp = str(time.time()).encode()
            hash_challenge = ascon_hash(timestamp + b"kliens", "Ascon-Hash")
            mac = ascon_mac(self.shared_secret, hash_challenge, "Ascon-Mac")
            auth_end_time = time.time()

            client_socket.send(timestamp + mac)

            response = client_socket.recv(1024)
            if response != mac:
                print(f"Hitelesítés sikertelen a következő kliens részéről: {client_type} ({addr})")
                return

            print(f"Kliens sikeresen hitelesítve: {client_type} ({addr})")
            print(f"Hitelesítési idő: {auth_end_time - auth_start_time} másodperc")

            if client_type == "SmartWatch":
                encryption_start = time.time()
                self.last_encrypted_message = client_socket.recv(1024)
                print("Erkezett üzenet: ", self.last_encrypted_message)
                encryption_end = time.time()
                print(f"Titkosítási idő (SmartWatch): {encryption_end - encryption_start} másodperc")

            elif client_type == "SmartPhone":
                decryption_start = time.time()
                client_socket.send(self.last_encrypted_message)
                print("Kuldott üzenet: ", self.last_encrypted_message)
                decryption_end = time.time()
                print(f"Titkosítási idő (SmartPhone): {decryption_end - decryption_start} másodperc")

        except Exception as e:
            print(f"Hiba a kliens kezelésekor ({client_type}, {addr}): {e}")
        finally:
            client_socket.close()

        end_time = time.time()
        print(f"Kliens kezelésének összes ideje: {end_time - start_time} másodperc")

    def run_server(self, shutdown_event):
        local = 'localhost'
        port = 12345
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
            client_thread = threading.Thread(target=self.handle_client_connection, args=(client_socket, addr))
            client_thread.start()

        server_socket.close()
        print("Szerver leállt.")

def smartWatch(server):
    times = []
    for _ in range(6):
        start_time = time.time()
        smartWatch_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        smartWatch_socket.connect(('localhost', 12345))
        smartWatch_socket.send(b"SmartWatch")
        print("Csatlakozva a szerverhez.")

        try:
            data = smartWatch_socket.recv(1024)
            timestamp = data[:len(data)-16]
            server_mac = data[len(data)-16:]
            hash_challenge = ascon_hash(timestamp + b"kliens", "Ascon-Hash")
            smartWatchMac = ascon_mac(server.shared_secret, hash_challenge, "Ascon-Mac")

            smartWatch_socket.send(smartWatchMac)
            if server_mac == smartWatchMac:
                print("SmartWatch sikeresen hitelesítve.")
                message = get_random_string(15)
                associated_data = b'sensitiveInformation'
                encrypted_data = ascon_encrypt(server.key, server.nonce, associated_data, message.encode(), "Ascon-128")
                smartWatch_socket.send(encrypted_data)
            else:
                print("Hitelesítés sikertelen a SmartWatch részéről!")
        finally:
            smartWatch_socket.close()

        end_time = time.time()
        times.append(end_time - start_time)
        time.sleep(1)

    avg_time = sum(times) / len(times)
    print("SmartWatch átlagos futási ideje:", avg_time, "másodperc")

def smartPhone(server):
    times = []
    for _ in range(6):
        start_time = time.time()
        smartPhone_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        smartPhone_socket.connect(('localhost', 12345))
        smartPhone_socket.send(b"SmartPhone")
        print("Csatlakozva a szerverhez.")

        try:
            data = smartPhone_socket.recv(1024)
            timestamp = data[:len(data)-16]
            server_mac = data[len(data)-16:]
            hash_challenge = ascon_hash(timestamp + b"kliens", "Ascon-Hash")
            smartPhoneMac = ascon_mac(server.shared_secret, hash_challenge, "Ascon-Mac")

            smartPhone_socket.send(smartPhoneMac)
            if server_mac == smartPhoneMac:
                print("SmartPhone sikeresen hitelesítve.")
                encrypted_data = smartPhone_socket.recv(1024)
                associated_data = b'sensitiveInformation'
                decrypted_data = ascon_decrypt(server.key, server.nonce, associated_data, encrypted_data, "Ascon-128")
                print("Adat az SmartPhone-tól a szerveren keresztül: ", decrypted_data.decode())
            else:
                print("Hitelesítés sikertelen a SmartPhone részéről!")
        finally:
            smartPhone_socket.close()

        end_time = time.time()
        times.append(end_time - start_time)
        time.sleep(1)

    avg_time = sum(times) / len(times)
    print("SmartPhone átlagos futási ideje:", avg_time, "másodperc")

def attacker():
    times = []
    for _ in range(6):
        attacker_secret = generate_symmetric_key()
        start_time = time.time()
        attacker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attacker_socket.connect(('localhost', 12345))
        attacker_socket.send(b"Attacker")
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

        end_time = time.time()
        times.append(end_time - start_time)
        time.sleep(1)

    avg_time = sum(times) / len(times)
    print("Attacker átlagos futási ideje:", avg_time, "másodperc")

def main():
    server = MyServer()
    shutdown_event = threading.Event()
    server_thread = threading.Thread(target=server.run_server, args=(shutdown_event,))
    server_thread.start()

    time.sleep(10)
    threading.Thread(target=smartWatch, args=(server,)).start()

    time.sleep(10)
    threading.Thread(target=smartPhone, args=(server,)).start()

    time.sleep(10)
    threading.Thread(target=attacker).start()

    time.sleep(10)
    shutdown_event.set()

    server_thread.join()
    print("A fő szál befejeződött.")

if __name__ == "__main__":
    main()
