##############################################################################
# pip install pyserial

# 'serial'
# ASTM Protocol
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
import serial # type: ignore

connection_type = 'tty'
input_tty = 'COM6'
s = None
x = None
logfile_name = 'C:\\ASTM\\var\\log\\access2.in.log'
log = 1
output_folder = 'C:\\ASTM\\root\\access2.data\\'
alarm_time = 10

logging.basicConfig(filename=logfile_name, level=logging.DEBUG)
def signal_handler(signal, frame):
    global x
    global byte_array
    try:
        if x:
            x.write(''.join(byte_array))
            x.close()
    except Exception as e:
        logging.exception("Error while handling signal: {}".format(e))
    byte_array = []
    logging.warning('Alarm: <EOT> NOT received. Data may be incomplete.')

def get_filename():
    dt = datetime.datetime.now()
    return output_folder + 'au_480_' + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")

def get_port():
    try:
        port = serial.Serial(port=input_tty, baudrate=9600, timeout=1)
        logging.info(f"Serial port {input_tty} opened successfully")
        print(f"Serial port {input_tty} opened successfully")
        return port
    except serial.SerialException as se:
        logging.exception(f"Error opening serial port: {se}")
        sys.exit(1)

def my_read(port):
    data = port.read(1)
    logging.debug(f"Received: {data}")
    print(f"Received: {data}")
    return data

def my_write(port, byte):
    port.write(byte)
    logging.debug(f"ACK Sent:  {byte}")
    print(f"ACK Sent: {byte}")

if log == 0:
    logging.disable(logging.CRITICAL)

signal.signal(signal.SIGBREAK, signal_handler)
port = get_port()
print(f"Connected to port: {port}")
logging.info(f"Connected to port: {port}")

byte_array = []
while True:
    byte = my_read(port)
    if not byte:
        logging.warning('<EOF> reached. Connection broken')
        print("Empty Bit Receiving!")
    else:
        byte_array.append(chr(ord(byte)))
        logging.debug(f"Received byte: {ord(byte)}")
        print(f"Received byte: {byte} = {ord(byte)}")

    if byte == b'\x05':
        byte_array = [chr(ord(byte))]
        my_write(port, b'\x06')
        cur_file = get_filename()
        try:
            x = open(cur_file, 'w')
            x.write(''.join(byte_array))
            logging.info(f'<ENQ> received. <ACK> Sent. File opened: {cur_file}')
        except IOError as ioe:
            logging.exception(f"Error opening file {cur_file}: {ioe}")

    elif byte == b'\x0a':
        my_write(port, b'\x06')
        try:
            x.write(''.join(byte_array))
            byte_array = []
            logging.info('<LF> received. <ACK> Sent. Data written to file.')
        except Exception as e:
            logging.exception(f"Error writing to file: {e}")

    elif byte == b'\x04':
        try:    
            if x:
                x.write(''.join(byte_array))
                x.close()
                logging.info('File closed.')
                print('File closed')
        except Exception as e:
            logging.exception(f"Error closing file: {e}")
        byte_array = []
        logging.info('<EOT> received. File written and closed.')


