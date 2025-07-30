
import socket
import os
import time
import threading
from datetime import datetime, timedelta
import logging
import smtplib
import threading
from email.message import EmailMessage

# Configuration
MACHINE_HOST = '192.168.3.190'
MACHINE_PORT = 1182
output_folder = 'C:\\ASTM\\root\\report_file\\'

log_file = 'C:\\ASTM\\root\\log_file\\logging_for_gem_premier_3000.log'
error_log_file = 'C:\\ASTM\\root\\log_file\\logging_for_gem_premier_3000_error.log'

log_check_interval = 86400  # 24 hours (in seconds)

subject = ""
to_email = ""
from_email = ""
password = "" 

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
    logger.error(f"Failed to send email: {e}")

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
    body_for_connection = (f" *********** error in LOG file initialize ***********  \n Error :-  {e}")
    send_email(subject, body_for_connection, to_email, from_email, password)

# log = setup_loggers()
logger = setup_loggers()

logger.info("Log file initialized.")
logger.error("Error Log file initialized.")

log_file_list = [log_file, error_log_file]

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
            
            time.sleep(log_check_interval)
    except Exception as e:
        logger.error(f"Exception in delete old log :- {e}")
        body_for_db = f' ********************** Exception in delete old log ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

def get_filename():
    try:
        dt = datetime.now()
        return output_folder + "gem_premier_3000_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")
    except Exception as e:
        logger.error(f"Error in Get File name :- {e}")
        body_for_connection = (f" *********** Error in Get File name ***********  \n{e}")
        send_email(subject, body_for_connection, to_email, from_email, password)
        return None

def my_read(port):
    try:
        return port.recv(1)
    except Exception as my_ex:
        body_for_connection = (f" *********** Error in read byte from port ***********  \n{my_ex}")
        send_email(subject, body_for_connection, to_email, from_email, password)
        logger.error(f'Error in read byte from port :- {my_ex}')
        return b''

  
def my_write(port, byte):
    try:
        return port.send(byte)
    except Exception as my_ex:
        logger.error(f'Error in write byte to port :- {my_ex}')
        body_for_connection = (f" *********** Error in write byte to port ***********  \n{my_ex}")
        send_email(subject, body_for_connection, to_email, from_email, password)

def communicate_with_machine():
    """Connects to the machine, receives data"""
    global s
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((MACHINE_HOST, MACHINE_PORT))
            print(f"Connected to machine at {MACHINE_HOST}:{MACHINE_PORT}")
            logging.info(f"Connected to machine at {MACHINE_HOST}:{MACHINE_PORT}")

            while True:
          
                byte = my_read(s)
                # if byte == b'':
                #     print('<EOF> reached. Connection broken: details below')
                #     break

                if byte == b'\x05':  # Start of Transmission
                    byte_array = [byte.decode('latin1')]
                    my_write(s, b'\x06')  # Acknowledge
                    cur_file = get_filename()
                    try:
                        x = open(cur_file, 'w')
                        x.write(''.join(byte_array))
                    except IOError as ioe:
                        body_for_error_in_opening_file = f"Error opening file {cur_file}: {ioe}"
                        send_email(subject, body_for_error_in_opening_file, to_email, from_email, password)
                        logger.error(f"Error opening file {cur_file}: {ioe}")

                elif byte == b'\x0a':  # Line Feed
                    my_write(s, b'\x06')  # Acknowledge
                    try:
                        x = open(cur_file, 'w')
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
                            # print(f'File closed :- {cur_file}')
                    except Exception as e:
                        body_for_error_in_data_written = f"Error Occur When Data Written to file {e}"
                        send_email(subject, body_for_error_in_data_written, to_email, from_email, password)
                        logger.error(f"Error closing file: {e}")


                else:
                    byte_array.append(byte.decode('latin1'))

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
    threading.Thread(target=remove_old_logs_from_log_file, args=(log_file_list,), daemon=True).start()

    communicate_with_machine()
