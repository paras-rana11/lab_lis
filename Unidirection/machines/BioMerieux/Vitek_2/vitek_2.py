from datetime import datetime, timedelta
import logging
import serial # type: ignore
import time
import smtplib
from email.message import EmailMessage

connection_type = 'tty'
input_tty = 'COM1'
s = None
x = None
output_folder = 'C:\\ASTM\\root\\report_file\\'

log_file = 'C:\\ASTM\\root\\log_file\\logging_for_vitek.log'
error_log_file = 'C:\\ASTM\\root\\log_file\\logging_for_vitek_error.log'
log_file_list = [log_file, error_log_file]

log_check_interval = 86400  # 24 hours (in seconds)

subject = ""
to_email = ""
from_email = ""
password = "" 

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

    logger.info("Email sent successfully!")

  except Exception as e:
    logger.error(f"Failed to send email: {e}")

def setup_loggers():
    """Set up separate loggers for info and error."""
    try:
        logger = logging.getLogger("app_logger")
        logger.setLevel(logging.DEBUG)  # capture everything, filter in handlers
        logger.handlers.clear()  # avoid duplicate logs on reload

        # Info Handler
        info_handler = logging.FileHandler(log_file)
        info_handler.setLevel(logging.INFO)
        info_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        info_handler.setFormatter(info_format)

        # Error Handler
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        error_handler.setFormatter(error_format)

        logger.addHandler(info_handler)
        logger.addHandler(error_handler)

        return logger
    except Exception as e:
        print(f"Error in log file initialization :- {e}")
        body_for_db = f' ********************** Error in log file initialization ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

logger = setup_loggers()
logger.info("Log file initialized.")
logger.error("This is an error log example.")

def remove_old_logs_from_log_file(log_file_list):
    try:
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

                with open('rag.txt','w') as f:
                    f.write('\n'.join(final_line_list))
            
            time.sleep(86400)
    except Exception as e:
        logger.error(f"Exception in delete old log :- {e}")
        body_for_db = f' ********************** Exception in delete old log ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

def get_filename():
    try:
        dt = datetime.now()
        return output_folder + 'vitek_' + dt.strftime("%Y-%m-%d-%H-%M-%S-%f")
    
    except Exception as e:
        logger.error(f"Exception in create new txt file :- {e}")
        body_for_db = f' ********************** Exception in create new txt file ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

def get_port():
    try:
        port = serial.Serial(port=input_tty, baudrate=9600, timeout=1)
        return port
    except serial.SerialException as e:
        logger.error(f"Exception during connection :- {e}")
        body_for_db = f' ********************** Exception during connection ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

def my_read(port):
    try:
        data = port.read(1)
        return data
    
    except Exception as e:
        logger.error(f"Exception during reading data :- {e}")
        body_for_db = f' ********************** Exception during reading data ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

def my_write(port, byte):
    try:
        port.write(byte)
    except Exception as e:
        logger.error(f"Exception during writing data :- {e}")
        body_for_db = f' ********************** Exception during writing data ********************** \n {e}'
        send_email(subject, body_for_db, to_email, from_email, password)

port = get_port()

byte_array = []
try:
    while True:
        if port:
            byte = my_read(port)
            if not byte:
                pass
            else:
                byte_array.append(chr(ord(byte)))
            
            if byte == b'\x05':
                byte_array = [chr(ord(byte))]
                my_write(port, b'\x06')
                cur_file = get_filename()
                try:
                    x = open(cur_file, 'w')
                    x.write(''.join(byte_array))
                except Exception as e:
                    logger.error(f"Exception during create new file ENQ :- {e}")
                    body_for_db = f' ********************** Exception during create new file ENQ ********************** \n {e}'
                    send_email(subject, body_for_db, to_email, from_email, password)

            elif byte == b'\x0a':
                my_write(port, b'\x06')
                try:
                    x.write(''.join(byte_array))
                    byte_array = []
                except Exception as e:
                    logger.error(f"Exception during create new file LF :- {e}")
                    body_for_db = f' ********************** Exception during create new file LF ********************** \n {e}'
                    send_email(subject, body_for_db, to_email, from_email, password)

            elif byte == b'\x04':
                try:    
                    if x:
                        x.write(''.join(byte_array))
                        x.close()

                except Exception as e:
                    logger.error(f"Exception during create new file EOT :- {e}")
                    body_for_db = f' ********************** Exception during create new file EOT ********************** \n {e}'
                    send_email(subject, body_for_db, to_email, from_email, password)
                byte_array = []
        else:
            port = get_port()

except Exception as e:
    logger.error(f"Exception during main loop :- {e}")
    body_for_db = f' ********************** Exception during main loop ********************** \n {e}'
    send_email(subject, body_for_db, to_email, from_email, password)
