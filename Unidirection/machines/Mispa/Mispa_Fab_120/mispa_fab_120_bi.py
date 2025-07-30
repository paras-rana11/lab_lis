# import socket
# import os
# from datetime import datetime
# import re
# import json
# import threading
# import logging
# import time
# import shutil

# CR = chr(0x0D)  # Carriage Return
# SB = chr(0x0B)
# EB = chr(0x1C)

# HOST = '192.168.52.101'
# PORT = 5152
# output_folder = 'C:\\ASTM\\root\\report_file\\'
# case_file_folder = "C:\\ASTM\\root\\case_file_real_time\\"
# backup_folder = "C:\\ASTM\\root\\case_file_real_time_backup\\"
# log_file = 'C:\\ASTM\\root\\log_files\\port_status_for_mispa_bi.log'
# log_retention_seconds = 172800  # 2 days
# log_check_interval = 86400  # 24 hours (in seconds)

# logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
# logging.info("Log file initialized.")

# os.makedirs(output_folder, exist_ok=True)

# def manage_log_file():
#     """Deletes the log file if it's older than 48 hours and creates a new one."""
#     while True:
#         try:
#             if os.path.exists(log_file):
#                 with open(log_file, "r") as file:
#                     lines = file.readlines()  

#                 current_time = time.time()
#                 updated_lines = []

#                 for line in lines:
#                     try:
#                         log_time_str = line.split(" - ")[0]  
#                         log_time_struct = time.strptime(log_time_str, "%Y-%m-%d %H:%M:%S,%f")
#                         log_timestamp = time.mktime(log_time_struct)  

#                         if current_time - log_timestamp < log_retention_seconds:
#                             updated_lines.append(line)
#                     except Exception as e:
#                         print(f"Skipping malformed line: {line} - Error: {e}")

#                 # Rewrite file with only recent logs
#                 with open(log_file, "w") as file:
#                     file.writelines(updated_lines)
#         except  Exception as e:
#             logging.info(f"Error When Removing Old Log")

#         finally:
#             time.sleep(log_check_interval) 

# def remove_old_file(folder_path):
#     while True:
#         for filename in os.listdir(folder_path):
#             file_path = os.path.join(folder_path, filename)

#             get_file_creation_time = os.path.getctime(file_path)

#             if get_file_creation_time > 259200:
#                 try:
#                     if file_path:
#                         os.remove(file_path)
#                 except Exception as e:
#                     print(f"Exception Occur :- {e}")
#         time.sleep(86400)



# def process_data(data):
#     data = data.strip(b'\x0B\x1C\x0D')
#     return data.decode('utf-8')

# def save_data_to_file(data):
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)
#     timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
#     file_path = os.path.join(output_folder, f'mispa_fab_120_{timestamp}.txt')
#     with open(file_path, 'a') as file:
#         file.write(data + '\n')
#     # print(f"Data saved to {file_path}")
#     logging.info(f"Data saved to {file_path}")

# def my_write(port, byte):
#     # print(f"Message Sent : {byte}")
#     logging.info(f"Message Sent : {byte}")
#     return port.send(byte)

# def send_message(sock, message):
#     my_write(sock, message.encode())

# def create_case_in_machine(sock, data):
#     barcode_id = data[2]
#     file_path = f"{case_file_folder}{barcode_id}.json"
#     if file_path:
#         with open(file_path, "r") as f:
#             json_data = json.load(f)

#         header_message = data[0]
#         qrd_message = data[1]
#         qrf_message = data[3]
#         barcode = json_data["case_id"]
#         sample_id = re.sub(r'[A-Za-z]', '', barcode)
#         sample_id = sample_id.split('-')[0]
#         test = json_data["test_id"]
#         sample_type = json_data["sample_type"]
#         patient_name = json_data["patient_name"]

#         order_message = f"""{SB}{header_message}{CR}
#                         MSA|AA|1|Message accepted|||0|{CR}
#                         ERR|0|{CR}
#                         QAK|SR|OK|{CR}
#                         {qrd_message}{CR}
#                         {qrf_message}{CR}
#                         DSP|1|||||{CR}
#                         DSP|2|||||{CR}
#                         DSP|3||{patient_name}|||{CR}
#                         DSP|4|||||{CR}
#                         DSP|5||O|||{CR}
#                         DSP|6|||||{CR}
#                         DSP|7|||||{CR}
#                         DSP|8|||||{CR}
#                         DSP|9|||||{CR}
#                         DSP|10|||||{CR}
#                         DSP|11|||||{CR}
#                         DSP|12|||||{CR}
#                         DSP|13|||||{CR}
#                         DSP|14|||||{CR}
#                         DSP|15|||||{CR}
#                         DSP|16|||||{CR}
#                         DSP|17|||||{CR}
#                         DSP|18|||||{CR}
#                         DSP|19|||||{CR}
#                         DSP|20|||||{CR}
#                         DSP|21||{barcode}|||{CR}
#                         DSP|22||{sample_id}|||{CR}
#                         DSP|23|||||{CR}
#                         DSP|24||N|||{CR}
#                         DSP|25|||||{CR}
#                         DSP|26||{sample_type}|||{CR}
#                         DSP|27|||||{CR}
#                         DSP|28|||||{CR}
#                         DSP|29||{test}|||{CR}
#                         DSC||{CR}
#                         {EB}{CR}"""
#         send_message(sock , order_message)
#         try:
#             shutil.copy2(file_path, backup_folder)
#             os.remove(file_path)
#         except Exception as e:
#             print(e)

# def communicate_with_machine():
#     global s
#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
#             s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Enable keep-alive
#             s.bind((HOST, PORT))
#             s.listen()
#             print(f"Server listening on {HOST}:{PORT}")
#             conn, addr = s.accept()
#             if conn:
#                 # print(f"Connected to {HOST}:{PORT}")
#                 logging.info(f"Connected to {HOST}:{PORT}")
#             buffer = b""
#             while True:
#                 if conn:
#                     data = conn.recv(1024)
#                     if data:
#                         buffer += data
#                         segment_list = []
#                         if b'\x1C\x0D' in buffer:
#                             messages = buffer.split(b'\x1C\x0D')
#                             for message in messages[:-1]:
#                                 processed_data = process_data(message)
                                
#                                 processed_data_list = processed_data.split('\r')
#                                 if processed_data_list[1].startswith('QRD'):
#                                     for message_data in processed_data_list:
#                                         if message_data.startswith('MSH'):
#                                             header_message = message_data.split('|')
#                                             header_message[8] = "DSR^Q03"
#                                             message_data_header = '|'.join(header_message)
#                                             segment_list.append(message_data_header)
#                                         elif message_data.startswith('QRD'):
#                                             message_data = message_data.split('|')
#                                             barcode_id = message_data[11]
#                                             message_data[8] = ""
#                                             message_data[9] = ""
#                                             message_data_qrd = '|'.join(message_data)
#                                             segment_list.append(message_data_qrd)
#                                             segment_list.append(barcode_id)
#                                         elif message_data.startswith('QRF'):
#                                             segment_list.append(message_data)
#                                     create_case_in_machine(conn , segment_list)
                                
#                                 else:
#                                     save_data_to_file(processed_data)

#                             buffer = messages[-1]
                            
#                     else:
#                         pass
#                 else:
#                     try:
#                         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                             s.bind((HOST, PORT))
#                             s.listen()
#                             print(f"Server listening on {HOST}:{PORT}")
#                             conn, addr = s.accept()
#                     except Exception as e:
#                         print(f"Exception Occur :- {e}")


#     except Exception as e:
#         print(f"Failed to communicate with machine at {HOST}:{PORT}: {e}")

# if __name__ == '__main__':
#     threading.Thread(target=manage_log_file, daemon=True).start()
#     threading.Thread(target=remove_old_file, args=(backup_folder), daemon=True).start()
#     communicate_with_machine()


import socket
import os
from datetime import datetime
import re
import json
import threading
import logging
import time
import shutil
import smtplib
from email.message import EmailMessage

CR = chr(0x0D)  # Carriage Return
SB = chr(0x0B)
EB = chr(0x1C)

HOST = '192.168.52.101'
PORT = 5152
output_folder = 'C:\\ASTM\\root\\report_file\\'
case_file_folder = "C:\\ASTM\\root\\case_file_real_time\\"
backup_folder = "C:\\ASTM\\root\\case_file_real_time_backup\\"

log_file = 'C:\\ASTM\\root\\log_files\\port_status_for_mispa_bi.log'
error_log_file = 'C:\\ASTM\\root\\log_files\\port_status_for_mispa_bi_error.log'

log_retention_seconds = 172800  # 2 days
log_check_interval = 86400  # 24 hours (in seconds)

subject = ""
to_email = ""
from_email = ""
password = "" 

os.makedirs(output_folder, exist_ok=True)
os.makedirs(backup_folder, exist_ok=True)

def setup_loggers():
    """Set up separate loggers for info and error."""
    logger = logging.getLogger("app_logger")
    logger.setLevel(logging.DEBUG)  # capture everything, filter in handlers
    logger.handlers.clear()  # avoid duplicate logs on reload

    # Info Handler
    info_handler = logging.FileHandler(log_file)
    info_handler.setLevel(logging.INFO)
    info_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    info_handler.setFormatter(info_format)

    # Error Handler
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    error_handler.setFormatter(error_format)

    logger.addHandler(info_handler)
    logger.addHandler(error_handler)

    return logger

log_file_list = [log_file,error_log_file]
logger = setup_loggers()
logger.info("Log file initialized.")
logger.error("This is an error log example.")

def manage_log_file(log_file_list):
    """Deletes the log file if it's older than 48 hours and creates a new one."""
    while True:
        try:
            for log_file in log_file_list:
                if os.path.exists(log_file):
                    with open(log_file, "r") as file:
                        lines = file.readlines()  

                    current_time = time.time()
                    updated_lines = []

                    for line in lines:
                        try:
                            log_time_str = line.split(" - ")[0]  
                            log_time_struct = time.strptime(log_time_str, "%Y-%m-%d %H:%M:%S,%f")
                            log_timestamp = time.mktime(log_time_struct)  

                            if current_time - log_timestamp < log_retention_seconds:
                                updated_lines.append(line)
                        except Exception as e:
                            print(f"Skipping malformed line: {line} - Error: {e}")
                            logger.error(f"Skipping malformed line: {line} - Error: {e}")
                            body_for_db = f' ********************** Skipping malformed line: ********************** \n {line} - Error: {e}'
                            send_email(subject, body_for_db, to_email, from_email, password)

                    # Rewrite file with only recent logs
                    with open(log_file, "w") as file:
                        file.writelines(updated_lines)
        except  Exception as e:
            logger.error(f"Error When Removing Old Log")

        finally:
            time.sleep(log_check_interval) 

def send_email(subject, body, to_email, from_email, password):
  try:
    # Create the email message
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    msg.set_content(body)

    # Connect to Gmail SMTP server
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
      smtp.ehlo()
      smtp.starttls()  # Secure the connection
      smtp.login(from_email, password)
      smtp.send_message(msg)

    logger.info("Email sent successfully!")

  except Exception as e:
    logger.error(f"Failed to send email: {e}")

def process_data(data):
    try:
        data = data.strip(b'\x0B\x1C\x0D')
        return data.decode('utf-8')
    except Exception as e:
        logger.error(f"Exception Occur in process data :- {e}")
        body_for_db = f' ********************** Exception Occur in process data :- ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)
        return None

def save_data_to_file(data):
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_path = os.path.join(output_folder, f'mispa_fab_120_{timestamp}.txt')
        with open(file_path, 'a') as file:
            file.write(data + '\n')
        # print(f"Data saved to {file_path}")
        logger.info(f"Data saved to {file_path}")
    except Exception as e:
        logger.error(f"Exception Occur in save data in txt file :- {e}")
        body_for_db = f' ********************** Exception Occur in save data in txt file :- ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

def my_write(port, byte):
    try:
        logger.info(f"Message Sent : {byte}")
        return port.send(byte)
    except Exception as e:
        logger.error(f"Exception Occur in write byte in port:- {e}")
        body_for_db = f' ********************** Exception Occur in write byte in port :- ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)
        return None

def send_message(sock, message):
    try:
        my_write(sock, message.encode())
    except Exception as e:
        logger.error(f"Exception Occur in send message:- {e}")
        body_for_db = f' ********************** Exception Occur in send message :- ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

def create_case_in_machine(sock, data):
    try:
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
            sample_id = sample_id.split('-')[0]
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
                shutil.copy2(file_path, backup_folder)
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Exception Occur while copy file in another folder:- {e}")
                body_for_db = f' ********************** Exception Occur while copy file in another folder :- ********************** \n {e}'
                send_email(subject, body_for_db, to_email, from_email, password)

    except Exception as e:
        logger.error(f"Exception Occur while create case:- {e}")
        body_for_db = f' ********************** Exception Occur while create case :- ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

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
                logger.info(f"Connected to {HOST}:{PORT}")
                body_for_db = f' ********************** Connected to {HOST}:{PORT} **********************'
                send_email(subject, body_for_db, to_email, from_email, password)
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
                            body_for_db = f' ********************** Connected to {HOST}:{PORT} **********************'
                            send_email(subject, body_for_db, to_email, from_email, password)
                    except Exception as e:
                        logger.error(f"Exception Occur :- {e}")
                        body_for_db = f' ********************** Exception Occur :- ********************** \n {e}'
                        send_email(subject, body_for_db, to_email, from_email, password)


    except Exception as e:
        logger.error(f"Failed to communicate with machine at {HOST}:{PORT}: {e}")
        body_for_db = f' ********************** Failed to communicate with machine at {HOST}:{PORT}: ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

if __name__ == '__main__':
    try:
        threading.Thread(target=manage_log_file, daemon=True).start()
        communicate_with_machine()
    except Exception as e:
        logger.error(f"Execption in main function: {e}")
        body_for_db = f' ********************** Execption in main function: ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

