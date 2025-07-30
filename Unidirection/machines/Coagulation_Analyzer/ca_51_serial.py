import sys
import signal
import datetime
import serial  # type: ignore
import os
import time

input_tty = 'COM3'
output_folder = 'C:\\ASTM\\root\\report_file\\'

os.makedirs(output_folder, exist_ok=True)

def signal_handler(signal, frame):
    sys.exit(0)

def get_port():
    try:
        port = serial.Serial(port=input_tty, baudrate=19200, timeout=1)
        return port
    except serial.SerialException as se:
        sys.exit(1)

def my_read(port):
    return port.read(1)

def my_write(port, byte):
    port.write(byte)

def get_filename():
    dt = datetime.datetime.now()
    return os.path.join(output_folder, 'ca_51_' + dt.strftime("%Y-%m-%d-%H-%M-%S") + '.txt')

signal.signal(signal.SIGBREAK, signal_handler)

port = get_port()

data_buffer = ""
last_received_time = time.time()  
idle_timeout = 2 

while True:
    byte = my_read(port)

    if byte:
        last_received_time = time.time()
        decoded_byte = byte.decode('ascii', errors='ignore') 

        if byte == b'\x05':
            my_write(port, b'\x06')

        elif byte == b'\x0a':
            my_write(port, b'\x06')
            data_buffer += "\n"

        elif byte == b'\x04':
            my_write(port, b'\x06')  
            data_buffer += "\n" 

        else:
            data_buffer += decoded_byte

    else:
        if time.time() - last_received_time > idle_timeout and data_buffer:
            try:
                with open(get_filename(), 'w') as file:
                    file.write(data_buffer)
                print(f"Data saved to file: {get_filename()}")
            except Exception as e:
                print(f"Error writing to file: {e}")
            data_buffer = ""
