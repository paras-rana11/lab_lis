import os
import logging
import time
from datetime import datetime, timedelta
import serial # type: ignore
import smtplib
import threading
from email.message import EmailMessage
 
CONNECTION_TYPE = 'Serial'
COM_PORT = 'COM3'
FILE_NAME_PREFIX = 'hemax_33'
 
OUTPUT_FOLDER = 'C:\\ASTM\\root\\report_file\\'
LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_hemax_33_info.log'
ERROR_LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_hemax_33_error.log'
LOG_FILE_LIST = [LOG_FILE, ERROR_LOG_FILE]
 
SUBJECT = "Email From BioSystem"
TO_EMAIL = "lishealthray@gmail.com"
FROM_EMAIL = "lishealthray@gmail.com"
PASSWORD = "rxbr zlzy tpin pgur"  
 
class MachineConnectionSerial:
    def __init__(self, com_port=None, machine_name=None):
        if com_port and machine_name:
            self.connection = None
            self.com_port = com_port
            self.machine_name = machine_name
            self.is_connected = False
 
    def get_filename(self):
        dt = datetime.now()
        return OUTPUT_FOLDER + f"{self.machine_name}_{dt.strftime('%Y-%m-%d-%H-%M-%S-%f')}.txt"
 
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
        error_message = 'Exception in initialize logger'
        send_mail_or_logging(error_message, e)
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
 
        - Filename: hemax_33.py (Alakahia)
        - Connetion Type: {CONNECTION_TYPE}
        - Port: {COM_PORT}
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
        error_message = 'Error in remove old log'
        send_mail_or_logging(error_message, e)
 
def communicate_with_machine(port):
    x = None
    cur_file = None
    byte_array = []
 
    try:
        while True:
            try:
                if port:
                    byte = port.read()
 
                    if not byte:
                        pass
                    else:
                        try:
                            decoded_char = byte.decode('ascii', errors='ignore')
                            byte_array.append(decoded_char)
                        except:
                            pass
 
                    if byte_array and not byte:
                        cur_file = port.get_filename()
                        try:
                            x = open(cur_file, 'w')
                            x.write(''.join(byte_array))
                            x.close()
                            logger.info(f"file closed {cur_file}")
                            byte_array = []
                            cur_file = None
                        except IOError as ioe:
                            error_message = 'Error in txt file initialize'
                            send_mail_or_logging(error_message, e)
                else:
                    break
 
            except Exception as e:
                error_message = 'Error in main loop'
                send_mail_or_logging(error_message, e)
    except Exception as e:
        error_message = 'Error in main loop'
        send_mail_or_logging(error_message, e)
 
    finally:
        logger.info("Closing connection...")
        if port:
            port.close_connection()
 
 
# Try to establish connection
try:
    CONNECTION_HEMAX_OBJECT = MachineConnectionSerial(
        com_port=COM_PORT,
        machine_name=FILE_NAME_PREFIX
    )
 
    connection_emax = CONNECTION_HEMAX_OBJECT.get_connection()
    logger.info(f"Connection established on port: {connection_emax}")
 
except Exception as e:
    error_message = 'Failed to establish machine connection'
    send_mail_or_logging(error_message, e)
 
 
# Start the processes
if __name__ == '__main__':
    try:
        threading.Thread(target=remove_old_logs_from_log_file, args=(LOG_FILE_LIST,), daemon=True).start()
 
        communicate_with_machine(CONNECTION_HEMAX_OBJECT)
 
        while True:
 
            if not CONNECTION_HEMAX_OBJECT.is_connected:
                try:
                    connection_emax= CONNECTION_HEMAX_OBJECT.get_connection()
                    logger.info(f"Connection established on port: {connection_emax}")
                except Exception as e:
                    error_message = 'Failed to establish machine connection'
                    send_mail_or_logging(error_message, e)
 
                communicate_with_machine(CONNECTION_HEMAX_OBJECT)
 
            else:
                communicate_with_machine(CONNECTION_HEMAX_OBJECT)
 
            time.sleep(5)
 
 
    except Exception as e:
        error_message = 'Error in main function'
        send_mail_or_logging(error_message, e)