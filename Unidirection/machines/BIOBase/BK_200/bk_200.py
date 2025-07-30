import socket
import os
from datetime import datetime, timedelta
import threading
import logging
import time
import smtplib
from email.message import EmailMessage
 
# Configuration
CONNECTION_TYPE = 'TCP'
HOST = '192.168.1.111'  
PORT = 5151
FILE_NAME_PREFIX = 'bk_200_'
 
LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_bk_200_info.log'
ERROR_LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_bk_200__error.log'
LOG_FILE_LIST = [LOG_FILE, ERROR_LOG_FILE]
 
log_check_interval = 86400  # 24 hours (in seconds)
 
SUBJECT = "Email From Bio Systems Hospital"
TO_EMAIL = "lishealthray@gmail.com"
FROM_EMAIL = "lishealthray@gmail.com"
PASSWORD = "rxbr zlzy tpin pgur"
 
# Ensure output folder exists
REPORT_FILE_PATH = 'C:\\ASTM\\root\\report_file\\'
os.makedirs(REPORT_FILE_PATH, exist_ok=True)
 
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
 
        - Filename: bk_200_uyo.py
        - Connetion Type: {CONNECTION_TYPE}
        - Machine Name: Biobase BK 200
        - Machine Host: {HOST}
        - Port: {PORT}
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
        error_message = 'Error in remove old log'
        send_mail_or_logging(error_message, e)
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
 
def process_data(data):
    # Decode bytes using UTF-8, replacing invalid characters
    try:
        return data.decode('utf-8', errors='replace')
 
    except Exception as e:
        error_message = 'Error in remove old log'
        send_mail_or_logging(error_message, e)
        return None
 
def get_filename():
    try:
        dt = datetime.now()
        return REPORT_FILE_PATH + FILE_NAME_PREFIX + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")
    except Exception as e:
        error_message = 'Error in create new file'
        send_mail_or_logging(error_message, e)
        return None
 
def my_read(port):
    try:
        return port.recv(1)
    except Exception as e:
        error_message = 'Error in receive data'
        send_mail_or_logging(error_message, e)
        return b''
 
def my_write(port, byte):
    try:
        return port.send(byte)
    except Exception as e:
        error_message = 'Error in write data'
        send_mail_or_logging(error_message, e)
        return None
 
def communicate_with_machine():
    global conn
    x = None
    cur_file = None
    byte_array = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            logger.info(f"Server listening on {HOST}:{PORT}")
            conn, addr = s.accept()
            logger.info(f"Connected to {conn}")
            while True:
                byte = my_read(conn)

                if byte == b'\x0b':  # Start of Transmission
                    byte_array = [byte.decode('latin1')]
                    cur_file = get_filename()
                    try:
                        x = open(cur_file, 'w')
                    except IOError as e:
                        send_mail_or_logging('Error creating new file', e)

                elif byte == b'\r':  # Line Feed
                    byte_array.append('\n')  

                elif byte == b'\x1c':  # End of Transmission
                    try:
                        if x:
                            x.write(''.join(byte_array))
                            x.close()
                            logger.info(f'File closed :- {cur_file}')
                            x = None
                            byte_array = []
                    except Exception as e:
                        send_mail_or_logging('Error in closing txt file', e)

                else:
                    try:
                        byte_array.append(byte.decode('latin1'))
                    except Exception as e:
                        send_mail_or_logging('Error in write in byte array', e)

    except Exception as e:
        send_mail_or_logging('Error in main loop', e)

    finally:
        logger.info("Closing connection...")
        if conn:
            conn.close()

    threading.Timer(5, communicate_with_machine).start()

# Start the processes
if __name__ == '__main__':
    try:
        threading.Thread(target=remove_old_logs_from_log_file, args=(LOG_FILE_LIST,), daemon=True).start()
        communicate_with_machine()
    except Exception as e:
        error_message = 'Error in main function'
        send_mail_or_logging(error_message, e)