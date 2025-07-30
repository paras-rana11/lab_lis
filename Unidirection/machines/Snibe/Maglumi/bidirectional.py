import socket
import logging
import os
from datetime import datetime

# Configuration variables
HOST = '192.168.1.224'  
PORT = 5150  
log_filename = 'received_data.log'
output_folder = 'C:\\HL7\\root\\access2.data\\'

# Request message to send to the client
REQUEST_MESSAGE = 'SEND_REPORT_ID_12345'  

# Logging configuration
logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def process_data(data):
    data = data.strip(b'\x0B\x1C\x0D')  # Strip specific HL7 delimiters
    return data.decode('utf-8')

def save_data_to_file(data):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'snibe_{timestamp}.txt')
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

def send_response(conn, message):
    """Send a response message back to the client."""
    if conn:
        conn.sendall(message.encode('utf-8'))
        logging.info(f"Sent response: {message}")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        logging.info(f"Server listening on {HOST}:{PORT}")
        print(f"Server listening on {HOST}:{PORT}")
        conn, addr = s.accept()
        with conn:
            logging.info(f"Connected by {addr}")
            
            # Step 1: Send request message to the client
            logging.info(f"Sending request: {REQUEST_MESSAGE}")
            conn.sendall(REQUEST_MESSAGE.encode('utf-8'))
            
            buffer = b""
            while True:
                data = conn.recv(1024)
                if not data:
                    logging.info("No more data received. Closing connection.")
                    break

                buffer += data
                if b'\x1C\x0D' in buffer:  # HL7 message terminator
                    messages = buffer.split(b'\x1C\x0D')
                    for message in messages[:-1]:
                        processed_data = process_data(message)
                        logging.debug(f"Received HL7 message: {processed_data}")
                        hl7_data = parse_hl7_message(processed_data)
                        logging.debug(f"Parsed HL7 data: {hl7_data}")
                        save_data_to_file(processed_data)

                        # Step 3: Send acknowledgment back to client
                        response_message = "ACK: Message received"
                        send_response(conn, response_message)

                    buffer = messages[-1]  # Keep any partial message

if __name__ == '__main__':
    main()
