import socket
import os
from datetime import datetime
import datetime

# Configuration variables
HOST = '10.10.0.38'  # or your specific IP address
PORT = 5001  # or your specific port
output_folder = 'C:\\ASTM\\root\\report_files\\'


def process_data(data):
    # Decode bytes using UTF-8, replacing invalid characters
    return data.decode('utf-8', errors='replace')

def get_filename():
  dt = datetime.datetime.now()
  return output_folder + "bc_700_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")


def my_read(port):
    try:
      return port.recv(1)
    except Exception as my_ex:
      print('Network disconnection??')
      return b''

def my_write(port, byte):
    return port.send(byte)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        conn, addr = s.accept()
        return conn

port = main()
byte_array = []
x = None

while True:
    byte = my_read(port)
    if byte == b'':
        print('<EOF> reached. Connection broken: details below')
        break

    if byte == b'\x05':  # Start of Transmission
        byte_array = [byte.decode('latin1')]
        my_write(port, b'\x06')  # Acknowledge
        cur_file = get_filename()
        x = open(cur_file, 'w', encoding='utf-8')

    elif byte == b'\x0a':  # Line Feed
        my_write(port, b'\x06')  # Acknowledge
        if x:
            x.write(''.join(byte_array))
            byte_array = []

    elif byte == b'\x04':  # End of Transmission
        if x:
            x.write(''.join(byte_array))
            x.close()
            x = None
        byte_array = []
        print(f"File Saved {cur_file}")

    else:
        byte_array.append(byte.decode('latin1'))