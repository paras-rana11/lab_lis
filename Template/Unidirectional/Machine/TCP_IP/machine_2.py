import socket
import os
from datetime import datetime, timedelta
import threading
import time
import logging
import smtplib
from email.message import EmailMessage
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuration variables
HOST = '192.168.3.141'  
PORT = 5600
FILE_NAME_PREFIX = ''

REPORT_FILE_PATH = 'C:\\ASTM\\root\\report_file\\'
os.makedirs(REPORT_FILE_PATH, exist_ok=True)

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
def send_mail_or_logging(error_message, error):
    logger.error(f'{error_message} : {error}')

    body = f"""
    Dear Team,

    This is an automated alert from the Laboratory Information System.

        --> {error_message} :: Below are the details of the incident:

        - Filename: database.py
        - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        - Error Details: {error}

    Best regards,  
    Laboratory Information System  
    [Healthray LAB]
    """

    is_send_mail = send_email(SUBJECT, body, TO_EMAIL, FROM_EMAIL, PASSWORD)
    if not is_send_mail:
        logger.error(f"Exception during sending mail")

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
    try:
        return data.decode('utf-8')
    except Exception as e:
        error_message = 'Error in remove old log'
        send_mail_or_logging(error_message, e, 'MAchine_Name')
        return None


def save_data_to_file(data):
    try:

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_path = os.path.join(REPORT_FILE_PATH, f'{FILE_NAME_PREFIX}{timestamp}.txt')

        with open(file_path, 'a') as file:
            file.write(data + '\n')

        # print(f"Data saved to {file_path}")
        logger.info(f"Data saved to {file_path}")
    except Exception as e:
        error_message = 'Error in save data in txt file'
        send_mail_or_logging(error_message, e, 'MAchine_Name')


def communicate_with_machine():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((HOST, PORT))
            server_socket.listen()
            logger.info(f"Server listening on {HOST}:{PORT}")
            conn, addr = server_socket.accept()
            logger.info(f"Connected to {addr}")
            with conn:
                while True:
                    try:
                        data = conn.recv(1024)
                        if not data:
                            pass
                        
                        processed_data = process_data(data)
                        save_data_to_file(processed_data)
                    except Exception as e:
                        error_message = 'Error in reading data from socket'
                        send_mail_or_logging(error_message, e, 'MAchine_Name')
                    
    except Exception as e:
        error_message = 'Error in communication'
        send_mail_or_logging(error_message, e, 'MAchine_Name')

    finally:
        logging.info("Closing connection...")
        conn.close()

    threading.Timer(5, communicate_with_machine).start()

if __name__ == '__main__':
    try:
        threading.Thread(target=remove_old_logs_from_log_file, args=(LOG_FILE_LIST,), daemon=True).start()
        communicate_with_machine()

    except Exception as e:
        error_message = 'Error in main function'
        send_mail_or_logging(error_message, e, 'MAchine_Name')