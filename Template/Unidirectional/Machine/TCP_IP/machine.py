import socket
import os
from datetime import datetime, timedelta
import threading
import logging
import time
import smtplib
from email.message import EmailMessage
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuration variables
HOST = '192.168.3.141'  # or your specific IP address
PORT = 5150  # or your specific port
FILE_NAME_PREFIX = ''

REPORT_FILE_PATH = 'C:\\ASTM\\root\\report_file\\'
os.makedirs(REPORT_FILE_PATH, exist_ok=True)

DISCONNECT_INTERVAL = 7200  

# log file path
LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_machine.log'
ERROR_LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_machine_error.log'
LOG_FILE_LIST = [LOG_FILE, ERROR_LOG_FILE]

# Email configuration
SUBJECT = ''
TO_EMAIL = ''
FROM_EMAIL = ''
PASSWORD = '' 

# Google configuration
GOOGLE_SHEET_NAME = ''
GOOGLE_WORKSHEET_NAME_FOR_PATIENT_DATA = ''
GOOGLE_WORKSHEET_NAME_FOR_LOGGING = ''

CREADENTIAL = {
}

SCOPE = []

creds = ServiceAccountCredentials.from_json_keyfile_dict(CREADENTIAL, SCOPE)  # Load credentials
client = gspread.authorize(creds)  # Authorize client
sheet_log = client.open(GOOGLE_SHEET_NAME).worksheet(GOOGLE_WORKSHEET_NAME_FOR_LOGGING)
sheet_log.update(values=[['Date', 'File_Name', 'Message','Error']], range_name='A1:D1')

# Method for setup logging
def setup_loggers(log_file, error_log_file):
    '''Set up separate loggers for info and error.'''
    logger = logging.getLogger('app_logger')
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

logger = setup_loggers(LOG_FILE, ERROR_LOG_FILE)
logger.info('Log file initialized.')
logger.error('This is an error log example.')

# Method for sending email and logging
def send_mail_or_logging(error_message, error, file_name):
    logger.error(f'{error_message} : {error}')
    body_for_email = (f'{error_message} \n {error}')
    is_send_mail = send_email(SUBJECT, body_for_email, TO_EMAIL, FROM_EMAIL, PASSWORD)
    if not is_send_mail:
        try:
            log_data = [f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', file_name, error_message, error]
            sheet_log.append_row(log_data)
        except Exception as e:
            logger.error(f"Error in append data in sheet :- {e}")

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
        send_mail_or_logging(error_message, e, 'MAchine_Name')

def process_data(data):
    # Decode bytes using UTF-8, replacing invalid characters
    try:
        return data.decode('utf-8', errors='replace')

    except Exception as e:
        error_message = 'Error in process data'
        send_mail_or_logging(error_message, e, 'MAchine_Name')
        return None

def get_filename():
    try:
        dt = datetime.now()
        return REPORT_FILE_PATH + f"{FILE_NAME_PREFIX}" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")
    except Exception as e:
        error_message = 'Error in create new file'
        send_mail_or_logging(error_message, e, 'MAchine_Name')
        return None


def my_read(port):
    try:
        return port.recv(1)
    except Exception as e:
        error_message = 'Error in read data from port'
        send_mail_or_logging(error_message, e, 'MAchine_Name')
        return b''

def my_write(port, byte):
    try:
        return port.send(byte)
    except Exception as e:
        error_message = 'Error in write data to port'
        send_mail_or_logging(error_message, e, 'MAchine_Name')
        return None

def get_actual_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a dummy address, doesn't have to be reachable
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

byte_array = []
x = None

def communicate_with_machine():
    global conn
    x = None
    cur_file = None
    try:
        if HOST == get_actual_ip():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, PORT))
                s.listen()
                logger.info(f"Server listening on {HOST}:{PORT}")
                conn, addr = s.accept()
                logger.info(f"Connected to {conn}") 
                start_time = time.time()
                while time.time() - start_time < DISCONNECT_INTERVAL:
                
                    byte = my_read(conn)
                    if byte == b'':
                        print('<EOF> reached. Connection broken: details below')
                        break

                    if byte == b'\x05':  # Start of Transmission
                        byte_array = [byte.decode('latin1')]
                        my_write(conn, b'\x06')  # Acknowledge
                        cur_file = get_filename()
                        try:
                            x = open(cur_file, 'w', encoding='latin1')
                            x.write(''.join(byte_array))
                        except IOError as e:
                            error_message = 'Error in open file'
                            send_mail_or_logging(error_message, e, 'MAchine_Name')

                    elif byte == b'\x0a':  # Line Feed
                        my_write(conn, b'\x06')  # Acknowledge
                        try:
                            x = open(cur_file, 'w', encoding='latin1')
                            x.write(''.join(byte_array))
                        except IOError as e:
                            error_message = 'Error in writing file'
                            send_mail_or_logging(error_message, e, 'MAchine_Name')

                    elif byte == b'\x04':  # End of Transmission
                        try:
                            if x:
                                x.write(''.join(byte_array))
                                x.close()
                                x = None
                                byte_array = []
                                logger.info(f'File closed :- {cur_file}')
                        except Exception as e:
                            error_message = 'Error in closing file'
                            send_mail_or_logging(error_message, e, 'MAchine_Name')

                    else:
                        byte_array.append(byte.decode('latin1'))
        else:
            # start_tray()
            pass
    except Exception as e:
        error_message = 'Error in data reading'
        send_mail_or_logging(error_message, e, 'MAchine_Name')

    finally:
        logger.info("Closing connection...")
        conn.close()

    threading.Timer(5, communicate_with_machine).start()

# Start the processes
if __name__ == '__main__':
    try:
        threading.Thread(target=remove_old_logs_from_log_file, args=(LOG_FILE_LIST,), daemon=True).start()
        communicate_with_machine()
    except Exception as e:
        error_message = 'Error in main function'
        send_mail_or_logging(error_message, e, 'MAchine_Name')