import os
import datetime
import time
import logging
import threading
import socket
import smtplib
from email.message import EmailMessage

connection_type='tcp'
host_address='192.168.19.108'
host_port='5150'

s = None
x = None
log = 1
output_folder = 'C:\\ASTM\\root\\report_file\\'
alarm_time = 10
log_file = 'C:\\ASTM\\root\\log_file\\logging_for_hemax_33.log'
error_log_file = 'C:\\ASTM\\root\\log_file\\logging_for_hemax_33_error.log'
log_file_list = [log_file, error_log_file]

log_retention_hours = 96  # 2 days
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
    print(f"Error in log file initialization :- {e}")
    body_for_db = f' ********************** Error in log file initialization ********************** \n {e}'
    send_email(subject, body_for_db, to_email, from_email, password)

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

                            if current_time - log_timestamp < log_retention_hours * 3600:
                                updated_lines.append(line)
                        except Exception as e:
                            print(f"Skipping malformed line: {line} - Error: {e}")

                    # Rewrite file with only recent logs
                    with open(log_file, "w") as file:
                        file.writelines(updated_lines)
        except  Exception as e:
            logging.info(f"Error When Removing Old Log")

        finally:
            time.sleep(log_check_interval) 

byte_array = []

def get_filename():
  try:
    dt = datetime.datetime.now()
    return output_folder + "hemax_33_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")
  except Exception as e:
    logger.error(f"Exception in delete old log :- {e}")
    body_for_db = f' ********************** Exception in delete old log ********************** \n {e}'
    send_email(subject, body_for_db, to_email, from_email, password)

def get_port():
  global s
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    """Set TCP keepalive on an open socket.
    It activates after 1 second (after_idle_sec) of idleness,
    then sends a keepalive ping once every 3 seconds (interval_sec),
    and closes the connection after 5 failed ping (max_fails), or 15 seconds
    """
    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

    try:
      s.bind((host_address, int(host_port)))  # it is a tuple
    except Exception as e:
      logger.error(f"Exception in bind ip and port :- {e}")
      body_for_db = f' ********************** Exception in bind ip and port ********************** \n {e}'
      send_email(subject, body_for_db, to_email, from_email, password)
    s.listen(1)

    # Initialize conn_tuple here to avoid the NameError
    conn_tuple = s.accept()
    
    return conn_tuple[0]
  except Exception as e:
    logger.error(f"Exception in connection :- {e}")
    body_for_db = f' ********************** Exception in connection ********************** \n {e}'
    send_email(subject, body_for_db, to_email, from_email, password)

def my_read(port):
  try:
    return port.recv(1)
  except Exception as e:
    logger.error(f"Exception in reading data from port :- {e}")
    body_for_db = f' ********************** Exception in reading data from port ********************** \n {e}'
    send_email(subject, body_for_db, to_email, from_email, password)
    return b''

def my_write(port, byte):
  try:
    return port.send(byte)
  except Exception as e:
    logger.error(f"Exception in writing data to port :- {e}")
    body_for_db = f' ********************** Exception in writing data to port ********************** \n {e}'
    send_email(subject, body_for_db, to_email, from_email, password)

def process_data(data):
    """Process received data by stripping control characters."""
    data = data.strip(b'\x0B\x1C\x0D')
    return data.decode('utf-8')

def save_data_to_file(data):
    """Save processed data to a timestamped file."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'hemax_33_{timestamp}.txt')
    
    with open(file_path, 'a') as file:
        file.write(data + '\n')
    
    print(f"Data saved to {file_path}")
    logging.info(f"Data saved to {file_path}")

#main loop##########################
threading.Thread(target=manage_log_file, args=(log_file_list,), daemon=True).start()

port = get_port()
byte_array = []
cur_file = None
if port:
  print(f"Connected to {port}")

buffer = b""

try:
  while True:
    if not port:
      port = get_port()
      if port:
        print(f"Connected to {port}")
        
    byte = my_read(port)
    print("--->",byte)
    if(byte == b''):
      print('<EOF> reached. Connection broken: details below')

      if(connection_type == 'tcp'):
        conn_tuple = s.accept()
        port = conn_tuple[0]

    else:
      byte_array = byte_array + [chr(ord(byte))]

    data = "".join(byte_array)
    if data:
        buffer += data
    if b'\x1C\x0D' in data:                                             
        messages = buffer.split(b'\x1C\x0D')
        for message in messages[:-1]:
            processed_data = process_data(message)
            save_data_to_file(processed_data)
        buffer = messages[-1]

    # if(byte == b'\x05'):
    #   try:
    #     byte_array = []
    #     byte_array = byte_array + [chr(ord(byte))]
    #     my_write(port, b'\x06')
    #     cur_file = get_filename()
    #     x = open(cur_file, 'w')
    #   except Exception as e:
    #     logger.error(f"Exception creating new file :- {e}")
    #     body_for_db = f' ********************** Exception creating new file ********************** \n {e}'
    #     send_email(subject, body_for_db, to_email, from_email, password)

    # elif(byte == b'\x0a'):
    #   my_write(port, b'\x06')
    #   try:
    #     x.write(''.join(byte_array))
    #     byte_array = []
    #   except Exception as e:
    #     logger.error(f"Exception in writing data in file LF :- {e}")
    #     body_for_db = f' ********************** Exception in writing data in file LF ********************** \n {e}'
    #     send_email(subject, body_for_db, to_email, from_email, password)

    # elif(byte == b'\x04'):

    #   try:
    #     if x is not None:
    #       x.write(''.join(byte_array))
    #       logger.info(f"File saved {cur_file}")
    #       x.close()

    #   except Exception as e:
    #     logger.error(f"Exception in writing data in file EOT :- {e}")
    #     body_for_db = f' ********************** Exception in in writing data in file EOT ********************** \n {e}'
    #     send_email(subject, body_for_db, to_email, from_email, password)

    #   byte_array = []

except Exception as e:
  logger.error(f"Exception in main loop :- {e}")
  body_for_db = f' ********************** Exception in main loop ********************** \n {e}'
  send_email(subject, body_for_db, to_email, from_email, password)

