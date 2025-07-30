import sys
import logging
import signal
import datetime
import socket

connection_type = 'tcp'
HOST = '127.0.0.1'
PORT = 5000 
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
    return output_folder + 'access_2_' + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")

def get_socket():
    try:
         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            logging.info(f"Server listening on {HOST}:{PORT}")
            print(f"Server listening on {HOST}:{PORT}")
            return s
    except socket.error as se:
        logging.exception(f"Error connecting to TCP server: {se}")
        sys.exit(1)

def my_read(sock):
    data = sock.recv(1)
    logging.debug(f"Received: {data}")
    print(f"Received: {data}")
    return data

def my_write(sock, byte):
    sock.sendall(byte)
    logging.debug(f"ACK Sent:  {byte}")
    print(f"ACK Sent: {byte}")

def send_enq(sock):
    enq = b'\x05'
    my_write(sock, enq)
    logging.info('ENQ Sent')
    print('ENQ Sent')

if log == 0:
    logging.disable(logging.CRITICAL)

signal.signal(signal.SIGINT, signal_handler)
sock = get_socket()
conn, addr = sock.accept()
print(f"Connected to socket: {conn}")
logging.info(f"Connected to socket: {conn}")

# Send ENQ to the machine
send_enq(conn)

byte_array = []
while True:
    byte = my_read(conn)
    if not byte:
        logging.warning('<EOF> reached. Connection broken')
        print("Empty Bit Receiving!")
    else:
        byte_array.append(chr(ord(byte)))
        logging.debug(f"Received byte: {ord(byte)}")
        print(f"Received byte: {byte} = {ord(byte)}")

    if byte == b'\x05':
        byte_array = [chr(ord(byte))]
        my_write(sock, b'\x06')
        cur_file = get_filename()
        try:
            x = open(cur_file, 'w')
            x.write(''.join(byte_array))
            logging.info(f'<ENQ> received. <ACK> Sent. File opened: {cur_file}')
        except IOError as ioe:
            logging.exception(f"Error opening file {cur_file}: {ioe}")

    elif byte == b'\x0a':
        my_write(sock, b'\x06')
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
