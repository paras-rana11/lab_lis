import socket
import os
from datetime import datetime
import datetime
import threading
import logging
import time
import smtplib
from email.message import EmailMessage

# Configuration variables
HOST = '192.168.3.141'  # or your specific IP address
PORT = 5150  # or your specific port
output_folder = 'C:\\ASTM\\root\\report_file\\'
disconnect_interval = 7200  

log_file = 'C:\\ASTM\\root\\log_file\\port_status_for_xn_1000.log'
error_log_file = 'C:\\ASTM\\root\\log_file\\port_status_for_xn_1000_error.log'
log_file_list = [log_file,error_log_file]

subject = ""
to_email = ""
from_email = ""
password = "" 

log_retention_hours = 96  # 2 days
log_check_interval = 86400  # 24 hours (in seconds)

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

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
    logger.info(f"Failed to send email: {e}")

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
        print(f"Error in log file initialization :- {e}")
        body_for_db = f' ********************** Error in log file initialization ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

logger = setup_loggers()
logger.info("Log file initialized.")
logger.error("This is an error log example.")

def manage_log_file(log_file_list):
    """Deletes the log file if it's older than 48 hours and creates a new one."""
    try:
        logger.info("Thread Started")
        while True:
            for log_file in log_file_list:
                if os.path.exists(log_file):
                    file_age = time.time() - os.path.getmtime(log_file)  # File age in seconds
                    if file_age > log_retention_hours * 3600:  # Convert hours to seconds
                        os.remove(log_file)
                        logger.info(f"Deleted old log file: {log_file}")

            time.sleep(log_check_interval)
    except Exception as e:
        logger.error(f"Exception in delete old log :- {e}")
        body_for_db = f' ********************** Exception in delete old log ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

def process_data(data):
    # Decode bytes using UTF-8, replacing invalid characters
    try:
        return data.decode('utf-8', errors='replace')

    except Exception as e:
        logger.error(f"Exception during decode text :- {e}")
        body_for_db = f' ********************** Exception during decode text ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)
        return None

def get_filename():
    try:
        dt = datetime.datetime.now()
        return output_folder + "xn_1000_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")
    except Exception as e:
        logger.error(f"Exception during creating new txt file :- {e}")
        body_for_db = f' ********************** Exception during creating new txt file ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)
        return None


def my_read(port):
    try:
        return port.recv(1)
    except Exception as e:
        logger.error(f"Exception during reading data from port :- {e}")
        body_for_db = f' ********************** Exception during reading data from port ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)
        return b''

def my_write(port, byte):
    try:
        return port.send(byte)
    except Exception as e:
        logger.error(f"Exception during writing data to port :- {e}")
        body_for_db = f' ********************** Exception during writing data to port ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

def get_actual_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a dummy address, doesn't have to be reachable
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

threading.Thread(target=manage_log_file, args=(log_file_list,), daemon=True).start()

byte_array = []
x = None

start_time = time.time()

byte_array = []
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
                while time.time() - start_time < disconnect_interval:
                
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
                        except IOError as ioe:
                            body_for_error_in_opening_file = f"Error opening file {cur_file}: {ioe}"
                            send_email(subject, body_for_error_in_opening_file, to_email, from_email, password)
                            logger.error(f"Error opening file {cur_file}: {ioe}")

                    elif byte == b'\x0a':  # Line Feed
                        my_write(conn, b'\x06')  # Acknowledge
                        try:
                            x = open(cur_file, 'w', encoding='latin1')
                            x.write(''.join(byte_array))
                        except IOError as ioe:
                            body_for_error_in_data_written = f"Error Occur When Data Written to file {e}"
                            send_email(subject, body_for_error_in_data_written, to_email, from_email, password)
                            logger.error(f"Error writing to file: {e}")

                    elif byte == b'\x04':  # End of Transmission
                        try:
                            if x:
                                x.write(''.join(byte_array))
                                x.close()
                                x = None
                                byte_array = []
                                logger.info(f'File closed :- {cur_file}')
                        except Exception as e:
                            body_for_error_in_data_written = f"Error Occur When Data Written to file {e}"
                            send_email(subject, body_for_error_in_data_written, to_email, from_email, password)
                            logger.error(f"Error closing file: {e}")

                    else:
                        byte_array.append(byte.decode('latin1'))
        else:
            # start_tray()
            pass
    except Exception as e:
        body_for_connection = (f" *********** Exception Occur in reading data ***********  \n {e}")
        send_email(subject, body_for_connection, to_email, from_email, password)
        logger.error(f"Exception Occur in reading data :- {e}")

    finally:
        print("Closing connection...")
        logger.info("Closing connection...")
        conn.close()

    threading.Timer(5, communicate_with_machine).start()

# Start the processes
if __name__ == '__main__':
    try:
        threading.Thread(target=manage_log_file, args=(log_file_list,), daemon=True).start()
        communicate_with_machine()
    except Exception as e:
        body_for_connection = (f" *********** Error in main fuction ***********  \n {e}")
        send_email(subject, body_for_connection, to_email, from_email, password)
        logger.error(f"Exception Occur in main function :- {e}")