import os
import logging
import time
import datetime
import serial # type: ignore
import smtplib
import threading
import schedule
from email.message import EmailMessage
import gspread
from oauth2client.service_account import ServiceAccountCredentials

connection_type = 'tty'
input_tty = 'COM5'
s = None
x = None
output_folder = 'C:\\ASTM\\root\\report_file\\'
log_file = 'C:\\ASTM\\root\\log_file\\port_status_for_cell_tak.log'
error_log_file = 'C:\\ASTM\\root\\log_file\\port_status_for_cell_tak_error.log'
disconnect_interval = 86400  # 1 day
log_retention_hours = 48  # 2 days
log_check_interval = 86400  # 24 hours (in seconds)

subject = ""
to_email = ""
from_email = ""
password = ""  

credential = {
}

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

creds = ServiceAccountCredentials.from_json_keyfile_dict(credential, scope)  # Load credentials
client = gspread.authorize(creds)  # Authorize client

sheet_log = client.open('Real_Lab_LIS').worksheet('Logging')
sheet_log.update(values=[['Date', 'File_Name', 'Message','Error']], range_name='A1:D1')

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
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def setup_loggers():
    """Set up separate loggers for info and error."""
    try:
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
    except Exception as e:
        error_message = 'Error in LOG file initialize'
        send_mail_or_logging(error_message, e, 'Cell_Tak')

# log = setup_loggers()
logger = setup_loggers()

logger.info("Log file initialized.")
logger.error("Error Log file initialized.")

log_file_list = [log_file, error_log_file]

def send_mail_or_logging(error_message, error, file_name):
    logger.error(f'{error_message} : {error}')
    body_for_email = (f'{error_message} \n {error}')
    is_send_mail = send_email(subject, body_for_email, to_email, from_email, password)
    if not is_send_mail:
        try:
            log_data = [f'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', file_name, error_message, error]
            sheet_log.append_row(log_data)
        except Exception as e:
            logger.error(f"Error in append data in sheet :- {e}")

def manage_log_file(log_file_list):
    """Deletes the log file if it's older than 48 hours and creates a new one."""
    try:
      while True:
          for file in log_file_list:
            if os.path.exists(file):
                file_age = time.time() - os.path.getmtime(log_file)  # File age in seconds
                if file_age > log_retention_hours * 3600:  # Convert hours to seconds
                    os.remove(log_file)
                    logger.info(f"Deleted old log file: {log_file}")         

          time.sleep(log_check_interval)
    except Exception as e:
        error_message = 'Error in LOG file'
        send_mail_or_logging(error_message, e, 'Cell_Tak')


def get_filename():
    try:
      dt = datetime.datetime.now()
      return output_folder + 'cell_tak_' + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")
    except Exception as e:
        error_message = 'Error in get_filename'
        send_mail_or_logging(error_message, e, 'Cell_Tak')

def get_port():
    try:
        port = serial.Serial(port=input_tty, baudrate=9600, timeout=1)
        message = f"Connected To {port}"
        send_mail_or_logging(message, e, 'Cell_Tak')
        return port
    except serial.SerialException as se:
        error_message = 'Error in Connection'
        send_mail_or_logging(error_message, se, 'Cell_Tak')

def my_read(port):
    try:
        data = port.read(1)
        return data
    except Exception as e:
        error_message = 'Error in Reading data from port'
        send_mail_or_logging(error_message, e, 'Cell_Tak')

def my_write(port, byte):
    try:
        port.write(byte)
        # print(byte)
    except Exception as e:
        error_message = 'Error in writing data to port'
        send_mail_or_logging(error_message, e, 'Cell_Tak')

port = get_port()

def scheduler_loop():
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        error_message = 'Error in schedule loop'
        send_mail_or_logging(error_message, e, 'Cell_Tak')

# Start the scheduler in a separate thread
# threading.Thread(target=manage_log_file,args=(log_file_list,) ,daemon=True).start()
threading.Thread(target=scheduler_loop, daemon=True).start()

cur_file = None
byte_array = []
try:
    while True:
        try:
            if port:
                byte = my_read(port)
                if not byte:
                    pass
                else:
                    byte_array.append(chr(ord(byte)))

                if byte == b'\x05':
                    byte_array = [chr(ord(byte))]
                    my_write(port, b'\x06')
                    cur_file = get_filename()
                    try:
                        x = open(cur_file, 'w')
                        x.write(''.join(byte_array))
                    except IOError as ioe:
                        error_message = 'Error in txt file initialize'
                        send_mail_or_logging(error_message, e, 'Cell_Tak')

                elif byte == b'\x0a':
                    my_write(port, b'\x06')
                    try:
                        x.write(''.join(byte_array))
                        byte_array = []
                    except Exception as e:
                        error_message = 'Error in writing data in file'
                        send_mail_or_logging(error_message, e, 'Cell_Tak')

                elif byte == b'\x04':
                    try:    
                        if x:
                            x.write(''.join(byte_array))
                            x.close()
                            logger.info(f'File closed :- {cur_file}')
                    except Exception as e:
                        error_message = 'Error in writing data in file'
                        send_mail_or_logging(error_message, e, 'Cell_Tak')
                    byte_array = []
            else:
                time.sleep(10)
                port = get_port()
        except Exception as e:
            error_message = 'Error in main loop'
            send_mail_or_logging(error_message, e, 'Cell_Tak')
except Exception as e:
    error_message = 'Error in main loop'
    send_mail_or_logging(error_message, e, 'Cell_Tak')