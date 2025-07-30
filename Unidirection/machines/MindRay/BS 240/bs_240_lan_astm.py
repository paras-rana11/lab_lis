import socket
import logging
import os
from datetime import datetime

# Configuration variables
HOST = '10.10.0.38'  # or your specific IP address
PORT = 7118  # or your specific port
output_folder = 'C:\\ASTM\\root\\report_files\\'


def process_data(data):
    # Attempt to decode, replacing invalid characters with a placeholder
    return data.decode('utf-8', errors='replace')


def save_data_to_file(data):
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Generate filename with current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'bs_240_{timestamp}.txt')

    # Save the data to a text file with UTF-8 encoding
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(data + '\n')
    print(f"Data saved to {file_path}")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        conn, addr = s.accept()
        with conn:
            while True:
                data = conn.recv(1024)
                if data:
                    print("Data Received") 
                    processed_data = process_data(data)
                    save_data_to_file(processed_data)
                if not data:
                    print("No more data received.")
                    pass


if __name__ == '__main__':
    main()
