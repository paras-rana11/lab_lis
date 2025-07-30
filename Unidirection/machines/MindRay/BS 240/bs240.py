##############################################################################
# pip install pyserial

# ASTM Protocol
# 'serial'
############################### For Create .exe ###############################
# pyinstaller --onefile get_data_from_machine_access_2.py
# update path in spec file

############################### After update spec file ########################
# pyinstaller get_data_from_machine_access_2.spec
###############################################################################


import sys
import logging
import signal
import datetime
import serial  # type: ignore
import os

connection_type = 'tty'
input_tty = 'COM5'
output_folder = 'C:\\ASTM\\root\\access2.data\\'

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)


def signal_handler(signal, frame):
    sys.exit(0)

def get_filename():
    dt = datetime.datetime.now()
    return os.path.join(output_folder, 'bs_240_' + dt.strftime("%Y-%m-%d-%H-%M-%S-%f") + '.txt')

def get_port():
    try:
        port = serial.Serial(port=input_tty, baudrate=9600, timeout=1)
        print(f"Serial port {input_tty} opened successfully")
        return port
    except serial.SerialException as se:
        sys.exit(1)

def my_read(port):
    data = port.read(1)
    return data

def my_write(port, byte):
    port.write(byte)


signal.signal(signal.SIGBREAK, signal_handler)
port = get_port()
print(f"Connected to port: {port}")

byte_array = []
cur_file = None

while True:
    byte = my_read(port)

    if not byte:
        print(f"Received:{byte}")
        print("Empty Bit Receiving!")
        continue

    byte_array.append(byte.decode('ascii', errors='ignore'))
    cur_file = get_filename()
    if byte == b'\x05':  # ENQ
        my_write(port, b'\x06')  # ACK for ENQ

    elif byte == b'\x0a':  # LF
        if cur_file is None:
            continue
        my_write(port, b'\x06')  # ACK for LF
        try:
            with open(cur_file, 'w') as x:
                x.write(''.join(byte_array))
                print('File closed')
            byte_array = []
            cur_file = None
        except Exception as e:
            pass

    elif byte == b'\x04':  # EOT
        if cur_file is None:
            continue
        try:
            with open(cur_file, 'a') as x:
                x.write(''.join(byte_array))
            print('File closed')
        except Exception as e:
            pass
        byte_array = []
        cur_file = None
