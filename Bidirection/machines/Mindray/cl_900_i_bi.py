import os
import re
import time
import json
import socket
import threading
import uvicorn
import smtplib 
import logging
import asyncio
from datetime import datetime, timedelta
from pydantic import BaseModel
from email.message import EmailMessage
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, BackgroundTasks

from Sanghvi_Hospital.Bidirectional.healper import GenerateChecksum, MachineConnectionTcp

app = FastAPI()

# Initialize connection and other objects
generate_checksum = GenerateChecksum()

STOP_THREAD = False
CASE_CREATION_FALG = False
MONITORING_ACTIVE = True  # Flag to control monitoring loop
CONNECTION_CL_900_I = None

CONNECTION_TYPE = "TCP/IP"
HOST_ADDRESS = "192.168.1.38"
HOST_PORT = 6010
HOST_CONNECTION_PORT = 7118
REPORT_FILE_PREFIX = 'cl_900_i_'

# log file path
CASE_FILE = 'C:\\ASTM\\root\\case_file\\complate_case_for_cl_900_i.json'

LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_cl_900_i_info.log'
ERROR_LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_cl_900_i_error.log'
LOG_FILE_LIST = [LOG_FILE, ERROR_LOG_FILE]

# Email configuration
SUBJECT = 'Email From Sanghvi Hospital'
TO_EMAIL = 'lishealthray@gmail.com'
FROM_EMAIL = 'lishealthray@gmail.com'
PASSWORD = 'rxbr zlzy tpin pgur'

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
        info_format = logging.Formatter('%(asctime)s - INFO - %(message)s')
        info_handler.setFormatter(info_format)

        # Error Handler
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_format = logging.Formatter('%(asctime)s - ERROR - %(message)s')
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

        - Filename: cl_900_i_by.py
        - Connetion Type: {CONNECTION_TYPE}
        - Machine Name: {HOST_ADDRESS}
        - Port: {HOST_PORT}
        - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        - Error Details: {error}

    Best regards,  
    Laboratory Information System  
    [Healthray LAB]
    """

    is_send_mail = send_email(SUBJECT, body, TO_EMAIL, FROM_EMAIL, PASSWORD)
    if not is_send_mail:
        logger.error(f"Exception during sending mail")

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
        error_message = 'Exception in send ASTM Message'
        send_mail_or_logging(error_message, e)

def write_data_to_file(file, byte_array):
    """Write data to a file safely."""
    try:
        file.write(''.join(byte_array))
    except Exception as e:
        error_message = 'Exception in rewrite data to file'
        send_mail_or_logging(error_message, e)
        raise

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

# Method for remove old case entry
def remove_old_case_entry(payload_file):
    try:
        while True:
            payload_file_data = load_json(payload_file)
            if payload_file_data != [[]]:
                new_case_list = [] 

                cutoff_date = datetime.now() - timedelta(days=10)

                json_data_list = payload_file_data[0][0]["cases"]
                for case in json_data_list:
                    if datetime.strptime(case["timestamp"], '%Y-%m-%d %H:%M:%S') > cutoff_date:
                        new_case_list.append(case)

                payload_file_data[0][0]["cases"] = new_case_list

                with open(payload_file, 'w') as f:
                    json.dump(payload_file_data, f, indent=4)

            time.sleep(86400)
    
    except Exception as e:
        error_message = 'Error in remove old payload entry'
        send_mail_or_logging(error_message, e)

def continuous_receiving_data(connection, initial_byte):
    """Continuously receive data from the machine."""
    global STOP_THREAD
    byte_array = []
    file = None

    def handle_data_block(byte):
        nonlocal byte_array
        byte_array.append(chr(ord(byte)))

    def handle_start_of_data(byte):
        nonlocal file, byte_array
        byte_array = [chr(ord(byte))]
        connection.write(b'\x06')  # Send ACK
        cur_file = connection.get_filename()
        if file:
            file.close()
        file = open(cur_file, 'w')
        write_data_to_file(file, byte_array)

    def handle_end_of_block():
        nonlocal byte_array
        connection.write(b'\x06')
        write_data_to_file(file, byte_array)
        byte_array = []

    def handle_end_of_transmission():
        nonlocal file, byte_array
        global STOP_THREAD
        if file:
            write_data_to_file(file, byte_array)
            logger.info(f'Data written to file: {file.name}')
            file.close()
        byte_array = []
        STOP_THREAD = False

    try:
        logger.info("Started unidirectional reading...")

        # Process the initial byte if provided
        if initial_byte == b'\x05':
            try:
                handle_start_of_data(initial_byte)
            except Exception as e:
                send_mail_or_logging('Exception in open file', e)

        while STOP_THREAD and connection:
            try:
                byte = connection.read()
                if not byte:
                    continue

                if byte == b'\x05':
                    try:
                        handle_start_of_data(byte)
                    except Exception as e:
                        send_mail_or_logging('Exception in open file', e)

                elif byte == b'\x0a':
                    try:
                        handle_end_of_block()
                    except Exception as e:
                        send_mail_or_logging('Exception in write file', e)

                elif byte == b'\x04':
                    try:
                        handle_end_of_transmission()
                    except Exception as e:
                        send_mail_or_logging('Exception in close file', e)

                else:
                    handle_data_block(byte)

            except Exception as e:
                send_mail_or_logging('Exception in data receive', e)

        logger.info("Stopped unidirectional reading.")
        
    except Exception as e:
        send_mail_or_logging('Exception in continuous receiving data', e)


# Method for create case in machine
def create_case_in_machine(connection, case_no, test_id, sample_type, sample_type_number, patient_name, gender):
    """Send commands to the machine to create a case."""
    global byte
    try:
        dt = datetime.now()
        logger.info(" ")
        logger.info("***  CASE CREATION PROCESS STARTED  ***")
        logger.info("*****************************************************")
        connection.write(generate_checksum.ENQ.encode())
        byte = connection.read()
        if byte == generate_checksum.ACK.encode():
            # Step 1: Send header message
            header_message = rf"1H|\^&|||Mindry^^|||||||SA|1394-97|{dt.strftime('%Y%m%d%H%M%S%f')}"
            send_message(connection, header_message)
            if connection.read() != generate_checksum.ACK.encode():
                return {"status": "error", "message": "Header Message Not Acknowledged"}
            logger.info(f"HEADER MESSAGE :-       {header_message}")

            # Step 2: Send patient message
            patient_id = re.sub(r'[A-Za-z]', '', case_no)
            if '-' in patient_id:
                patient_id = patient_id.split('-')[0]
            patient_message = f"2P|1||{patient_id}||{patient_name}||19600315^45^Y|{gender}||keshi||||||||zhenduan||01|||||A1|002||||||||"
            send_message(connection, patient_message)
            if connection.read() != generate_checksum.ACK.encode():
                return {"status": "error", "message": "Patient Message Not Acknowledged"}
            logger.info(f"PATIENT MESSAGE :-      {patient_message}")

            # Step 3: Send order message
            order_message = f"3O|1||{case_no}|{test_id}|R|{dt.strftime('%Y%m%d%H%M%S%f')}|{dt.strftime('%Y%m%d%H%M%S%f')}||||||||{sample_type}||||||||||O|||||"
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
                return {"status": "success", "message": "Case created successfully", "case_no":case_no}
            else:
                return {"status": "error", "message": "Termination Message Not Acknowledged", "case_no":case_no}
        else:
            return {"status": "error", "message": "ENQ Message Not Acknowledged", "case_no":case_no}
    except Exception as e:
        error_message = 'Exception during case creation process'
        send_mail_or_logging(error_message, e)
        return {"status": "error", "message": str(e)}
        
# Method for calling create case function
def retry_api_call(connection, case_id, test_id, sample_type, machine_id, patient_name, gender):
    """Retry API call to ensure the case is created."""
    global CASE_CREATION_FALG, STOP_THREAD, MONITORING_ACTIVE
    try:
        STOP_THREAD = False
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
                if not STOP_THREAD:
                    response = create_case_in_machine(connection, case_id, test_id, sample_type, sample_type_number, patient_name, gender)
                    if response["status"] == "success":
                        case_entry = {"case_id": case_id, "test_id": test_id, "sample_type": sample_type, "sample_type_number": sample_type_number, "machine_id":machine_id, "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "status":"Complate"}
                        add_new_case_entry(case_entry, CASE_FILE)
                        logger.info(f"COUNTER :- {counter}")
                        CASE_CREATION_FALG = False
                        
                        MONITORING_ACTIVE = True
                        logger.info("Case creation completed, resuming monitoring...")
                        return response
                    
            except Exception as e:
                error_message = 'Error in API call'
                send_mail_or_logging(error_message, e)
                case_entry = {"case_id": case_id, "test_id": test_id, "sample_type": sample_type, "sample_type_number": sample_type_number, "machine_id":machine_id, "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "status":"Uncomplate"}
                add_new_case_entry(case_entry, CASE_FILE)

            counter+=1
            time.sleep(3)
    except Exception as e:
        error_message = 'Exception in retry api call'
        send_mail_or_logging(error_message, e)
    finally:
        MONITORING_ACTIVE = True

def checking_api_calling_and_data_reading(connection):
    """Continuously monitor for data from machine - starts on startup"""
    global STOP_THREAD, CASE_CREATION_FALG, MONITORING_ACTIVE
    
    logger.info("Started continuous monitoring for machine data...")
    
    while True: 
        try:
            if MONITORING_ACTIVE and not CASE_CREATION_FALG:
                try:
                    if hasattr(connection, 'settimeout'):
                        connection.settimeout(1.0)
                    
                    byte = connection.read()
                    
                    if byte and byte != b'':
                        STOP_THREAD = True
                        continuous_receiving_data(connection, byte)
                        
                    elif byte == generate_checksum.ACK.encode():
                        logger.info("Received ACK from machine")
                        
                except socket.timeout:
                    pass
                except Exception as e:
                    if "timed out" not in str(e).lower():
                        send_mail_or_logging('Exception while monitoring data', e)
                        
            else:
                if CASE_CREATION_FALG:
                    logger.info("Monitoring paused - API call in progress")
                time.sleep(0.5)  
                
        except Exception as e:
            send_mail_or_logging('Critical exception in monitoring loop', e)
            time.sleep(5) 
            
        time.sleep(0.1)  

# API routes
@app.post(f"/create_case/P7118")
async def api_create_case(request: CreateCaseRequest, background_tasks: BackgroundTasks):
    """API endpoint to create a case."""
    global CASE_CREATION_FALG, MONITORING_ACTIVE, CONNECTION_CL_900_I
    
    try:
        logger.info(f"API called for case creation: {request.case_id}")
        
        # Stop monitoring temporarily while processing API
        CASE_CREATION_FALG = True
        MONITORING_ACTIVE = False
        logger.info("Monitoring paused for API processing")
        
        # Wait a moment for monitoring to pause
        await asyncio.sleep(0.5)
        
        # Add the case creation task to background
        background_tasks.add_task(
            retry_api_call,
            CONNECTION_CL_900_I,
            request.case_id,
            request.test_id,
            request.sample_type,
            request.machine_id,
            request.patient_name,
            request.gender
        )
        
        return {"status": 200, "statusState": "success", "message": "Case Creation Started"}
        
    except Exception as e:
        error_message = 'Exception in api call'
        send_mail_or_logging(error_message, e)
        
        # Resume monitoring even if API fails
        CASE_CREATION_FALG = False
        MONITORING_ACTIVE = True
        
        raise HTTPException(
            status_code=400,
            detail={
                "status": 400,
                "statusState": "error",
                "message": f"Case Creation Error: {e}"
            }
        )

# Try to establish connection
try:
    CONNECTION_CL_900_I = MachineConnectionTcp(
        server_ip=HOST_ADDRESS,
        server_port=HOST_CONNECTION_PORT, 
        machine_name=REPORT_FILE_PREFIX
    )
    
    port_cl_900_i = CONNECTION_CL_900_I.get_connection()
    logger.info(f"Connection established on port: {port_cl_900_i}")
except Exception as e:
    error_message = 'Failed to establish machine connection'
    send_mail_or_logging(error_message, e)

# Start monitoring thread on startup
def start_monitoring():
    """Start the monitoring thread"""
    global CONNECTION_CL_900_I
    try:
        monitoring_thread = threading.Thread(
            target=checking_api_calling_and_data_reading, 
            args=(CONNECTION_CL_900_I,), 
            daemon=True,
            name="MonitoringThread"
        )
        monitoring_thread.start()
        logger.info("Monitoring thread started")

    except Exception as e:
        error_message = 'Failed to establish machine connection'
        send_mail_or_logging(error_message, e)

async def check_connection():
    global MONITORING_ACTIVE, CONNECTION_CL_900_I
    try:
        while True:
            MONITORING_ACTIVE = False
            logger.info("Monitoring paused for checking connection")

            await asyncio.sleep(0.5)
            
            CONNECTION_CL_900_I.write(generate_checksum.ENQ.encode())

            byte = CONNECTION_CL_900_I.read()

            if byte == generate_checksum.ACK.encode():
                CONNECTION_CL_900_I.write(generate_checksum.EOT.encode())

                logger.info("Machine Still Connected")
                MONITORING_ACTIVE = True
                logger.info("Monitoring Start")
            else:
                CONNECTION_CL_900_I.close_connection()
                time.sleep(2)
                port_cl_900_i = CONNECTION_CL_900_I.get_connection()

            time.sleep(3600)
            
    except Exception as e:
        CONNECTION_CL_900_I.close_connection()
        time.sleep(2)
        port_cl_900_i = CONNECTION_CL_900_I.get_connection()
        error_message = 'Failed to establish machine connection'
        send_mail_or_logging(error_message, e)

# Main
if __name__ == "__main__":
    try:
        logger.info(f"Starting FastAPI server on {HOST_ADDRESS}:{HOST_PORT}")
        
        # Start monitoring before starting the server
        start_monitoring()
        
        threading.Thread(target=remove_old_case_entry, args=(CASE_FILE,), daemon=True).start()
        threading.Thread(target=remove_old_logs_from_log_file, args=(LOG_FILE_LIST,), daemon=True).start()
        threading.Thread(target=check_connection, daemon=True).start()

        # Start the FastAPI server
        uvicorn.run(app, host=HOST_ADDRESS, port=HOST_PORT)
        
    except Exception as e:
        error_message = 'Exception in main function'
        send_mail_or_logging(error_message, e)