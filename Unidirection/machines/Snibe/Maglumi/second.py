import socket
import logging
import os
from datetime import datetime

# Configuration variables
HOST = '192.168.0.21'  # or your specific IP address
PORT = 5150  # or your specific port
log_filename = 'received_data.log'
output_folder = 'C:\\ASTM\\root\\access2.data\\'

# Set up logging
logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def process_data(data):
    data = data.strip(b'\x0B\x1C\x0D')
    return data.decode('utf-8')

def save_data_to_file(data):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'hl7_{timestamp}.txt')

    # Save the data to a text file
    with open(file_path, 'a') as file:
        file.write(data + '\n')
    logging.info(f"Data saved to {file_path}")

def parse_hl7_message(message):
    segments = message.split('\r')
    hl7_data = {}

    for segment in segments:
        if segment:
            fields = segment.split('|')
            segment_type = fields[0]
            hl7_data[segment_type] = fields[1:]

    return hl7_data

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        logging.info(f"Server listening on {HOST}:{PORT}")
        print(f"Server listening on {HOST}:{PORT}")
        conn, addr = s.accept()
        with conn:
            logging.info(f"Connected by {addr}")
            buffer = b""
            while True:
                data = conn.recv(1024)
                if not data:
                    print("No more data received.")
                    break
                
                
                buffer += data

                if b'\x1C\x0D' in buffer:
                    messages = buffer.split(b'\x1C\x0D')
                    for message in messages[:-1]:
                        processed_data = process_data(message)
                        print(f"Received HL7 message: {processed_data}")

                        # hl7_data = parse_hl7_message(processed_data)
                        # logging.debug(f"Parsed HL7 data: {hl7_data}")

                        # save_data_to_file(processed_data)
                    
                    buffer = messages[-1]

if __name__ == '__main__':
    main()