##############################################################################
# TCP
# HL7 Protocol
############################### For Create .exe ###############################
# pyinstaller --onefile get_data_from_machine_celltak.py
# update path in spec file

############################### After update spec file ########################
# pyinstaller get_data_from_machine_celltak.spec

###############################################################################

import socket
import os
from datetime import datetime

# Configuration for the Mindray BC-5130 machine
MACHINE_HOST = '192.168.1.112'
MACHINE_PORT = 5100
output_folder = 'C:\\ASTM\\root\\access2.data\\'


def process_data(data):
    data = data.strip(b'\x0B\x1C\x0D')
    return data.decode('utf-8')


def save_data_to_file(data):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'bc_5130_{timestamp}.txt')
    with open(file_path, 'a') as file:
        file.write(data + '\n')
    print(f"Data saved to {file_path}")


# Function to parse HL7 message structure
def parse_hl7_message(message):
    segments = message.split('\r')
    hl7_data = {}

    for segment in segments:
        if segment:
            fields = segment.split('|')
            segment_type = fields[0]
            hl7_data[segment_type] = fields[1:]
    return hl7_data

def communicate_with_machine():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((MACHINE_HOST, MACHINE_PORT))
            print(f"Connected to machine at {MACHINE_HOST}:{MACHINE_PORT}")

            request_message = "Requesting patient data...\x1C\x0D"
            s.sendall(request_message.encode('utf-8'))

            # Receive and process data
            buffer = b""
            while True:
                data = s.recv(1024)
                if data:
                    buffer += data

                    if b'\x1C\x0D' in buffer:
                        messages = buffer.split(b'\x1C\x0D')
                        for message in messages[:-1]:
                            processed_data = process_data(message)
                            hl7_data = parse_hl7_message(processed_data)
                            save_data_to_file(processed_data)

                        buffer = messages[-1]
                else:
                    pass

    except Exception as e:
        print(f"Failed to communicate with machine at {MACHINE_HOST}:{MACHINE_PORT}: {e}")

if __name__ == '__main__':
    communicate_with_machine()

