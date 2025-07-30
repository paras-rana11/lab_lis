# import socket
# import os
# from datetime import datetime

# # Configuration for the Mindray BC-5130 machine
# MACHINE_HOST = '192.168.52.200'
# MACHINE_PORT = 5100
# output_folder ='C:\\ASTM\\root\\report_file\\'


# def process_data(data):
#     data = data.strip(b'\x0B\x1C\x0D')
#     return data.decode('utf-8')


# def save_data_to_file(data):
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)
#     timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
#     file_path = os.path.join(output_folder, f'bc_5150_{timestamp}.txt')
#     with open(file_path, 'a') as file:
#         file.write(data + '\n')
#     print(f"Data saved to {file_path}")

# def communicate_with_machine():
#     global s
#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             s.connect((MACHINE_HOST, MACHINE_PORT))
#             print(f"Connected to machine at {MACHINE_HOST}:{MACHINE_PORT}")

#             # Receive and process data
#             buffer = b""
#             while True:
#                 if s:
#                     data = s.recv(1024)
#                     if data:
#                         buffer += data

#                         if b'\x1C\x0D' in buffer:
#                             messages = buffer.split(b'\x1C\x0D')
#                             for message in messages[:-1]:
#                                 processed_data = process_data(message)
#                                 save_data_to_file(processed_data)

#                             buffer = messages[-1]
#                     else:
#                         pass
#                 else:
#                     try:
#                         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                             s.connect((MACHINE_HOST, MACHINE_PORT))
#                             print(f"Connected to machine at {MACHINE_HOST}:{MACHINE_PORT}")
#                     except Exception as e:
#                         print(f"Exception Occur :- {e}")


#     except Exception as e:
#         print(f"Failed to communicate with machine at {MACHINE_HOST}:{MACHINE_PORT}: {e}")

# if __name__ == '__main__':
#     communicate_with_machine()


import socket
import os
import time
import threading
from datetime import datetime
import logging

# Configuration
MACHINE_HOST = '192.168.52.200'
MACHINE_PORT = 5100
output_folder = 'C:\\ASTM\\root\\report_file\\'
log_file = 'port_status_for_bc_5150.log'
disconnect_interval = 600  # 10 minutes
log_retention_hours = 48  # 2 days
log_check_interval = 86400  # 24 hours (in seconds)

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
    """Process received data by stripping control characters."""
    data = data.strip(b'\x0B\x1C\x0D')
    return data.decode('utf-8')

def save_data_to_file(data):
    """Save processed data to a timestamped file."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'bc_5150_{timestamp}.txt')
    
    with open(file_path, 'a') as file:
        file.write(data + '\n')
    
    print(f"Data saved to {file_path}")
    logging.info(f"Data saved to {file_path}")

def communicate_with_machine():
    """Connects to the machine, receives data, and disconnects every 10 minutes."""
    global s
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((MACHINE_HOST, MACHINE_PORT))
            print(f"Connected to machine at {MACHINE_HOST}:{MACHINE_PORT}")
            logging.info(f"Connected to machine at {MACHINE_HOST}:{MACHINE_PORT}")

            buffer = b""
            start_time = time.time()

            while time.time() - start_time < disconnect_interval:
                try:
                    data = s.recv(1024)
                    if data:
                        buffer += data
                        if b'\x1C\x0D' in buffer:                                             
                            messages = buffer.split(b'\x1C\x0D')
                            for message in messages[:-1]:
                                processed_data = process_data(message)
                                save_data_to_file(processed_data)
                            buffer = messages[-1]
                except socket.error as e:
                    print(f"Socket error: {e}")
                    logging.info(f"Socket error: {e}")
                    break  

    except Exception as e:
        print(f"Failed to communicate with machine: {e}")
        logging.info(f"Failed to communicate with machine: {e}")

    finally:
        print("Closing connection...")
        logging.info("Closing connection...")
        s.close()
    
    threading.Timer(5, communicate_with_machine).start()

# Start the processes
if __name__ == '__main__':
    threading.Thread(target=manage_log_file, daemon=True).start()

    communicate_with_machine()