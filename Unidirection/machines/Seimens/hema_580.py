import socket
import os
from datetime import datetime

# Configuration for the Mindray BC-5130 machine
MACHINE_HOST = '10.10.10.121'
MACHINE_PORT = 7778
output_folder = 'C:\\ASTM\\root\\report_file\\'


def process_data(data):
    return data.decode('utf-8')


def save_data_to_file(data):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'hema_580_{timestamp}.txt')
    with open(file_path, 'a') as file:
        file.write(data + '\n')
    print(f"Data saved to {file_path}")


def my_read(port):
    try:
      return port.recv(1)
    except Exception as my_ex:
      print('Network disconnection??')
      return b''

def my_write(port, byte):
    return port.send(byte)


def get_filename():
    dt = datetime.now()
    return output_folder + "hema_580_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")


def communicate_with_machine():
    byte_array = []
    x = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((MACHINE_HOST, MACHINE_PORT))
            print(f"Connected to machine at {MACHINE_HOST}:{MACHINE_PORT}")
            while True:
                byte = my_read(s)
                if byte == b'':
                    print('<EOF> reached. Connection broken: details below')
                    conn_tuple = s.accept()
                    port = conn_tuple[0]
                else:
                    byte_array.append(chr(ord(byte)))

                if byte == b'\x05':
                    byte_array = []
                    byte_array.append(chr(ord(byte)))
                    my_write(s, b'\x06')
                    cur_file = get_filename()
                    x = open(cur_file, 'w')

                elif byte == b'\x0a':
                    my_write(s, b'\x06')
                    try:
                        x.write(''.join(byte_array))
                        byte_array = []
                    except Exception as my_ex:
                        print(my_ex)

                elif byte == b'\x04':
                    try:
                        if x is not None:
                            x.write(''.join(byte_array))
                            x.close()
                    except Exception as my_ex:
                        print(my_ex)
                    byte_array = []

    except Exception as e:
        print(f"Failed to communicate with machine at {MACHINE_HOST}:{MACHINE_PORT}: {e}")


if __name__ == '__main__':
    communicate_with_machine()
