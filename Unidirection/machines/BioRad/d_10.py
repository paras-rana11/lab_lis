import sys
import logging
import datetime
import serial
import os
import time
import threading

# Configuration
connection_type = 'tty'
input_tty = 'COM4'
output_folder = 'C:\\ASTM\\root\\report_file\\'
log_file = 'port_status_for_d_10.log'
disconnect_interval = 600  # 10 minutes
log_retention_hours = 48  # 2 days
log_check_interval = 86400  # 24 hours (in seconds)

def manage_log_file():
    """Deletes the log file if it's older than 48 hours and creates a new one."""
    while True:
        if os.path.exists(log_file):
            file_age = time.time() - os.path.getmtime(log_file)  # File age in seconds
            if file_age > log_retention_hours * 3600:  # Convert hours to seconds
                os.remove(log_file)
                print(f"Deleted old log file: {log_file}")
                logging.info(f"Deleted old log file: {log_file}")

        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
        logging.info("Log file initialized.")

        time.sleep(log_check_interval)

def get_filename(extension="txt"):
  dt = datetime.datetime.now()
  return output_folder + "d_10_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f") + f".{extension}"

def get_port():
  try:
    s = serial.Serial(port=input_tty, baudrate=9600, timeout=1, xonxoff=True)
    print(f"Serial port {input_tty} opened successfully")
    return s
  except serial.SerialException as se:
    print(f"Error opening serial port: {se}")
    sys.exit(1)

def my_read(port):
  data = port.read(1)
  # print(f"Received: {data}")
  return data

def my_write(port, byte):
  port.write(byte)
  # print(f"ACK Sent: {byte}")

threading.Thread(target=manage_log_file, daemon=True).start()
# Open Serial Port
port = get_port()
logging.info(f"Connected to port: {port}")

byte_array = []
cur_file = None  # Track the current file
x = None  # File handler
while True:
  byte = my_read(port)

  if not byte:
    # print("Empty Bit Receiving!")
    continue

  byte_array.append(byte.decode(errors="ignore"))  # Properly decode bytes
  # print(f"Received byte: {byte} = {ord(byte)}")

  if byte == b'\x05':  # Start of a new message
    # print("Start of new message detected")
    byte_array = [byte.decode(errors="ignore")]
    my_write(port, b'\x06')

    # Open a new file
    cur_file = get_filename()
    try:
      x = open(cur_file, 'w', encoding="utf-8")
      x.write(''.join(byte_array))  # Initial write
      x.flush()
    except IOError as ioe:
      print(f"File write error: {ioe}")

  elif byte == b'\x0a':  # Line break
    my_write(port, b'\x06')
    if x:
      try:
        x.write(''.join(byte_array) + '\n')
        x.flush()  # Ensure data is written
        byte_array = []
      except Exception as e:
        print(f"Error writing to file: {e}")

  elif byte == b'\x04':  # End of message
    if x:
      try:
        x.write(''.join(byte_array))
        x.close()
        print(f'File saved: {cur_file}')
        # logging.info(f'File saved: {cur_file}')
      except Exception as e:
        print(f"Error closing file: {e}")
    byte_array = []
