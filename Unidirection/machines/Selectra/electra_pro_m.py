import socket
import time
from datetime import datetime
import datetime
import logging
import os
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import smtplib
import threading
from email.message import EmailMessage
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuration variables
HOST = '192.168.1.28'  # or your specific IP address
PORT = 5152  # or your specific port
output_folder = 'C:\\ASTM\\root\\report_file\\'
log_file = 'C:\\ASTM\\root\\log_file\\port_status_for_selectra_pro_m.log'
error_log_file = 'C:\\ASTM\\root\\log_file\\port_status_for_selectra_pro_m_error.log'

disconnect_interval = 600  # 10 minutes
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

sheet_log = client.open('Real_Lab_lIS').worksheet('Logging')
sheet_log.update(values=[['Date', 'File_Name', 'Message','Error']], range_name='A1:D1')

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
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')

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
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')

def get_actual_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    # Connect to a dummy address, doesn't have to be reachable
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
  finally:
    s.close()
  return ip

def process_data(data):
  try:
    return data.decode('utf-8', errors='replace')
  except Exception as e:
    error_message = 'Error in process data'
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')
    return None

def get_filename():
  try:
    dt = datetime.datetime.now()
    return output_folder + "selectra_pro_m_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")
  except Exception as e:
    error_message = 'Error in get_filename'
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')
    return None

def my_read(port):
  try:
    return port.recv(1)
  except Exception as e:
    error_message = 'Error in reading data from port'
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')
    return b''

def my_write(port, byte):
  try:
    return port.send(byte)
  except Exception as my_ex:
    error_message = 'Error in writing data to port'
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')

# Function to create the tray icon
def create_image():
  # Generate an image and draw on it
  try:
    image = Image.new('RGB', (64, 64), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([16, 16, 48, 48], fill="blue")
    return image
  except Exception as e:
    error_message = 'Error in create image'
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')
    return None

# Function to handle the notification
def show_notification(icon):
  try:
    icon.visible = True
    icon.notify("Your host PC has not been assigned the IP address 192.168.1.28. Please configure this IP address first.")
  except Exception as e:
    error_message = 'Error in show notifiaction'
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')

def start_tray():
  try:
    icon = Icon("test", create_image(), menu=Menu(MenuItem('Exit', lambda icon, item: icon.stop())))
    if icon:
      show_notification(icon)
  except Exception as e:
    error_message = 'Error in satrt tray'
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')

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
        print(f"Server listening on {HOST}:{PORT}")
        conn, addr = s.accept()
        logger.info(f"Connected to {conn}") 
        # body_for_connection = (f" *********** SELECTRA PRO M ***********  \n Connected To :- \n {conn}")
        # send_email(subject, body_for_connection, to_email, from_email, password)
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
              x = open(cur_file, 'w')
              x.write(''.join(byte_array))
            except IOError as e:
              error_message = 'Error in LOG file initialize'
              send_mail_or_logging(error_message, e, 'Selectra_Pro_M')

          elif byte == b'\x0a':  # Line Feed
            my_write(conn, b'\x06')  # Acknowledge
            try:
              x = open(cur_file, 'w')
              x.write(''.join(byte_array))
            except IOError as e:
              error_message = 'Error in LOG file writing'
              send_mail_or_logging(error_message, e, 'Selectra_Pro_M')

          elif byte == b'\x04':  # End of Transmission
            try:
              if x:
                x.write(''.join(byte_array))
                x.close()
                x = None
                byte_array = []
                logger.info(f'File closed :- {cur_file}')
            except Exception as e:
              error_message = 'Error in LOG file writing'
              send_mail_or_logging(error_message, e, 'Selectra_Pro_M')

          else:
            byte_array.append(byte.decode('latin1'))
    else:
      start_tray()
  except Exception as e:
    error_message = 'Error in connection'
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')

  finally:
    # print("Closing connection...")
    logger.info("Closing connection...")
    conn.close()

  threading.Timer(5, communicate_with_machine).start()

# Start the processes
if __name__ == '__main__':
  try:
      
    # threading.Thread(target=manage_log_file, args=(log_file_list,), daemon=True).start()

    communicate_with_machine()
  except Exception as e:
    error_message = 'Error in main function'
    send_mail_or_logging(error_message, e, 'Selectra_Pro_M')


