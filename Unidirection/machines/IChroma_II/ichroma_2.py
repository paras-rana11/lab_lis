import socket
import os
from datetime import datetime

# Configuration variables
HOST = '192.168.1.6'  # or your specific IP address
PORT = 5168  # or your specific port
output_folder = 'C:\\ASTM\\root\\access2.data\\'

def process_data(data):
    # Implement any specific data processing here
    return data.decode('utf-8')


def save_data_to_file(data):
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Generate filename with current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'ichroma_2_{timestamp}.txt')

    # Save the data to a text file
    with open(file_path, 'a') as file:
        file.write(data + '\n')
    print(f"Data saved to {file_path}")


def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if data:
                print("Data Received")
                processed_data = process_data(data)
                save_data_to_file(processed_data)
            else:
                print(f"Connection closed by {addr}")
                break
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            handle_client(conn, addr)


if __name__ == '__main__':
    main()
