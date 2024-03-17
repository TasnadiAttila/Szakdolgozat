import socket
import threading
import time
import os
from ascon import ascon_encrypt, ascon_decrypt

host = '127.0.0.1'
port = 12345

def generate_random_bytes(length):
    return os.urandom(length)

key = generate_random_bytes(16)
nonce = generate_random_bytes(16)

def server():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Server is running at {}:{}".format(host, port))

    smartWatchSocket, addr = server_socket.accept()
    print('Connection accepted for: ', addr)

    encrypted_data = smartWatchSocket.recv(1024)
    print('Received encrypted data from SmartWatch: ', encrypted_data)

    smartPhoneSocket, addr = server_socket.accept()
    print('Connection accepted for: ', addr)
    smartPhoneSocket.send(encrypted_data)

    server_socket.close()
    smartWatchSocket.close()
    smartPhoneSocket.close()

def smartWatch():
    watch_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    watch_socket.connect((host,port))
    message = 'This is the message'
    associated_data = b'sensitiveInformation'
    encrypted_data = ascon_encrypt(key,nonce,associated_data,message.encode(),"Ascon-128")
    watch_socket.send(encrypted_data)
    watch_socket.close()

def smartPhone():
    phone_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    phone_socket.connect((host,port))
    encrypted_data = phone_socket.recv(1024)
    associated_data = b'sensitiveInformation'
    decrypted_data = ascon_decrypt(key, nonce, associated_data, encrypted_data,"Ascon-128")
    print("Data received from server: ", decrypted_data.decode())
    phone_socket.close()

# Run the server and client in separate threads
server_thread = threading.Thread(target=server)
smartWatch_thread = threading.Thread(target=smartWatch)
smartPhone_thread = threading.Thread(target=smartPhone)

server_thread.start()
smartWatch_thread.start()
smartPhone_thread.start()

server_thread.join()
smartWatch_thread.join()
smartPhone_thread.join()
