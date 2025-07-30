##############################################################################
# TCP
############################### For Create .exe ###############################
# pyinstaller --onefile get_data_from_machine_celltak.py
# update path in spec file
############################### After update spec file ########################
# pyinstaller get_data_from_machine_celltak.spec

###############################################################################

import socket
import logging
import os
from datetime import datetime

# Configuration variables
HOST = '192.168.1.6'
PORT = 5151
log_filename = 'received_data.log'
output_folder = 'C:\\ASTM\\root\\access2.data\\'

# # Set up logging
# logging.basicConfig(filename=log_filename, level=logging.DEBUG,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

def process_data(data):
    return data.decode('utf-8')

def save_data_to_file(data):
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'accre_{timestamp}.txt')

    # Save the data to a text file using UTF-8 encoding
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(data + '\n')

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        # logging.info(f"Server listening on {HOST}:{PORT}")
        print(f"Server listening on {HOST}:{PORT}")
        conn, addr = s.accept()
        with conn:
            # logging.info(f"Connected by {addr}")
            buffer = b""
            while True:
                data = conn.recv(1024)
                print(data)
                if not data:
                    print("No more data received.")
                    break
                buffer += data
                if b'\x1C\x0D' in buffer:
                    messages = buffer.split(b'\x1C\x0D')
                    for message in messages[:-1]:
                        processed_data = process_data(message)
                        # print(f"Received HL7 message: {processed_data}")
                        print("Data Received")
                        save_data_to_file(processed_data)

                    buffer = messages[-1]

if __name__ == '__main__':
    main()