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
import datetime
import serial # type: ignore

connection_type = 'tty'
input_tty = 'COM6'
s = None
x = None
output_folder = 'C:\\ASTM\\root\\access2.data\\'
alarm_time = 10


def get_filename():
    dt = datetime.datetime.now()
    return output_folder + 'aia_360_' + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")

def get_port():
    try:
        port = serial.Serial(port=input_tty, baudrate=9600, timeout=1)
        print(f"Serial port {input_tty} opened successfully")
        return port
    except serial.SerialException as se:
        sys.exit(1)

def my_read(port):
    data = port.read(1)
    print(f"Received: {data}")
    return data

def my_write(port, byte):
    port.write(byte)
    print(f"ACK Sent: {byte}")

port = get_port()
print(f"Connected to port: {port}")

byte_array = []
while True:
    byte = my_read(port)
    if not byte:
        print("Empty Bit Receiving!")
    else:
        byte_array.append(chr(ord(byte)))
        print(f"Received byte: {byte} = {ord(byte)}")

    if byte == b'\x05':
        byte_array = [chr(ord(byte))]
        my_write(port, b'\x06')
        cur_file = get_filename()
        try:
            x = open(cur_file, 'w')
            x.write(''.join(byte_array))
        except IOError as ioe:
            print(f"Error opening file {cur_file}: {ioe}")

    elif byte == b'\x0a':
        my_write(port, b'\x06')
        try:
            x.write(''.join(byte_array))
            byte_array = []
        except Exception as e:
            print(f"Error writing to file: {e}")

    elif byte == b'\x04':
        try:    
            if x:
                x.write(''.join(byte_array))
                x.close()
                print('File closed')
        except Exception as e:
            print(f"Error closing file: {e}")
        byte_array = []


