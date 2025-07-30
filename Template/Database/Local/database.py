# here is database file for save data in mysql
# here you only need to chage machine fucntions for extract data from txt file 


import json
import os
import re
import time
import pymysql
from datetime import datetime, timedelta
import ast
import logging
import smtplib
import threading
import shutil
from email.message import EmailMessage
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Mysql Configuration
MY_HOST = ''
MY_USER = ''
MY_PASS = ''
MY_DB = ''

# Report file path
REPORT_FILE_PATH = 'C:\\ASTM\\root\\report_file\\'
BACKUP_FILE_PATH = 'C:\\ASTM\\root\\backup_file\\'

# log file path
LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_database.log'
ERROR_LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_database_error.log'
LOG_FILE_LIST = [LOG_FILE, ERROR_LOG_FILE]

# Email configuration
SUBJECT = ''
TO_EMAIL = ''
FROM_EMAIL = ''
PASSWORD = '' 

# Google configuration
GOOGLE_SHEET_NAME = ''
GOOGLE_WORKSHEET_NAME_FOR_PATIENT_DATA = ''

CREADENTIAL = {
}

SCOPE = []

creds = ServiceAccountCredentials.from_json_keyfile_dict(CREADENTIAL, SCOPE)  # Load credentials
client = gspread.authorize(creds)  # Authorize client
sheet = client.open(GOOGLE_SHEET_NAME).worksheet(GOOGLE_WORKSHEET_NAME_FOR_PATIENT_DATA)  # Open the Google Sheet (by name or URL)
sheet.update(values=[['Status', 'Date', 'Machine_ID', 'Patient_ID', 'Test']], range_name='A1:E1')

# Method for setup logging
def setup_loggers(log_file, error_log_file):
    '''Set up separate loggers for info and error.'''
    logger = logging.getLogger('app_logger')
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

logger = setup_loggers(LOG_FILE, ERROR_LOG_FILE)
logger.info('Log file initialized.')
logger.error('This is an error log example.')

# Method for sending email and logging
def send_mail_or_logging(error_message, error):
    logger.error(f'{error_message} : {error}')

    body = f"""
    Dear Team,

    This is an automated alert from the Laboratory Information System.

        --> {error_message} :: Below are the details of the incident:

        - Filename: database.py
        - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        - Error Details: {error}

    Best regards,  
    Laboratory Information System  
    [Healthray LAB]
    """

    is_send_mail = send_email(SUBJECT, body, TO_EMAIL, FROM_EMAIL, PASSWORD)
    if not is_send_mail:
        logger.error(f"Exception during sending mail")

# Method for send email
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

# Method for reading txt file
def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        error_message = 'Error in reading file'
        send_mail_or_logging(error_message, e)
        return None

# Method for connection establish to mysql
def get_connection():
    try:
        con = pymysql.connect(
            host=MY_HOST,
            user=MY_USER,
            password=MY_PASS,
            database=MY_DB
        )
        return con
    except pymysql.MySQLError as e:
        error_message = 'Error in establish connection'
        send_mail_or_logging(error_message, e)
        return None

# Method for run query
def run_query(con, prepared_sql, data_tpl):
    try:
        with con.cursor() as cur:
            cur.execute(prepared_sql, data_tpl)
            con.commit()
            return cur
    except pymysql.MySQLError as e:
        error_message = 'Error in query'
        send_mail_or_logging(error_message, e)
        return None

# Method for close cursor
def close_cursor(cur):
    try:
        if cur:
            cur.close()
    except pymysql.MySQLError as e:
        error_message = 'Error in closing cursor'
        send_mail_or_logging(error_message, e)

# Method for close connection
def close_connection(con):
    try:
        if con:
            con.close()
    except pymysql.MySQLError as e:
        error_message = 'Error in closing connection'
        send_mail_or_logging(error_message, e)

# Method for save data in mysql 
def send_to_mysql(data):
    try:
        con = get_connection()
        if not con:
            return False
        prepared_sql = 'INSERT INTO machineData (machineName, patientId, test) VALUES (%s, %s, %s)'
        try:
            json_report_data = json.dumps(data[2]) if data[2] else json.dumps({})
            cur = run_query(con, prepared_sql, (data[0], data[1], json_report_data))
            if cur:
                close_cursor(cur)
        except Exception as e:
            error_message = 'Error in save in mysql'
            send_mail_or_logging(error_message, e)
            return False
        finally:
            close_connection(con)
        return True
    except Exception as e:
        error_message = 'Error in save in mysql'
        send_mail_or_logging(error_message, e)
        return False



# Method for extract data from particular Machine
# Here you can change according lab requirements means change below method according to machine,
# means if cell tak 6500 machine than this code is right but if cobas c 311 1 machine than change only this method.
def extract_report_data_cell_tak_6500(data):
    patients = []
    try:
      lines = data.split('\n')
      data_line = remove_starting_chars(lines)
      patientId = None
      machine_name = 'Database'
      result_dict = {}
      for line in data_line:
          
          if line.startswith('2P'):
              if patientId and result_dict:
                patients.append((machine_name, patientId, str(result_dict)))
              patientId = line.split('|')[4].split()[0]
              if '-' in patientId:
                  patientId = patientId.split('-')[0]
          elif re.match(r'^[0-7]R\|',line):
              test_name = line.split('|')[2].split('^')
              if len(test_name) > 4:
                  test_name = test_name[3].strip()
              else:
                  test_name = test_name[3].strip()
              test_result = line.split('|')[3]
              result_dict[test_name] = test_result
      if patientId and result_dict:
          patients.append((machine_name, patientId, str(result_dict)))
      # print(patients)
      return patients
    except Exception as e:
        error_message = 'Error in extract data from cell tak'
        send_mail_or_logging(error_message, e)
        return patients

# healper Function 
def remove_starting_chars(data):
    try:
      return [re.sub(r'^\x05|\x03|\x02', '', item) for item in data]
    except Exception as e:
        error_message = 'Error in healper function'
        send_mail_or_logging(error_message, e)
        return []

# Method for extract data from txt file and remove used txt file  
def extract_list_data_from_txt_file(folder_path, backup_path):
    file_path = None
    results = []
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            text_data = read_file(file_path)
            if not text_data:
                continue
            extractors = {
                'Database_':extract_report_data_cell_tak_6500
                
            }
            extractor = next((ext for prefix, ext in extractors.items() if filename.startswith(prefix)), None)
            if extractor:
                results.append(extractor(text_data))
                try:
                    shutil.copy2(file_path, backup_path)
                    os.remove(file_path)
                    file_path = None
                except Exception as e:
                    if 'The process cannot access the file because it is being used by another process' not in e :
                        error_message = 'Error in removing file'
                        send_mail_or_logging(error_message, e)
            else:
                try:
                    shutil.copy2(file_path, backup_path)
                    os.remove(file_path)
                    file_path = None
                except Exception as e:
                    if 'The process cannot access the file because it is being used by another process' not in e :
                        error_message = 'Error in removing file'
                        send_mail_or_logging(error_message, e)
        return results
    except Exception as e:
        error_message = 'Error in extract data from txt file'
        send_mail_or_logging(error_message, e)
        return results
    finally:
        try:
            if file_path:
                shutil.copy2(file_path, backup_path)
                os.remove(file_path)
                file_path = None
        except Exception as e:
            if 'The process cannot access the file because it is being used by another process' not in e :
                error_message = 'Error in removing file'
                send_mail_or_logging(error_message, e)

# Method for save data in mysql db
def send_data_to_mysql(results):
    case_no_list = []
    google_data_list = []
    try:
        flattened_list = [sub_list for item in results for sub_list in item]
        if isinstance(flattened_list, list):
            for result in flattened_list:
                result = list(result)
                google_data_list.append(result)
                data_dict = result[2]
                case_no = result[1]
                data_dict = ast.literal_eval(data_dict)
                result[2] = data_dict
                result = tuple(result)
                send_to_mysql(result)       
                case_no_list.append(case_no) 
        else:
            pass
        return case_no_list, google_data_list
    except Exception as e:
        error_message = 'Error in send data to mysql'
        send_mail_or_logging(error_message, e)
        return case_no_list, google_data_list

# Thread for remove old log 
threading.Thread(target=remove_old_logs_from_log_file, args=(LOG_FILE_LIST,), daemon=True).start()

# main loop
while True:
    try:
        all_results = extract_list_data_from_txt_file(REPORT_FILE_PATH, BACKUP_FILE_PATH)
        if all_results:
            case_no, google_data = send_data_to_mysql(all_results)
            logger.info(f'Data Save in MySQL For {case_no}')
            if google_data:
                for result_data in google_data:
                    result_data[2] = str(result_data[2])
                    result_data.insert(0, '200')
                    result_data.insert(1, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    sheet.append_row(result_data)   # Append data in google sheet

        time.sleep(8)
    except Exception as e:
        error_message = 'Error in main loop'
        send_mail_or_logging(error_message, e)
