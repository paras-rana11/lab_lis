# #!/usr/bin/python3
# import sys
# import os
# import logging
# import threading

# connection_type='tcp'
# host_address='192.168.1.135'
# host_port='6501'

# s = None
# x = None
# log = 1
# output_folder = 'C:\\ASTM\\root\\report_file\\'
# alarm_time = 10
# log_file = 'port_status_for_xl_200.log'
# disconnect_interval = 600  # 10 minutes
# log_retention_hours = 48  # 2 days
# log_check_interval = 86400  # 24 hours (in seconds)

# # Ensure output folder exists
# os.makedirs(output_folder, exist_ok=True)

# def manage_log_file():
#   """Deletes the log file if it's older than 48 hours and creates a new one."""
#   while True:
#     if os.path.exists(log_file):
#       file_age = time.time() - os.path.getmtime(log_file)  # File age in seconds
#       if file_age > log_retention_hours * 3600:  # Convert hours to seconds
#         os.remove(log_file)
#         print(f"Deleted old log file: {log_file}")
#         logging.info(f"Deleted old log file: {log_file}")

#     logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
#     logging.info("Log file initialized.")

#     time.sleep(log_check_interval)
# #import other modules
# try:
#   import signal
#   import datetime
#   import time
# except ModuleNotFoundError:
#   exception_return = sys.exc_info()
#   quit()

# #import serial or socket
# if(connection_type == 'tty'):
#   try:
#     import serial
#   except ModuleNotFoundError:
#     exception_return = sys.exc_info()
#     quit()
# elif(connection_type == 'tcp'):
#   try:
#     import socket
#   except ModuleNotFoundError:
#     exception_return = sys.exc_info()
#     quit()

#   byte_array = []

# def get_filename():
#   dt = datetime.datetime.now()
#   return output_folder + "xl_200_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")

# def get_port():
#   if(connection_type == 'tty'):
#     try:
#       port = serial.Serial(input_tty, baudrate=9600)
#       return port
#     except:
#       exception_return = sys.exc_info()
#       quit()

#   elif(connection_type == 'tcp'):
#     global s
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#     """Set TCP keepalive on an open socket.
#     It activates after 1 second (after_idle_sec) of idleness,
#     then sends a keepalive ping once every 3 seconds (interval_sec),
#     and closes the connection after 5 failed ping (max_fails), or 15 seconds
#     """
#     s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

#     s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
#     s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
#     s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

#     try:
#       s.bind((host_address, int(host_port)))  # it is a tuple
#     except:
#       exception_return = sys.exc_info()
#       quit()
#     s.listen(1)

#     # Initialize conn_tuple here to avoid the NameError
#     conn_tuple = s.accept()
    
#     return conn_tuple[0]

# def my_read(port):
#   if(connection_type == 'tty'):
#     return port.read(1)
#   elif(connection_type == 'tcp'):
#     try:
#       return port.recv(1)
#     except Exception as my_ex:
#       print('Network disconnection??')
#       return b''

# def my_write(port, byte):
#   if(connection_type == 'tty'):
#     return port.write(byte)
#   elif(connection_type == 'tcp'):
#     return port.send(byte)

# #main loop##########################
# threading.Thread(target=manage_log_file, daemon=True).start()
# port = get_port()
# byte_array = []
# cur_file = None
# if port:
#   print(f"Connected to {port}")
# while True:
#   if not port:
#     port = get_port()
#     if port:
#       print(f"Connected to {port}")
      
#   byte = my_read(port)
#   print("--->",byte)
#   if(byte == b''):
#     print('<EOF> reached. Connection broken: details below')

#     if(connection_type == 'tcp'):
#       conn_tuple = s.accept()
#       port = conn_tuple[0]

#   else:
#     byte_array = byte_array + [chr(ord(byte))]

#   if(byte == b'\x05'):
#     byte_array = []
#     byte_array = byte_array + [chr(ord(byte))]
#     my_write(port, b'\x06')
#     cur_file = get_filename()
#     x = open(cur_file, 'w')

#   elif(byte == b'\x0a'):
#     my_write(port, b'\x06')
#     try:
#       x.write(''.join(byte_array))
#       byte_array = []
#     except Exception as my_ex:
#       print(my_ex)

#   elif(byte == b'\x04'):

#     try:
#       if x is not None:
#         x.write(''.join(byte_array))
#         logging.info(f"File saved {cur_file}")
#         x.close()

#     except Exception as my_ex:
#       print(my_ex)

#     byte_array = []


#!/usr/bin/python3
import sys
import os
import datetime
import time
import logging
import threading
import socket
import smtplib
from email.message import EmailMessage

connection_type='tcp'
host_address='192.168.1.135'
host_port='6501'

s = None
x = None
log = 1
output_folder = 'C:\\ASTM\\root\\report_file\\'
alarm_time = 10
log_file = 'C:\\ASTM\\root\\log_file\\port_status_for_xl_200.log'
error_log_file = 'C:\\ASTM\\root\\log_file\\port_status_for_xl_200_error.log'
log_file_list = [log_file,error_log_file]

disconnect_interval = 600  # 10 minutes
log_retention_hours = 48  # 2 days
log_check_interval = 86400  # 24 hours (in seconds)

subject = ""
to_email = ""
from_email = ""
password = "" 

disconnect_interval = 600  # 10 minutes
log_retention_hours = 48  # 2 days
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

byte_array = []

def get_filename():
  try:
    dt = datetime.datetime.now()
    return output_folder + "xl_200_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")
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

#main loop##########################
threading.Thread(target=manage_log_file,args=(log_file_list,), daemon=True).start()

port = get_port()
byte_array = []
cur_file = None
if port:
  print(f"Connected to {port}")
  
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

    if(byte == b'\x05'):
      try:
        byte_array = []
        byte_array = byte_array + [chr(ord(byte))]
        my_write(port, b'\x06')
        cur_file = get_filename()
        x = open(cur_file, 'w')
      except Exception as e:
        logger.error(f"Exception creating new file :- {e}")
        body_for_db = f' ********************** Exception creating new file ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

    elif(byte == b'\x0a'):
      my_write(port, b'\x06')
      try:
        x.write(''.join(byte_array))
        byte_array = []
      except Exception as e:
        logger.error(f"Exception in writing data in file LF :- {e}")
        body_for_db = f' ********************** Exception in writing data in file LF ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

    elif(byte == b'\x04'):

      try:
        if x is not None:
          x.write(''.join(byte_array))
          logger.info(f"File saved {cur_file}")
          x.close()

      except Exception as e:
        logger.error(f"Exception in writing data in file EOT :- {e}")
        body_for_db = f' ********************** Exception in in writing data in file EOT ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

      byte_array = []

except Exception as e:
  logger.error(f"Exception in main loop :- {e}")
  body_for_db = f' ********************** Exception in main loop ********************** \n {e}'
  send_email(subject, body_for_db, to_email, from_email, password)

