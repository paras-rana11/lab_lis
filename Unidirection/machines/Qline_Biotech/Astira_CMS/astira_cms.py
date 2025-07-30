import sys

connection_type = 'tcp'
host_address = '192.168.31.33'
host_port = '5150'

s = None
x = None
log = 1
output_folder = 'C:\\ASTM\\root\\report_file\\'
alarm_time = 10

try:
    import signal
    import datetime
    import time
except ModuleNotFoundError:
    exception_return = sys.exc_info()
    quit()

if connection_type == 'tty':
    try:
        import serial
    except ModuleNotFoundError:
        exception_return = sys.exc_info()
        quit()
elif connection_type == 'tcp':
    try:
        import socket
    except ModuleNotFoundError:
        exception_return = sys.exc_info()
        quit()

byte_array = []

def get_filename():
    dt = datetime.datetime.now()
    return output_folder + "qline_biotech_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")

def get_port():
    if connection_type == 'tty':
        try:
            port = serial.Serial(input_tty, baudrate=9600)
            return port
        except:
            exception_return = sys.exc_info()
            quit()
    elif connection_type == 'tcp':
        global s
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

        try:
            s.bind((host_address, int(host_port)))
        except:
            exception_return = sys.exc_info()
            quit()
        s.listen(1)
        conn_tuple = s.accept()
        return conn_tuple[0]

def my_read(port):
    if connection_type == 'tty':
        return port.read(1)
    elif connection_type == 'tcp':
        try:
            return port.recv(1)
        except Exception as my_ex:
            return b''

def my_write(port, byte):
    if connection_type == 'tty':
        return port.write(byte)
    elif connection_type == 'tcp':
        return port.send(byte)

port = get_port()
byte_array = []

while True:
    byte = my_read(port)

    if byte == b'':
        if connection_type == 'tcp':
            conn_tuple = s.accept()
            port = conn_tuple[0]

    elif byte == b'\x0b':
        # Start-of-data marker: explicitly open a new file.
        byte_array = []
        cur_file = get_filename()
        try:
            x = open(cur_file, 'w')
            print(f"Opened new file: {cur_file}")
        except Exception as ex:
            x = None

    elif byte == b'\r':
        try:
            line = ''.join(byte_array).replace(' ', '')
            if x is not None:
                x.write(line + '\n')
            else:
                print("No open file to write line; skipping.")
            byte_array = []
        except Exception as ex:
            pass

    elif byte == b'\x1c':
        try:
            if x is not None:
                line = ''.join(byte_array).replace(' ', '')
                if line:
                    x.write(line)
                x.close()
                print("File closed")
                x = None
            else:
                print("No open file to close.")
        except Exception as ex:
            pass
        byte_array = []

    else:
        # Process regular data bytes
        # Removed auto-open logic here; we assume data is only saved between b'\x0b' and b'\x1c'
        if byte == b'\x00':
            continue
        if byte not in [b' ', b'\t', b'\n']:
            try:
                # This conversion assumes the byte is valid ASCII. You might need to adjust it based on your data.
                byte_array.append(byte.decode('ascii'))
            except Exception:
                # If decoding fails, skip the byte
                continue
