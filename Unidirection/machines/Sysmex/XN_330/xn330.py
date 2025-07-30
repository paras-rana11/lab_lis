##############################################################################
# TCP
# ASTM Protocol
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
HOST = '192.168.1.224'  # or your specific IP address
PORT = 5150  # or your specific port
log_filename = 'received_data.log'
output_folder = 'C:\\ASTM\\root\\access2.data\\'

# Set up logging
logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def process_data(data):
    # Implement any specific data processing here
    return data.decode('utf-8')


def save_data_to_file(data):
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Generate filename with current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'xn_330_{timestamp}.txt')

    # Save the data to a text file
    with open(file_path, 'a') as file:
        file.write(data + '\n')
    logging.info(f"Data saved to {file_path}")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        logging.info(f"Server listening on {HOST}:{PORT}")
        print(f"Server listening on {HOST}:{PORT}")
        conn, addr = s.accept()
        with conn:
            logging.info(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if data:
                    print("Data Received") 
                if not data:
                    logging.info("No more data received.")
                    break

                processed_data = process_data(data)
                logging.debug(f"Received data: {processed_data}")

                # Save the processed data to a file
                save_data_to_file(processed_data)

if __name__ == '__main__':
    main()
