
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from threading import RLock, Thread
import uvicorn
import time
import json
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
MACHINE_NAME = 'Cobas C 311 1'
HOST_ADDRESS = '0.0.0.0'
HOST_PORT = 6010
HOST_COM_PORT = 'COM5'
MACHINE_ID = 'C_311_1'
REPORT_FILE_PREFIX = 'c_311_1_'
CONNECTION_TYPE = 'serial'

LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_c_311_1.log'
ERROR_LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_c_311_1_error.log'
LOG_FILE_LIST = [LOG_FILE, ERROR_LOG_FILE]

log_check_interval = 86400  # 24 hours (in seconds)

SUBJECT = "Email From SGL Hospital"
TO_EMAIL = "lishealthray@gmail.com"
FROM_EMAIL = "lishealthray@gmail.com"
PASSWORD = "rxbr zlzy tpin pgur" 

connection_c_311 = MachineConnectionSerial(
    connection_type=CONNECTION_TYPE,
    input_tty=HOST_COM_PORT, 
    machine_name=REPORT_FILE_PREFIX
)
# Try to establish connection
port_c_311, path = connection_c_311.get_port()

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
    
def send_mail_or_logging(error_message, error):
    logger.error(f'{error_message} : {error}')

    body = f"""
    Dear Team,

    This is an automated alert from the Laboratory Information System.

        --> {error_message} :: Below are the details of the incident:

        - Filename: cobas_c_311_1.py
        - Connetion Type: {CONNECTION_TYPE}
        - Machine Name: {MACHINE_NAME}
        - Machine Host Address: {HOST_ADDRESS}
        - Port: {HOST_PORT}
        - COM Port: {HOST_COM_PORT}
        - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        - Error Details: {error}

    Best regards,  
    Laboratory Information System  
    [Healthray LAB]
    """

    is_send_mail = send_email(SUBJECT, body, TO_EMAIL, FROM_EMAIL, PASSWORD)
    if not is_send_mail:
        logger.error(f"Exception during sending mail")

def setup_loggers(log_file, error_log_file):
    '''Set up separate loggers for info and error.'''
    logger = logging.getLogger('app_logger')
    try:
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
    except Exception as e:
        print(f"Error in initialize logger : {e}")
        return logger
    
logger = setup_loggers(LOG_FILE, ERROR_LOG_FILE)
logger.info('Log file initialized.')
logger.error('This is an error log example.')

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
        error_message = 'Error in remove old log'
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
        error_message = 'Error in send msg function'
        send_mail_or_logging(error_message, e)


def write_data_to_file(file, byte_array):
    """Write data to a file safely."""
    try:
        file.write(''.join(byte_array))
    except Exception as e:
        error_message = 'Error in write data in txt file'
        send_mail_or_logging(error_message, e)
        raise


def create_case_in_machine(connection, case_no, test_id, sample_type, sample_type_number):
    """Send commands to the machine to create a case."""
    with LOCK:
        try:
            logger.info(" ")
            logger.info("***  CASE CREATION PROCESS STARTED  ***")
            logger.info("*****************************************************")
            connection.write(generate_checksum.ENQ.encode())
            byte = connection.read()

            if byte == generate_checksum.ACK.encode():
                # Step 1: Send header message
                header_message = f"1H|\\^&|||host^1|||||C311|TSDWN^BATCH|P|1"
                send_message(connection, header_message)
                if connection.read() != generate_checksum.ACK.encode():
                    return {"status": "error", "message": "Header Message Not Acknowledged"}
                logger.info(f"HEADER MESSAGE :-       {header_message}")

                # Step 2: Send patient message
                patient_message = f"2P|1"
                send_message(connection, patient_message)
                if connection.read() != generate_checksum.ACK.encode():
                    return {"status": "error", "message": "Patient Message Not Acknowledged"}
                logger.info(f"PATIENT MESSAGE :-      {patient_message}")

                # Step 3: Send order message
                order_message = (
                    f"3O|1|{' ' * (22 - len(case_no))}{case_no}|^^^^{sample_type}^SC|{test_id}|R||||||A||||{sample_type_number}||||||||||O"
                )
                send_message(connection, order_message)
                if connection.read() != generate_checksum.ACK.encode():
                    return {"status": "error", "message": "Order Message Not Acknowledged"}
                logger.info(f"ORDER MESSAGE :-        {order_message}")

                # Step 4: Send comment message
                comment_message = (
                    f"4C|1|I|                              ^                         ^                    ^               ^          |G"
                )
                send_message(connection, comment_message)
                if connection.read() != generate_checksum.ACK.encode():
                    return {"status": "error", "message": "Comment Message Not Acknowledged"}
                logger.info(f"COMMENT MESSAGE :-      {comment_message}")

                # Step 5: Send termination message
                termination_message = f"5L|1|N"
                send_message(connection, termination_message)
                if connection.read() == generate_checksum.ACK.encode():
                    connection.write(generate_checksum.EOT.encode())
                    logger.info(f"TERMINATION MESSAGE :-  {termination_message}")
                    logger.info("*****************************************************")
                    logger.info(" ")
                    return {"status": "success", "message": "Case created successfully"}
                else:
                    return {"status": "error", "message": "Termination Message Not Acknowledged"}
            else:
                return {"status": "error", "message": "ENQ Message Not Acknowledged"}
        except Exception as e:
            error_message = 'Error in create case in machine'
            send_mail_or_logging(error_message, e)
            return {"status": "error", "message": str(e)}


def save_case_to_json(case_entry, machine_id, file_name):
    """Save case information to a JSON file, preserving data from the last 10 days and adding new entries."""
    file_path = os.path.join('C:\\ASTM\\root\\case_file\\', file_name)
    os.makedirs('C:\\ASTM\\root\\case_file\\', exist_ok=True)

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
        error_message = 'Error in save case in json'
        send_mail_or_logging(error_message, e)


def retry_api_call(connection, case_id, test_id, sample_type, machine_id):
    """Retry API call to ensure the case is created."""
    try:
        counter = 0
        if sample_type == "S1":
            sample_type_number = 1
        elif sample_type == "S2":
            sample_type_number = 2
        elif sample_type == "S3":
            sample_type_number = 3
        elif sample_type == "S4":
            sample_type_number = 4
        else:
            sample_type_number = 1
        while True:
            try:
                response = create_case_in_machine(connection, case_id, test_id, sample_type, sample_type_number)
                if response["status"] == "success":
                    case_entry = {"case_id": case_id, "test_id": test_id, "sample_type": sample_type, "sample_type_number": sample_type_number, "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    save_case_to_json(case_entry, machine_id, 'log_complate_case.json')
                    logger.info(f"COUNTER :- {counter}")
                    return response
            except Exception as e:
                print(f"Error in API call: {e}")
                case_entry = {"case_id": case_id, "test_id": test_id, "sample_type": sample_type, "sample_type_number": sample_type_number, "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "status":"Error"}
                save_case_to_json(case_entry, machine_id, 'log_error_case.json')
            counter+=1
            time.sleep(5)
    except Exception as e:
        error_message = 'Error in retry api call'
        send_mail_or_logging(error_message, e)

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
                                error_message = 'Error in creating new txt file'
                                send_mail_or_logging(error_message, e)

                        elif byte == b'\x0a':  # Data block finished
                            try:
                                connection.write(b'\x06')
                                write_data_to_file(file, byte_array)
                                byte_array = []
                            except Exception as e:
                                error_message = 'Error in wite data in txt file'
                                send_mail_or_logging(error_message, e)

                        elif byte == b'\x04':  # End of data transmission
                            try:
                                if file:  
                                    write_data_to_file(file, byte_array)
                                    logger.info(f'Data written to file : {file}')
                                    file.close()
                                byte_array = []
                            except Exception as e:
                                error_message = 'Error in closing file'
                                send_mail_or_logging(error_message, e)

                    except Exception as e:
                        error_message = 'Error in reading data'
                        send_mail_or_logging(error_message, e)

        logger.info("Stopped unidirectional reading.")
    except Exception as e:
        error_message = 'Error in continuous reading data'
        send_mail_or_logging(error_message, e)

def start_receiving_data(connection):
    """Start data receiving thread."""
    try:
        threading.Thread(target=remove_old_logs_from_log_file, args=(LOG_FILE_LIST,), daemon=True).start()
        time.sleep(2)
        receive_thread = Thread(target=continuous_receiving_data, args=(connection,))
        receive_thread.daemon = True
        receive_thread.start()
    except Exception as e:
        error_message = 'Error in receive data function'
        send_mail_or_logging(error_message, e)


# API routes
@app.post(f"/create_case/{HOST_COM_PORT}")
async def api_create_case(request: CreateCaseRequest, background_tasks: BackgroundTasks):
    """API endpoint to create a case."""
    try:
        background_tasks.add_task(
            retry_api_call,
            connection_c_311,
            request.case_id,
            request.test_id,
            request.sample_type,
            request.machine_id
        )
        return {"status": 200, "statusState": "success", "message": "Case Creation Started"}
    except Exception as e:
        error_message = 'Error in main api calling'
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
        start_receiving_data(connection_c_311)
        uvicorn.run(app, host=HOST_ADDRESS, port=HOST_PORT)
    except Exception as e:
        error_message = 'Error in main function'
        send_mail_or_logging(error_message, e)