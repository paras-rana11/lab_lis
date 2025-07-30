from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from threading import RLock, Thread
import uvicorn
import time
import json
import re
import os
import logging
import threading
import smtplib
from email.message import EmailMessage

from healper import MachineConnectionSerial, GenerateChecksum

# Global objects and variables
generate_checksum = GenerateChecksum()
LOCK = RLock()
STOP_THREAD = False

# Machine Configuration
MACHINE_NAME = 'ACCESS 2'
HOST_ADDRESS = '0.0.0.0'
HOST_PORT = 6010
HOST_COM_PORT = 'COM1'
REPORT_FILE_PREFIX = 'access_2_'
CONNECTION_TYPE = 'Serial'

CASE_FILE = 'C:\\ASTM\\root\\case_file\\complate_case_for_access_2.json'
os.makedirs(CASE_FILE, exist_ok=True)

# log file path
LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_access_2.log'
ERROR_LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_access_2_error.log'
LOG_FILE_LIST = [LOG_FILE, ERROR_LOG_FILE]


# Email configuration
SUBJECT = 'Email From Universal Hospital'
TO_EMAIL = 'lishealthray@gmail.com'
FROM_EMAIL = 'lishealthray@gmail.com'
PASSWORD = 'rxbr zlzy tpin pgur' 

connection_access_2 = MachineConnectionSerial(
    connection_type=CONNECTION_TYPE,
    input_tty=HOST_COM_PORT, 
    machine_name=REPORT_FILE_PREFIX
)
# Try to establish connection
port_access_2, path = connection_access_2.get_port()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema for create_case
class CreateCaseRequest(BaseModel):
    case_id: str
    test_id: str
    sample_type: str
    machine_id: str
    patient_name: str
    gender: str

# Method for send email
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

        logger.info('Email sent successfully!')
        return True
    except Exception as e:
        logger.error(f'Failed to send email: {e}')
        return False

# Method for setup logging
def setup_loggers(log_file, error_log_file):
    '''Set up separate loggers for info and error.'''
    logger = logging.getLogger('app_logger')
    try:
        logger.setLevel(logging.DEBUG)  
        logger.handlers.clear()  

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
    except Exception as e:
        error_message = 'Exception in initialize logger'
        send_mail_or_logging(error_message, e)
        return logger

logger = setup_loggers(LOG_FILE, ERROR_LOG_FILE)
logger.info('Log file initialized.')
logger.error('This is an error log example.')

def send_mail_or_logging(error_message, error):
    logger.error(f'{error_message} : {error}')

    body = f"""
    Dear Team,

    This is an automated alert from the Laboratory Information System.

        --> {error_message} :: Below are the details of the incident:

        - Filename: access_2_by.py
        - Connetion Type: {CONNECTION_TYPE}
        - Machine Name: {MACHINE_NAME}
        - Port: {HOST_COM_PORT}
        - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        - Error Details: {error}

    Best regards,  
    Laboratory Information System  
    [Healthray LAB]
    """

    is_send_mail = send_email(SUBJECT, body, TO_EMAIL, FROM_EMAIL, PASSWORD)
    if not is_send_mail:
        logger.error(f"Exception during sending mail")

# Method for remove old logs
def remove_old_logs_from_log_file(log_file_list):
    try:
        logger.info("Thread Start For Remove old Logs")
        while True:
            for file in log_file_list:
                with open(file, 'r') as f:
                    data = f.read()

                lines = data.split('\n')

                cutoff_date = datetime.now() - timedelta(days=10)
                final_line_list = []
                for line in lines:
                    line_date = line.split()
                    if len(line_date) > 1:
                        if line_date[0] > (str(cutoff_date)).split()[0]:
                            final_line_list.append(line)

                with open(file,'w') as f:
                    f.write('\n'.join(final_line_list))
            
            time.sleep(86400)
    except Exception as e:
        error_message = 'Exception in remove old log'
        send_mail_or_logging(error_message, e)

# Helper functions
def send_message(connection, message):
    """Send a framed message with checksum to the machine."""
    try:
        framed_message = f"{generate_checksum.STX}{message}{generate_checksum.CR}{generate_checksum.ETX}"
        checksum = generate_checksum.get_checksum_value(framed_message)
        final_message = f"{framed_message}{checksum}{generate_checksum.CR}{generate_checksum.LF}"
        connection.write(final_message.encode())
    except Exception as e:
        error_message = 'Exception in send ASTM Message'
        send_mail_or_logging(error_message, e)

# Method for write data in txt file
def write_data_to_file(file, byte_array):
    """Write data to a file safely."""
    try:
        file.write(''.join(byte_array))
    except Exception as e:
        error_message = 'Exception in rewrite data to file'
        send_mail_or_logging(error_message, e)
        raise

# Method for unidirectional reading
def continuous_receiving_data(connection):
    """Continuously receive data from the machine."""
    global STOP_THREAD
    byte_array = []
    file = None  # Initialize file variable here
    try:
        logger.info("Started unidirectional reading...")
        while not STOP_THREAD:
            with LOCK:
                if connection:
                    try:
                        byte = connection.read()
                        if not byte:
                            continue

                        byte_array.append(chr(ord(byte)))

                        if byte == b'\x05':  # Start of new data
                            byte_array = [chr(ord(byte))]
                            connection.write(b'\x06')  # Send ACK
                            cur_file = connection.get_filename()
                            try:
                                if file:  # Close any open file before opening a new one
                                    file.close()
                                file = open(cur_file, 'w')  # Open a new file
                                write_data_to_file(file, byte_array)
                            except IOError as e:
                                error_message = 'Exception in open file'
                                send_mail_or_logging(error_message, e)

                        elif byte == b'\x0a':  # Data block finished
                            try:
                                connection.write(b'\x06')
                                write_data_to_file(file, byte_array)
                                byte_array = []
                            except Exception as e:
                                error_message = 'Exception in write file'
                                send_mail_or_logging(error_message, e)

                        elif byte == b'\x04':  # End of data transmission
                            try:
                                if file:  
                                    write_data_to_file(file, byte_array)
                                    logger.info(f'Data written to file, closing... {file}')
                                    file.close()
                                byte_array = []
                            except Exception as e:
                                error_message = 'Exception in close file'
                                send_mail_or_logging(error_message, e)

                    except Exception as e:
                        error_message = 'Exception in data receive'
                        send_mail_or_logging(error_message, e)

        logger.info("Stopped unidirectional reading.")
    except Exception as e:
        error_message = 'Exception in continuous receiving data'
        send_mail_or_logging(error_message, e)

# Method for create case in machine
def create_case_in_machine(connection, case_no, test_id, sample_type, patient_name):
    """Send commands to the machine to create a case."""
    with LOCK:
        try:
            dt = datetime.now()
            logger.info("\n***  CASE CREATION PROCESS STARTED  ***")
            logger.info("*****************************************************")
            connection.write(generate_checksum.ENQ.encode())
            byte = connection.read()

            if byte == generate_checksum.ACK.encode():
                # Step 1: Send header message
                header_message = f"1H|\\^&|||LIS|||||||P|1|20001010080000"
                send_message(connection, header_message)
                if connection.read() != generate_checksum.ACK.encode():
                    return {"status": "error", "message": "Header Message Not Acknowledged"}
                logger.info(f"HEADER MESSAGE :-       {header_message}")

                patient_message = f"2P|1|{patient_name}"
                send_message(connection, patient_message)
                if connection.read() != generate_checksum.ACK.encode():
                    return {"status": "error", "message": "Patient Message Not Acknowledged"}
                logger.info(f"PATIENT MESSAGE :-      {patient_message}")

                # Step 3: Send order message
                order_message = f"3O|1|{case_no}||{test_id}|R||||||A||||{sample_type}"
                send_message(connection, order_message)
                if connection.read() != generate_checksum.ACK.encode():
                    return {"status": "error", "message": "Order Message Not Acknowledged"}
                logger.info(f"ORDER MESSAGE :-        {order_message}")

                # Step 4: Send termination message
                termination_message = f"4L|1|N"
                send_message(connection, termination_message)
                if connection.read() == generate_checksum.ACK.encode():
                    connection.write(generate_checksum.EOT.encode())
                    logger.info(f"TERMINATION MESSAGE :-  {termination_message}")
                    logger.info("*****************************************************\n")
                    return {"status": "success", "message": "Case created successfully"}
                else:
                    return {"status": "error", "message": "Termination Message Not Acknowledged"}
            else:
                return {"status": "error", "message": "ENQ Message Not Acknowledged"}
        except Exception as e:
            error_message = 'Exception during case creation process'
            send_mail_or_logging(error_message, e)
            return {"status": "error", "message": str(e)}

# Method for save case in json file
def save_case_to_json(case_entry, machine_id, file_name):
    """Save case information to a JSON file, preserving data from the last 10 days and adding new entries."""
    file_path = os.path.join(CASE_FILE, file_name)

    try:
        # Open the file and load existing data
        if os.path.exists(file_path):
            with open(file_path, 'r') as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = [[]]
        else:
            existing_data = [[]]

        cutoff_date = datetime.now() - timedelta(days=10)

        for machine_group in existing_data:
            for machine in machine_group:
                if machine_id in machine:
                    machine[machine_id] = [
                        entry for entry in machine[machine_id]
                        if datetime.strptime(entry["timestamp"], '%Y-%m-%d %H:%M:%S') > cutoff_date
                    ]

        machine_found = False
        for machine_group in existing_data:
            for machine in machine_group:
                if machine_id in machine:
                    # Avoid duplicates
                    if not any(entry["case_id"] == case_entry["case_id"] for entry in machine[machine_id]):
                        machine[machine_id].append(case_entry)
                    machine_found = True
                    break
            if machine_found:
                break

        if not machine_found:
            existing_data[0].append({machine_id: [case_entry]})

        with open(file_path, 'w') as json_file:
            json.dump(existing_data, json_file, indent=4)

    except Exception as e:
        error_message = 'Error in save case in json file'
        send_mail_or_logging(error_message, e)

# Method for load new json file 
def load_json(file_path):
    try:
        # Open the file and load existing data
        if os.path.exists(file_path):
            with open(file_path, 'r') as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = [[]]
        else:
            with open(file_path, 'w') as json_file:
                json.dump([[]], json_file, indent=4)
            existing_data = [[]]
        return existing_data
    
    except Exception as e:
        existing_data = [[]]
        error_message = 'Exception During Loding JSON File'
        send_mail_or_logging(error_message, e)
        return existing_data

# Method for dump json data in file
def save_json(file_path, data):
    try:
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
    except Exception as e:
        error_message = 'Exception During Saving Data in JSON File'
        send_mail_or_logging(error_message, e)

def add_new_case_entry(case_data, case_file):
    try:
        case_file_data = load_json(case_file)
        if case_file_data != [[]]:
            case_file_data_list = case_file_data[0][0]["cases"]
            case_data["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            case_file_data_list.append(case_data)

            save_json(case_file, case_file_data)
        else:
            payload_case_list = []
            case_data["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            payload_case_list.append(case_data)
            case_file_data[0].append({'cases':payload_case_list})
            save_json(case_file, case_file_data)
    except Exception as e:
        error_message = 'Exception During Add New Case Entry in JSON File'
        send_mail_or_logging(error_message, e)

# Method for calling create case function
def retry_api_call(connection, case_id, test_id, sample_type, machine_id, patient_name):
    """Retry API call to ensure the case is created."""
    try:
        counter = 0
        if sample_type == "Serum":
            sample_type_number = 1
        elif sample_type == "Urin":
            sample_type_number = 2
        elif sample_type == "CSF":
            sample_type_number = 3
        elif sample_type == "other":
            sample_type_number = 4
        else:
            sample_type_number = 1
        while True:
            try:
                response = create_case_in_machine(connection, case_id, test_id, sample_type, patient_name)
                if response["status"] == "success":
                    case_entry = {"case_id": case_id, "test_id": test_id, "sample_type": sample_type, "sample_type_number": sample_type_number, "machine_id":machine_id, "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "status":"Complate"}
                    add_new_case_entry(case_entry, CASE_FILE)
                    logger.info(f"COUNTER :- {counter}")
                    return response
            except Exception as e:
                print(f"Error in API call: {e}")
                case_entry = {"case_id": case_id, "test_id": test_id, "sample_type": sample_type, "sample_type_number": sample_type_number, "machine_id":machine_id, "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "status":"Uncomplate"}
                add_new_case_entry(case_entry, CASE_FILE)
            counter+=1
            time.sleep(3)
    except Exception as e:
        error_message = 'Exception in retry api call'
        send_mail_or_logging(error_message, e)

def check_machine_connection(connection):
    global tcp_conn, path, STOP_THREAD
    try:
        while True:
            with LOCK:

                STOP_THREAD = True
                time.sleep(3)

                connection.write(generate_checksum.ENQ.encode())

                byte = connection.read()
                if byte == generate_checksum.ACK.encode():
                    connection.write(generate_checksum.EOT.encode())
                    print("!! Machine Still Connected !!")
                else:
                    connection.close_connection()
                    STOP_THREAD = False
                    tcp_conn, path = connection_access_2.get_connection()

                time.sleep(1800)
                continue

            time.sleep(5)
    except Exception as e:
        try:
            connection.close_connection()
            STOP_THREAD = False
            tcp_conn, path = connection_access_2.get_connection()
        except Exception as reconnection_error:
            logger.error(f"Exception during reconnection :- {reconnection_error}")
        error_message = 'Exception during checking connection'
        send_mail_or_logging(error_message, e)

# Method for call unidirectional reading method
def start_receiving_data(connection):
    """Start data receiving thread."""
    try:
        threading.Thread(target=remove_old_logs_from_log_file, args=(LOG_FILE_LIST,), daemon=True).start()
        time.sleep(2)
        receive_thread = Thread(target=continuous_receiving_data, args=(connection,))
        receive_thread.daemon = True
        receive_thread.start()
    except Exception as e:
        error_message = 'Exception in receiving data'
        send_mail_or_logging(error_message, e)

# API routes
@app.post(f"/create_case/{HOST_COM_PORT}")
async def api_create_case(request: CreateCaseRequest, background_tasks: BackgroundTasks):
    """API endpoint to create a case."""
    try:
        background_tasks.add_task(
            retry_api_call,
            connection_access_2,
            request.case_id,
            request.test_id,
            request.sample_type,
            request.machine_id,
            request.patient_name
        )
        return {"status": 200, "statusState": "success", "message": "Case Creation Started"}
    except Exception as e:
        error_message = 'Exception in api call'
        send_mail_or_logging(error_message, e)
        raise HTTPException(
            status_code=400,
            detail={
                "status": 400,
                "statusState": "error",
                "message": f"Case Creation Error: {e}"
            }
        )

# Main
if __name__ == "__main__":
    try:
        start_receiving_data(connection_access_2)
        uvicorn.run(app, host=HOST_ADDRESS, port=HOST_PORT)
    except Exception as e:
        error_message = 'Exception in main function'
        send_mail_or_logging(error_message, e)