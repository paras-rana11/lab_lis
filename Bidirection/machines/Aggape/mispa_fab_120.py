import socket
import os
from datetime import datetime
import re
import json
import threading
import logging
import time

HOST = '192.168.52.101'
PORT = 5152
output_folder = 'C:\\ASTM\\root\\report_file\\'
case_file_folder = "C:\\ASTM\\root\\case_file_real_time\\"
log_file = 'C:\\ASTM\\root\\log_files\\port_status_for_mispa_bi.log'
disconnect_interval = 600  # 10 minutes
log_retention_hours = 48  # 2 days
log_check_interval = 86400  # 24 hours (in seconds)

CR = chr(0x0D)  # Carriage Return
SB = chr(0x0B)
EB = chr(0x1C)

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

def manage_log_file():
    """Deletes the log file if it's older than 48 hours and creates a new one."""
    while True:
        if os.path.exists(log_file):
            file_age = time.time() - os.path.getmtime(log_file)  # File age in seconds
            if file_age > log_retention_hours * 3600:  # Convert hours to seconds
                os.remove(log_file)
                print(f"Deleted old log file: {log_file}")
                logging.info(f"Deleted old log file: {log_file}")

        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
        logging.info("Log file initialized.")

        time.sleep(log_check_interval)

def process_data(data):
    data = data.strip(b'\x0B\x1C\x0D')
    return data.decode('utf-8')

def save_data_to_file(data):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'mispa_fab_120_{timestamp}.txt')
    with open(file_path, 'a') as file:
        file.write(data + '\n')
    # print(f"Data saved to {file_path}")
    logging.info(f"Data saved to {file_path}")

def my_write(port, byte):
    # print(f"Message Sent : {byte}")
    logging.info(f"Message Sent : {byte}")
    return port.send(byte)

def send_message(sock, message):
    my_write(sock, message.encode())

def create_case_in_machine(sock, data):
    barcode_id = data[2]
    file_path = f"{case_file_folder}{barcode_id}.json"
    if file_path:
        with open(file_path, "r") as f:
            json_data = json.load(f)

        header_message = data[0]
        qrd_message = data[1]
        qrf_message = data[3]
        barcode = json_data["case_id"]
        sample_id = re.sub(r'[A-Za-z]', '', barcode)
        test = json_data["test_id"]
        sample_type = json_data["sample_type"]
        patient_name = json_data["patient_name"]

        order_message = f"""{SB}{header_message}{CR}
                        MSA|AA|1|Message accepted|||0|{CR}
                        ERR|0|{CR}
                        QAK|SR|OK|{CR}
                        {qrd_message}{CR}
                        {qrf_message}{CR}
                        DSP|1|||||{CR}
                        DSP|2|||||{CR}
                        DSP|3||{patient_name}|||{CR}
                        DSP|4|||||{CR}
                        DSP|5||O|||{CR}
                        DSP|6|||||{CR}
                        DSP|7|||||{CR}
                        DSP|8|||||{CR}
                        DSP|9|||||{CR}
                        DSP|10|||||{CR}
                        DSP|11|||||{CR}
                        DSP|12|||||{CR}
                        DSP|13|||||{CR}
                        DSP|14|||||{CR}
                        DSP|15|||||{CR}
                        DSP|16|||||{CR}
                        DSP|17|||||{CR}
                        DSP|18|||||{CR}
                        DSP|19|||||{CR}
                        DSP|20|||||{CR}
                        DSP|21||{barcode}|||{CR}
                        DSP|22||{sample_id}|||{CR}
                        DSP|23|||||{CR}
                        DSP|24||N|||{CR}
                        DSP|25|||||{CR}
                        DSP|26||{sample_type}|||{CR}
                        DSP|27|||||{CR}
                        DSP|28|||||{CR}
                        DSP|29||{test}|||{CR}
                        DSC||{CR}
                        {EB}{CR}"""
        send_message(sock , order_message)
        try:
            os.remove(file_path)
        except Exception as e:
            print(e)

def communicate_with_machine():
    global s
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Enable keep-alive
            s.bind((HOST, PORT))
            s.listen()
            print(f"Server listening on {HOST}:{PORT}")
            conn, addr = s.accept()
            if conn:
                # print(f"Connected to {HOST}:{PORT}")
                logging.info(f"Connected to {HOST}:{PORT}")
            buffer = b""
            while True:
                if conn:
                    data = conn.recv(1024)
                    if data:
                        buffer += data
                        segment_list = []
                        if b'\x1C\x0D' in buffer:
                            messages = buffer.split(b'\x1C\x0D')
                            for message in messages[:-1]:
                                processed_data = process_data(message)
                                
                                processed_data_list = processed_data.split('\r')
                                if processed_data_list[1].startswith('QRD'):
                                    for message_data in processed_data_list:
                                        if message_data.startswith('MSH'):
                                            header_message = message_data.split('|')
                                            header_message[8] = "DSR^Q03"
                                            message_data_header = '|'.join(header_message)
                                            segment_list.append(message_data_header)
                                        elif message_data.startswith('QRD'):
                                            message_data = message_data.split('|')
                                            barcode_id = message_data[11]
                                            message_data[8] = ""
                                            message_data[9] = ""
                                            message_data_qrd = '|'.join(message_data)
                                            segment_list.append(message_data_qrd)
                                            segment_list.append(barcode_id)
                                        elif message_data.startswith('QRF'):
                                            segment_list.append(message_data)
                                    create_case_in_machine(conn , segment_list)
                                
                                else:
                                    save_data_to_file(processed_data)

                            buffer = messages[-1]
                            
                    else:
                        pass
                else:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.bind((HOST, PORT))
                            s.listen()
                            print(f"Server listening on {HOST}:{PORT}")
                            conn, addr = s.accept()
                    except Exception as e:
                        print(f"Exception Occur :- {e}")


    except Exception as e:
        print(f"Failed to communicate with machine at {HOST}:{PORT}: {e}")

if __name__ == '__main__':
    threading.Thread(target=manage_log_file, daemon=True).start()
    communicate_with_machine()