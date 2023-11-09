import socket
import threading
import time

# Define the device classes
class Device:
    def __init__(self, name, port_number):
        self.name = name
        self.port_number = port_number
        self.position = (0, 0)
        self.connected_device = None
        self.data_collected = None

    def setPosition(self, x, y):
        self.position = (x, y)

    def connectTo(self, device, verify=False):
        if verify:
            self.connected_device = device
            device.connected_device = self
        else:
            self.connected_device = device

    def sendData(self, data):
        if self.connected_device:
            print(f"{self.name} is sending data: {data}")
            self.connected_device.receiveData(data)
        else:
            print(f"{self.name} is not connected to any device, cannot send data.")

    def receiveData(self, data):
        print(f"{self.name} received data: {data}")
        self.data_collected = data

# Create socket server for communication
def device_communication(device):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', device.port_number))
        s.listen(1)

        # Set a timeout of 1 second on the accept operation
        s.settimeout(1)

        try:
            conn, addr = s.accept()
        except socket.timeout:
            # No connection was accepted, so terminate the thread
            return

        with conn:
            print(f"Connected to {device.name} at {device.position}")
            data = conn.recv(1024)
            if data:
                print(f"{device.name} received data: {data.decode()}")
                device.receiveData(data.decode())


# Create device instances
smartWatch = Device("Smart Watch", 4214)
mobilePhone = Device("Mobile Phone", 4215)
attacker = Device("Attacker", 4216)

# Place the devices within range of each other
smartWatch.setPosition(0, 0)
mobilePhone.setPosition(10, 0)
attacker.setPosition(5, 0)

# Securely connect the mobile phone to the smartwatch (one-time verification)
smartWatch.connectTo(mobilePhone, verify=True)

# Set up threads for device communication
threading.Thread(target=device_communication, args=(smartWatch,)).start()
threading.Thread(target=device_communication, args=(mobilePhone,)).start()
threading.Thread(target=device_communication, args=(attacker,)).start()

# Simulate data collection from the smartwatch
data_to_send = [1, 2, 3]
smartWatch.sendData(data_to_send)

# Attacker receives data from the smartwatch
attacker.receiveData(data_to_send)
