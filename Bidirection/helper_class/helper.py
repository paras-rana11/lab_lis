import sys
import datetime
import serial  # type: ignore
import mysql.connector
import socket




REPORT_FILE_PATH = 'C:\\ASTM\\root\\report_file\\'
CASE_FILE_PATH = 'C:\\ASTM\\root\\case_file\\'
LOG_FILE_PATH = 'C:\\ASTM\\root\\log_file\\'


class MachineConnectionSerial:
    def __init__(self, connection_type: str, input_tty: str, machine_name: str):
        self.connection_type = connection_type
        self.input_tty = input_tty
        self.machine_name = machine_name
        self.port = None

    def get_filename(self):
        dt = datetime.datetime.now()
        return REPORT_FILE_PATH + self.machine_name + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")

    def get_port(self):
        try:
            self.port = serial.Serial(port=self.input_tty, baudrate=9600, timeout=1)
            print(f"Serial port {self.input_tty} opened successfully")
            return self.port, CASE_FILE_PATH
        except serial.SerialException as se:
            print(f"Failed to open serial port {self.input_tty}: {se}")
            sys.exit(1)

    def read(self):
        if not self.port:
            raise Exception("Port is not initialized. Call get_port() first.")
        data = self.port.read(1)
        # print(f"Received: {data}")
        return data

    def write(self, byte):
        if not self.port:
            raise Exception("Port is not initialized. Call get_port() first.")
        self.port.write(byte)
        print(f"Query Sent: {byte}")

class MachineConnectionTcp:
    def __init__(self, server_ip=None, server_port=None, machine_name=None):
        if server_ip and server_port and machine_name:
            self.connection = None
            self.server_socket = None  
            self.server_ip = server_ip
            self.server_port = server_port
            self.machine_name = machine_name
            self.is_connected = False 

    def get_filename(self):
        dt = datetime.now()
        return REPORT_FILE_PATH + f"{self.machine_name}_{dt.strftime('%Y-%m-%d-%H-%M-%S-%f')}.txt"

    def get_connection(self):
        if self.is_connected and self.connection:
            print("Using existing connection")
            return self.connection
            
        try:            
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.server_socket.bind((self.server_ip, self.server_port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(30.0) 
            
            # Accept connection
            self.connection, addr = self.server_socket.accept()
            self.connection.settimeout(1.0)
            self.is_connected = True
            print(f"Server Connected To {self.server_ip}:{self.server_port} : {self.connection}")
            
            return self.connection
                
        except Exception as e:
            print(f"Failed to Connect {self.server_ip} : {self.server_port} ::- {e}")
            self.cleanup()
            return None, None

    def read(self):
        if not self.connection:
            raise Exception("Connection is not initialized. Call get_connection() first.")
        try:
            data = self.connection.recv(1)
            return data
        except socket.timeout:
            return b''  # Return empty bytes on timeout
        except Exception as e:
            print(f"Error reading data: {e}")
            return b''
    
    def recv(self, buffer_size=1):
        """Alternative method name for consistency"""
        return self.read() if buffer_size == 1 else self.connection.recv(buffer_size)
    
    def process_data(self, data):
        if data:
            return data.decode('utf-8')
        return ""
    
    def write(self, byte_data):
        if not self.connection:
            raise Exception("Connection is not initialized. Call get_connection() first.")
        try:
            self.connection.sendall(byte_data)
            print(f"Data sent: {byte_data}")
        except Exception as e:
            print(f"Error sending data: {e}")

    def sendall(self, byte_data):
        """Alternative method name for consistency"""
        self.write(byte_data)

    def cleanup(self):
        """Properly close both client and server sockets"""
        if self.connection:
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
            except:
                pass
            self.connection = None
            
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        self.is_connected = False  # Reset connection status

    def close_connection(self):
        self.cleanup()

    def __del__(self):
        """Ensure cleanup on object destruction"""
        self.cleanup()

class GenerateChecksum:
    def __init__(self):
        # Initialize ASTM Protocol Constants
        self.STX = chr(0x02)  # Start of text
        self.ETX = chr(0x03)  # End of text
        self.EOT = chr(0x04)  # End of transmission
        self.ENQ = chr(0x05)  # Enquiry
        self.ACK = chr(0x06)  # Acknowledge
        self.NAK = chr(0x15)  # Negative Acknowledge
        self.CR = chr(0x0D)   # Carriage Return
        self.LF = chr(0x0A)   # Line Feed

    def get_checksum_value(self, frame: str) -> str:
        """
        Reads checksum of an ASTM frame. Calculates characters after STX,
        up to and including the ETX or ETB.
        """
        sum_of_chars = 0
        complete = False

        # Loop through each character in the frame to calculate checksum
        for char in frame:
            byte_val = ord(char)

            if byte_val == 2:
                sum_of_chars = 0  
            elif byte_val in {3, 23}:
                sum_of_chars += byte_val
                complete = True
                break
            else:
                sum_of_chars += byte_val

        # Return the checksum if complete and valid
        if complete and sum_of_chars > 0:
            checksum = hex(sum_of_chars % 256)[2:].upper()  
            return checksum.zfill(2)  
        return "00" 

class ConnectionDb:
    def __init__(self , host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def connect_db(self):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if conn:
                print("*******************************************")
                print("***********  DATABASE CONNECTED ***********")
                print("*******************************************")
                return conn
            else:
                return "Connectiona Not Established"
        except Exception as e:
            print(f"Connection Error : {e}")