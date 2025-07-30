import os
import re
import ast
import jwt
import time
import json
import shutil
import pymysql
import logging
import smtplib
import threading
from datetime import datetime, timedelta
from email.message import EmailMessage
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

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

# CREADENTIAL = {
# }

# SCOPE = [
#     "https://spreadsheets.google.com/feeds",
#     "https://www.googleapis.com/auth/spreadsheets",
#     "https://www.googleapis.com/auth/drive"
# ]

# creds = ServiceAccountCredentials.from_json_keyfile_dict(CREADENTIAL, SCOPE)  # Load credentials
# client = gspread.authorize(creds)  # Authorize client
# sheet = client.open(GOOGLE_SHEET_NAME).worksheet(GOOGLE_WORKSHEET_NAME_FOR_PATIENT_DATA)  # Open the Google Sheet (by name or URL)
# sheet.update(values=[['Status', 'Date', 'Machine_ID', 'Patient_ID', 'Test']], range_name='A1:E1')

# Method for setup logging
def setup_loggers(log_file, error_log_file):
    '''Set up separate loggers for info and error.'''
    logger = logging.getLogger('app_logger')
    try:
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
        print(f"Error in initialize logger : {e}")
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

def remove_control_characters(text):
    try:
        block_number = 1
        while True:
            pattern = r"\x02" + str(block_number)
            if not re.search(pattern, text):
                break
            text = re.sub(pattern, "", text, count=1)
            block_number += 1

        # Step 2: Remove ENQ, ETX+1char, EOT, ETB+2char
        text = re.sub(r"\x05", "", text)   
        text = re.sub(r"\x03.", "", text)  
        text = re.sub(r"\x04", "", text)       
        text = re.sub(r"\x17..", "", text)  

        # Strip spaces from each line
        text = "\n".join(line.strip() for line in text.splitlines())
        return text
    except Exception as e:
        error_message = 'Error in remove control characters'
        send_mail_or_logging(error_message, e)
        return None

def merge_broken_lines(text):
    try:
        lines = text.splitlines()
        merged_lines = []
        fixed_lines = []

        for line in lines:
            line = line.strip()
            if merged_lines and not re.match(r'^[A-Z]\|\d+\|', line) and not re.match(r'^[HLPRCO]\|', line):
                merged_lines[-1] += line  # continuation of previous line
            else:
                merged_lines.append(line)

        for line in merged_lines:
            if re.match(r'^C\|1\|I\|.*R\|\d+\|', line):
                # Find the part where "R|n|" starts
                match = re.search(r'(R\|\d+\|)', line)
                if match:
                    split_index = match.start()
                    corrupted_c = line[:split_index]
                    fixed_r = line[split_index:]
                    fixed_lines.append(corrupted_c)
                    fixed_lines.append(fixed_r)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)    

        return fixed_lines

    except Exception as e:
        error_message = 'Error in merge broken line function'
        send_mail_or_logging(error_message, e)
        return []
    
def extract_report_data_mindray_bs_240(data):
    patients = [] 
    try:
        cleaned_data = remove_control_characters(data)

        # Step 2: Merge broken lines
        merged_lines = merge_broken_lines(cleaned_data)

        if merged_lines:
            machine_name = 'BS_240'
            
            patient_name = None
            report_data = {}

            for line in merged_lines:
                if line.startswith('O'):
                    if patient_name and report_data:
                        patients.append((machine_name, patient_name, str(report_data)))
                        report_data = {}
                        patient_name = None
                    patient_name = line.split('|')[3]
                    if '-' in patient_name:
                        patient_name = patient_name.split('-')[0]

                elif line.startswith('R'):
                    report_name = line.split('|')[2]
                    report_value = line.split('|')[3].replace('^', '').strip()
                    report_data[report_name] = report_value

            # Append the last patient's data after the loop
            if patient_name and report_data:
                patients.append((machine_name, patient_name, str(report_data)))

            return patients
    except Exception as e:
        error_message = 'Error in extract data from bs 240'
        send_mail_or_logging(error_message, e)
        return patients

def extract_report_data_mispa_nano(data):
    patients = [] 
    try:
        cleaned_data = remove_control_characters(data)

        # Step 2: Merge broken lines
        merged_lines = merge_broken_lines(cleaned_data)

        if merged_lines:
            machine_name = 'MISPA_NANO_PLUS'
            
            patient_name = None
            report_data = {}

            for line in merged_lines:
                if line.startswith('O'):
                    if patient_name and report_data:
                        patients.append((machine_name, patient_name, str(report_data)))
                        report_data = {}
                        patient_name = None
                    patient_name = line.split('|')[3]
                    if '-' in patient_name:
                        patient_name = patient_name.split('-')[0]

                elif line.startswith('R'):
                    report_name = line.split('|')[2]
                    report_value = line.split('|')[3].replace('^', '').strip()
                    report_data[report_name] = report_value

            # Append the last patient's data after the loop
            if patient_name and report_data:
                patients.append((machine_name, patient_name, str(report_data)))

            return patients
    except Exception as e:
        error_message = 'Error in extract data from mispa nano plus'
        send_mail_or_logging(error_message, e)
        return patients

def is_numeric(val):
    try:
        float(val)
        return True
    except ValueError:
        return False

def extract_report_data_from_cobas_machine(data, file_prefix):
    final_list = []
    try:
        machine_name = file_prefix.upper()
        pid_field = None  # Initialize with a default value
        result_dict = {}

        # Step 1: Clean control characters
        cleaned_data = remove_control_characters(data)

        # Step 2: Merge broken lines
        merged_lines = merge_broken_lines(cleaned_data)

        for line in merged_lines:
            if line.__contains__('O'):
                if pid_field and result_dict:
                    final_list.append((machine_name, pid_field, str(result_dict)))
                    result_dict = {}
                    pid_field = None

                pid_field = line.split("|")[2].strip()
                if '-' in pid_field:
                    pid_field = pid_field.split('-')[0].strip()
                if 'H' in pid_field or 'h' in pid_field or 'P' in pid_field or 'p' in pid_field:
                    pid_field = re.sub(r'[HhPp]', '', pid_field).strip()

            elif line.startswith('R') or line.startswith('V'):
                if '{' in line or '}' in line or 'o' in line or 'O' in line:
                    line = line.replace('{','|').replace('}','|').replace('o','/').replace('O','/')

                parts = line.split('|')
                if len(parts) >= 4:
                    test_id = parts[2].split('^')[-1].replace('/','').strip()
                    
                    if '\x02' in test_id:
                        test_id = test_id.split('\x02')[1]

                        if " " in test_id:
                            test_id = test_id.split()[1]

                    test_value = parts[3]
                    if '\x02' in test_value:
                        test_value = parts[3].split('\x02')[1]

                    if is_numeric(test_value):
                        result_dict[test_id] = test_value

        if pid_field and result_dict:
            final_list.append((machine_name, pid_field, str(result_dict)))

        return final_list
    except Exception as e:
        error_message = 'Error in extract data from c311'
        send_mail_or_logging(error_message, e)
        return final_list

def extract_report_data_e_411_1(data,file_prefix):
    final_list = []
    try:
        machine_name = file_prefix.upper()
        patient_id = None
        result_dict = {}
        # Step 1: Clean control characters
        cleaned_data = remove_control_characters(data)

        # Step 2: Merge broken lines
        merged_lines = merge_broken_lines(cleaned_data)

        for line in merged_lines:
            if line.startswith('O'):
                if patient_id and result_dict:
                    final_list.append((machine_name, patient_id, str(result_dict)))
                    patient_id = None
                    result_dict = {}

                patient_id = line.split('|')[2].strip()
                if '-' in patient_id:
                    patient_id = patient_id.split('-')[0].strip()

            elif line.startswith('R'):
                test_data = line.split('|')
                test_name = test_data[2].split('/')[0].replace('^^^','').strip()
                test_value = test_data[3]
                result_dict[test_name] = test_value

        if patient_id and result_dict:
            final_list.append((machine_name, patient_id, str(result_dict)))

        return final_list
    except Exception as e:
        error_message = 'Error in extract data from e411'
        send_mail_or_logging(error_message, e)
        return final_list

def extract_report_data_mispa_fab_120(data):
    try:
        lines = data.split('\n')
        patientId = None
        machine_name = "FAB_120"
        report_data = {}
        patients = []
        formatted_data = []
        
        obx_data = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith("OBX"):
                if obx_data:
                    formatted_data.append(obx_data.strip())
                obx_data = line
            elif obx_data and not line.startswith(("MSH", "OBR", "OBX", "PID", "ORC")):
                obx_data += line.strip()
            else:
                if obx_data:
                    formatted_data.append(obx_data.strip())
                    obx_data = ""
                formatted_data.append(line)

        if obx_data:
            formatted_data.append(obx_data.strip())
        for line in formatted_data:
            if line.startswith('OBR'):
                if patientId and report_data:
                    patients.append((machine_name, "D"+patientId, str(report_data)))
                    report_data = {}
                    patientId = None
                patientId = line.split('|')[3].replace('^MR', '').replace('^', '').strip()

            elif line.startswith('OBX'):
                if line.split('|')[2] == 'IS':
                    continue
                report_name = line.split('|')[3].strip()
                report_value = line.split('|')[5]
                report_data[report_name] = report_value

        if patientId and report_data:
            patients.append((machine_name, "D"+ patientId, str(report_data)))

        return patients
    except Exception as e:
        error_message = 'Error in extract data from agape mispa fab 120'
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
                'aggape_mispa_nano_plus_':extract_report_data_mispa_nano,
                'aggape_mispa_fab_120_': extract_report_data_mispa_fab_120,
                'mindray_bs_240_': extract_report_data_mindray_bs_240,
                'cobas_c_311_': extract_report_data_from_cobas_machine,
                'cobas_e_411_': extract_report_data_e_411_1

            }
            extractor = next((ext for prefix, ext in extractors.items() if filename.startswith(prefix)), None)
            if extractor:
                results.append(extractor(text_data))
                try:
                    shutil.copy2(file_path, backup_path)
                    os.remove(file_path)
                    file_path = None
                except Exception as e:
                    if 'The process cannot access the file because it is being used by another process' not in str(e):
                        error_message = 'Error in removing file'
                        send_mail_or_logging(error_message, e)
            else:
                try:
                    shutil.copy2(file_path, backup_path)
                    os.remove(file_path)
                    file_path = None
                except Exception as e:
                    if 'The process cannot access the file because it is being used by another process' not in str(e):
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
            if 'The process cannot access the file because it is being used by another process' not in str(e):
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
            # if google_data:
            #     for result_data in google_data:
            #         result_data[2] = str(result_data[2])
            #         result_data.insert(0, f'200')
            #         result_data.insert(1, f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
            #         sheet.append_row(result_data)   # Append data in google sheet

        time.sleep(8)
    except Exception as e:
        error_message = 'Error in main loop'
        send_mail_or_logging(error_message, e)
