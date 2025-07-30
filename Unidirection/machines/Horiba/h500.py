#!/usr/bin/python3
import sys

connection_type='tcp'
host_address='10.1.55.147'
host_port='8000'

s = None
x = None
log = 1
output_folder = 'C:\\ASTM\\root\\access2.data\\'
alarm_time = 10

#import other modules
try:
  import signal
  import datetime
  import time
except ModuleNotFoundError:
  exception_return = sys.exc_info()
  quit()

#import serial or socket
if(connection_type == 'tty'):
  try:
    import serial
  except ModuleNotFoundError:
    exception_return = sys.exc_info()
    quit()
elif(connection_type == 'tcp'):
  try:
    import socket
  except ModuleNotFoundError:
    exception_return = sys.exc_info()
    quit()

  byte_array = []

def get_filename():
  dt = datetime.datetime.now()
  return output_folder + "h500_" + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")

def get_port():
  if(connection_type == 'tty'):
    try:
      port = serial.Serial(input_tty, baudrate=9600)
      return port
    except:
      exception_return = sys.exc_info()
      quit()

  elif(connection_type == 'tcp'):
    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    """Set TCP keepalive on an open socket.
    It activates after 1 second (after_idle_sec) of idleness,
    then sends a keepalive ping once every 3 seconds (interval_sec),
    and closes the connection after 5 failed ping (max_fails), or 15 seconds
    """
    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

    try:
      s.bind((host_address, int(host_port)))  # it is a tuple
    except:
      exception_return = sys.exc_info()
      quit()
    s.listen(1)

    # Initialize conn_tuple here to avoid the NameError
    conn_tuple = s.accept()
    
    return conn_tuple[0]

def my_read(port):
  if(connection_type == 'tty'):
    return port.read(1)
  elif(connection_type == 'tcp'):
    try:
      return port.recv(1)
    except Exception as my_ex:
      print('Network disconnection??')
      return b''

def my_write(port, byte):
  if(connection_type == 'tty'):
    return port.write(byte)
  elif(connection_type == 'tcp'):
    return port.send(byte)

#main loop##########################

port = get_port()
byte_array = []
while True:
  byte = my_read(port)
  if(byte == b''):
    print('<EOF> reached. Connection broken: details below')

    if(connection_type == 'tcp'):
      conn_tuple = s.accept()
      port = conn_tuple[0]

  else:
    byte_array = byte_array + [chr(ord(byte))]

  if(byte == b'\x05'):
    byte_array = []
    byte_array = byte_array + [chr(ord(byte))]
    my_write(port, b'\x06')
    cur_file = get_filename()
    x = open(cur_file, 'w')

  elif(byte == b'\x0a'):
    my_write(port, b'\x06')
    try:
      x.write(''.join(byte_array))
      byte_array = []
    except Exception as my_ex:
      print(my_ex)

  elif(byte == b'\x04'):

    try:
      if x is not None:
        x.write(''.join(byte_array))
        x.close()

    except Exception as my_ex:
      print(my_ex)

    byte_array = []
