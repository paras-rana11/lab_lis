import socket
import os
from datetime import datetime
import time
import logging
import threading
import smtplib
from email.message import EmailMessage

# Configuration variables
HOST = '192.168.2.123'  
PORT = 5150 
output_folder = 'C:\\ASTM\\root\\report_file\\'

log_file = 'C:\\ASTM\\root\\log_file\\logging_for_bk_240.log'
error_log_file = 'C:\\ASTM\\root\\log_file\\logging_for_bk_240_error.log'
log_file_list = [log_file,error_log_file]

disconnect_interval = 600  # 10 minutes
log_retention_hours = 48  # 2 days
log_check_interval = 86400  # 24 hours (in seconds)

subject = ""
to_email = ""
from_email = ""
password = "" 

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

# Ensure output folder exists

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
  try:
    return data.decode('utf-8')
  except Exception as e:
    logger.error(f"Error in decode data :- {e}")
    body_for_db = f' ********************** Error in decode data ********************** \n {e}'
    send_email(subject, body_for_db, to_email, from_email, password)
    return None

def save_data_to_file(data):
  try:
    if not os.path.exists(output_folder):
      os.makedirs(output_folder)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(output_folder, f'bk_240_{timestamp}.txt')

    with open(file_path, 'a') as file:
      file.write(data + '\n')

    # print(f"Data saved to {file_path}")
    logger.info(f"Data saved to {file_path}")
  except Exception as e:
    logger.error(f"Error in save data :- {e}")
    body_for_db = f' ********************** Error in save data ********************** \n {e}'
    send_email(subject, body_for_db, to_email, from_email, password)

def communicate_with_machine():
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
      server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      server_socket.bind((HOST, PORT))
      server_socket.listen()
      print(f"Server listening on {HOST}:{PORT}")
      # logging.info(f"Server listening on {HOST}:{PORT}")
      conn, addr = server_socket.accept()
      # print(f"Connected to {addr}")
      logger.info(f"Connected to {addr}")
      start_time = time.time()
      with conn:
        while time.time() - start_time < disconnect_interval:
          try:
            data = conn.recv(1024)
            if not data:
              logger.info("Client disconnected")
              conn.close()
              break
            processed_data = process_data(data)
            save_data_to_file(processed_data)
          except ConnectionResetError:
            logger.error(f"Error in connection  :- {e}")
            body_for_db = f' ********************** Error in connection ********************** \n {e}'
            send_email(subject, body_for_db, to_email, from_email, password)
            break  
  except Exception as e:
    logger.error(f"Error in communication :- {e}")
    body_for_db = f' ********************** Error in communication ********************** \n {e}'
    send_email(subject, body_for_db, to_email, from_email, password)

  finally:
    print("Closing connection...")
    logger.info("Closing connection...")
    conn.close()

  threading.Timer(5, communicate_with_machine).start()

if __name__ == '__main__':
  try:
    threading.Thread(target=manage_log_file, args=(log_file_list,), daemon=True).start()
    communicate_with_machine()
  except Exception as e:
    logger.error(f"Error in main function :- {e}")
    body_for_db = f' ********************** Error in main function ********************** \n {e}'
    send_email(subject, body_for_db, to_email, from_email, password)