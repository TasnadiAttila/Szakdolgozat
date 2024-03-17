import socket
import threading
import time
import os
from ascon import ascon_encrypt, ascon_decrypt

host = '127.0.0.1'
port = 12345

def server():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print("Server is running at {}:{}".format(host, port))

    smartWatchSocket, addr = server_socket.accept()
    print('Connection accepted for: ', addr)

    data = smartWatchSocket.recv(1024)
    print('Received from SmartWatch: ', data.decode())

    smartPhoneSocket, addr = server_socket.accept()
    print('Connection accepted for: ', addr)
    smartPhoneSocket.send(data)

    server_socket.close()
    smartWatchSocket.close()
    smartPhoneSocket.close()


def smartWatch():
    watch_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    watch_socket.connect((host,port))
    message = 'This is the message'
    watch_socket.send(message.encode())
    watch_socket.close()

def smartPhone():
    phone_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    phone_socket.connect((host,port))
    data = phone_socket.recv(1024)
    print("Data received from server: ", data.decode())
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
