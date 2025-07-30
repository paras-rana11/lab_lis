import os
import logging
import time
from datetime import datetime, timedelta
import serial # type: ignore
import smtplib
import threading
import schedule
from email.message import EmailMessage

HOST_ADDRESS = '0.0.0.0'
HOST_PORT = 0000
CONNECTION_TYPE = 'Serial'
COM_PORT = 'COM3'
s = None
x = None

REPORT_FILE_PREFIX = ''
REPORT_FILE_PATH = 'C:\\ASTM\\root\\report_file\\'
os.makedirs(REPORT_FILE_PATH, exist_ok=True)

# log file path
LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_machine.log'
ERROR_LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_machine_error.log'
LOG_FILE_LIST = [LOG_FILE, ERROR_LOG_FILE]

# Email configuration
SUBJECT = ''
TO_EMAIL = ''
FROM_EMAIL = ''
PASSWORD = '' 


class MachineConnectionSerial:
    def __init__(self, com_port=None, machine_name=None):
        if com_port and machine_name:
            self.connection = None
            self.com_port = com_port
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
            self.connection = serial.Serial(port=self.com_port, baudrate=115200, timeout=1)
            self.is_connected = True
            print(f"Server Connected To {self.com_port}: {self.connection}")
            return self.connection
                
        except Exception as e:
            print(f"Failed to Connect {self.server_ip} : {self.server_port} ::- {e}")
            self.cleanup()
            return None, None

    def read(self):
        if not self.connection:
            raise Exception("Connection is not initialized. Call get_connection() first.")
        try:
            data = self.connection.read(1)
            return data
        except Exception as e:
            print(f"Error reading data: {e}")
            return b''
    
    def process_data(self, data):
        if data:
            return data.decode('utf-8')
        return ""
    
    def write(self, byte_data):
        if not self.connection:
            raise Exception("Connection is not initialized. Call get_connection() first.")
        try:
            self.connection.write(byte_data)
            print(f"Data sent: {byte_data}")
        except Exception as e:
            print(f"Error sending data: {e}")

    def cleanup(self):
        """Properly close both client and server sockets"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
            
        self.is_connected = False  # Reset connection status

    def close_connection(self):
        self.cleanup()

    def __del__(self):
        """Ensure cleanup on object destruction"""
        self.cleanup()

# Method for setup logging
def send_email(subject, body, to_email, from_email, password):
    try:
        # Create the email message
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg.set_content(body)

        # Connect to Gmail SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()  # Secure the connection
            smtp.login(from_email, password)
            smtp.send_message(msg)

        logger.info('Email sent successfully!')
        return True
    except Exception as e:
        logger.error(f'Failed to send email: {e}')
        return False
    
# Method for setup logging
def setup_loggers(log_file, error_log_file):
    '''Set up separate loggers for info and error.'''
    logger = logging.getLogger('app_logger')
    try:
        logger.setLevel(logging.DEBUG)  
        logger.handlers.clear()  

        # Info Handler
        info_handler = logging.FileHandler(log_file)
        info_handler.setLevel(logging.INFO)
        info_format = logging.Formatter('%(asctime)s - INFO - %(message)s')
        info_handler.setFormatter(info_format)

        # Error Handler
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_format = logging.Formatter('%(asctime)s - ERROR - %(message)s')
        error_handler.setFormatter(error_format)

        logger.addHandler(info_handler)
        logger.addHandler(error_handler)

        return logger
    except Exception as e:
        send_mail_or_logging('Exception in initialize logger', e)
        return logger

logger = setup_loggers(LOG_FILE, ERROR_LOG_FILE)
logger.info('Log file initialized.')
logger.error('This is an error log example.')

def send_mail_or_logging(error_message, error):
    logger.error(f'{error_message} : {error}')

    body = f"""
    Dear Team,

    This is an automated alert from the Laboratory Information System.

        --> {error_message} :: Below are the details of the incident:

        - Filename: cobas_c_311_2_by.py
        - Connetion Type: {CONNECTION_TYPE}
        - Serial Port: {COM_PORT}
        - Machine Name: {REPORT_FILE_PREFIX}
        - IP Address: {HOST_ADDRESS}
        - Port: {HOST_PORT}
        - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        - Error Details: {error}

    Best regards,  
    Laboratory Information System  
    [Healthray LAB]
    """

    is_send_mail = send_email(SUBJECT, body, TO_EMAIL, FROM_EMAIL, PASSWORD)
    if not is_send_mail:
        logger.error(f"Exception during sending mail")

def remove_old_logs_from_log_file(log_file_list):
    try:
        logger.info("Thread Start For Remove old Logs")
        while True:
            for file in log_file_list:
                with open(file, 'r') as f:
                    data = f.read()

                lines = data.split('\n')

                cutoff_date = datetime.now() - timedelta(days=10)
                final_line_list = []
                for line in lines:
                    line_date = line.split()
                    if len(line_date) > 1:
                        if line_date[0] > (str(cutoff_date)).split()[0]:
                            final_line_list.append(line)

                with open(file,'w') as f:
                    f.write('\n'.join(final_line_list))
            
            time.sleep(86400)
    except Exception as e:
        send_mail_or_logging('Error in remove old log', e)


# def get_filename():
#     try:
#       dt = datetime.datetime.now()
#       return REPORT_FILE_PATH + f'{REPORT_FILE_PREFIX}' + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")
#     except Exception as e:
#         error_message = 'Error in get_filename'
#         send_mail_or_logging(error_message, e)

# def get_port():
#     try:
#         port = serial.Serial(port=COM_PORT, baudrate=9600, timeout=1)
#         message = f"Connected To {port}"
#         send_mail_or_logging(message, e)
#         return port
#     except serial.SerialException as se:
#         error_message = 'Error in Connection'
#         send_mail_or_logging(error_message, se)

# def my_read(port):
#     try:
#         data = port.read(1)
#         return data
#     except Exception as e:
#         error_message = 'Error in Reading data from port'
#         send_mail_or_logging(error_message, e)

# def my_write(port, byte):
#     try:
#         port.write(byte)
#         # print(byte)
#     except Exception as e:
#         error_message = 'Error in writing data to port'
#         send_mail_or_logging(error_message, e)

def communicate_with_machine(connection):
    cur_file = None
    byte_array = []
    try:
        while True:
            try:
                if connection:
                    byte = connection.read()
                    if not byte:
                        pass
                    else:
                        byte_array.append(chr(ord(byte)))

                    if byte == b'\x05':
                        byte_array = [chr(ord(byte))]
                        connection.write(b'\x06')
                        cur_file = connection.get_filename()
                        try:
                            x = open(cur_file, 'w')
                            x.write(''.join(byte_array))
                        except IOError as e:
                            error_message = 'Error in txt file initialize'
                            send_mail_or_logging(error_message, e)

                    elif byte == b'\x0a':
                        connection.write(b'\x06')
                        try:
                            x.write(''.join(byte_array))
                            byte_array = []
                        except Exception as e:
                            error_message = 'Error in writing data in file'
                            send_mail_or_logging(error_message, e)

                    elif byte == b'\x04':
                        try:    
                            if x:
                                x.write(''.join(byte_array))
                                x.close()
                                logger.info(f'File closed :- {cur_file}')
                        except Exception as e:
                            error_message = 'Error in writing data in file'
                            send_mail_or_logging(error_message, e)
                        byte_array = []
                else:
                    time.sleep(10)
            except Exception as e:
                error_message = 'Error in main loop'
                send_mail_or_logging(error_message, e)
    except Exception as e:
        error_message = 'Error in main loop'
        send_mail_or_logging(error_message, e)

    finally:
        logger.info("Closing connection...")
        if connection:
            connection.close_connection()

# Try to establish connection
try:
    CONNECTION_MACHINE_OBJECT = MachineConnectionSerial(
        com_port=COM_PORT,
        machine_name=REPORT_FILE_PREFIX
    )

    connection_object = CONNECTION_MACHINE_OBJECT.get_connection()
    logger.info(f"Connection established on port: {connection_object}")

except Exception as e:
    error_message = 'Failed to establish machine connection'
    send_mail_or_logging(error_message, e)


# Start the processes
if __name__ == '__main__':
    try:
        threading.Thread(target=remove_old_logs_from_log_file, args=(LOG_FILE_LIST,), daemon=True).start()

        communicate_with_machine(CONNECTION_MACHINE_OBJECT)

        while True:

            if not CONNECTION_MACHINE_OBJECT.is_connected:
                try:
                    connection_object= CONNECTION_MACHINE_OBJECT.get_connection()
                    logger.info(f"Connection established on port: {connection_object}")
                except Exception as e:
                    error_message = 'Failed to establish machine connection'
                    send_mail_or_logging(error_message, e)

                communicate_with_machine(CONNECTION_MACHINE_OBJECT)

            else:
                communicate_with_machine(CONNECTION_MACHINE_OBJECT)

            time.sleep(5)


    except Exception as e:
        error_message = 'Error in main function'
        send_mail_or_logging(error_message, e)