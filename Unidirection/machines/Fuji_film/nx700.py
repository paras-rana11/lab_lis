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
PORT = 5150
log_filename = 'received_data.log'
output_folder = 'C:\\ASTM\\root\\access2.data\\'

# Set up logging
logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def process_data(data):
    # Remove non-printable characters if necessary
    return ''.join(char for char in data.decode('utf-8') if char.isprintable())

def save_data_to_file(data):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'nx_700_{timestamp}.txt')

    with open(file_path, 'a') as file:
        file.write(data + '\n')
    logging.info(f"Data saved to {file_path}")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        logging.info(f"Server listening on {HOST}:{PORT}")
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                logging.info(f"Connected by {addr}")
                while True:
                    data = conn.recv(2048)
                    if data:
                        print(f"Received data")
                        processed_data = process_data(data)
                        save_data_to_file(processed_data)
                    else:
                        logging.info("No more data received.")
                        break

if __name__ == '__main__':
    main()




