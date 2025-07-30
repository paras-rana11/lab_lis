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

import hashlib
import sys
import logging
import signal
import datetime
import uuid
import hashlib
import serial

# Configuration
connection_type = 'tty'
input_tty = 'COM17'
s = None
x = None
log = 1
logfile_name = 'C:\\ASTM\\var\\log\\access2.in.log'
output_folder = 'C:\\ASTM\\root\\access2.data\\'

# stored_license_key = "34ad7747ef4f423ca6234c0a6de73eedff591ea67235ae8e84486a90ae731b56"
#
# def get_mac_address():
#     mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
#     return ":".join([mac[e:e+2] for e in range(0, 11, 2)])
#
# def generate_license_key(mac_address):
#     key = hashlib.sha256(mac_address.encode()).hexdigest()
#     return key
#
# def check_license(license_key, mac_address):
#     generated_key = generate_license_key(mac_address)
#     return generated_key == license_key
#
# # License check
# current_mac = get_mac_address()
# if not check_license(stored_license_key, current_mac):
#     print("Invalid license. This executable can only run on the registered system.")
#     logging.error("Invalid license. This executable can only run on the registered system.")
#     sys.exit(1)

# Configure logging
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


def get_filename(extension="txt"):
    dt = datetime.datetime.now()
    return output_folder + "c_111_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f") + f".{extension}"


def get_port():
    try:
        port = serial.Serial(port=input_tty, baudrate=9600, timeout=10, xonxoff=True, rtscts=True
                             , dsrdtr=True)
        logging.info(f"Serial port {input_tty} opened successfully")
        print(f"Serial port {input_tty} opened successfully")
        return port
    except serial.SerialException as se:
        logging.exception(f"Error opening serial port: {se}")
        sys.exit(1)


def my_read(port):
    # data = port.readline()
    data = port.read(1)
    # data = b'\x05'
    logging.debug(f"Received: {data}")
    print(f"Received: {data}")
    return data


def my_write(port, byte):
    port.write(byte)
    logging.debug(f"ACK Sent:  {byte}")
    print(f"ACK Sent: {byte}")

# Disable logging if not required
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
        print(byte_array)
        logging.debug(f"Received byte: {ord(byte)}")
        print(f"Received byte: {byte} = {ord(byte)}")

    if byte == b'\x05':
        # signal.alarm(0)
        print("byte == b'\x05'")
        byte_array = [chr(ord(byte))]
        my_write(port, b'\x06')
        cur_file = get_filename()
        try:
            x = open(cur_file, 'w')
            x.write(''.join(byte_array))
            logging.info(f'<ENQ> received. <ACK> Sent. File opened: {cur_file}')
            # signal.alarm(alarm_time)
        except IOError as ioe:
            logging.exception(f"Error opening file {cur_file}: {ioe}")

    elif byte == b'\x0a':
        # signal.alarm(0)
        my_write(port, b'\x06')
        try:
            x.write(''.join(byte_array))
            byte_array = []
            logging.info('<LF> received. <ACK> Sent. Data written to file.')
            # signal.alarm(alarm_time)
        except Exception as e:
            logging.exception(f"Error writing to file: {e}")

    elif byte == b'\x04':
        # signal.alarm(0)
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
