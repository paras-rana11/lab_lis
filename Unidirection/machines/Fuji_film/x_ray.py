import os
import jwt
import time
import json
import boto3
import shutil
import zipfile
import smtplib
import logging
import requests
import threading
from pydicom import dcmread
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone

LAB_BRANCH_ID = None
JWT_SECRET_KEY = ''
API_URL = ""

CONNECTION_TYPE = 'TCP/IP'
MACHINE_NAME = 'Fuji Film X-Ray'
HOST_ADDRESS = '0.0.0.0'
HOST_PORT = 0000

LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_fuji_film_x_ray_info.log'
ERROR_LOG_FILE = 'C:\\ASTM\\root\\log_file\\logging_for_fuji_film_x_ray_error.log'
LOG_FILE_LIST = [LOG_FILE, ERROR_LOG_FILE]

SUBJECT = ""
TO_EMAIL = ""
FROM_EMAIL = ""
PASSWORD = "" 

CASE_FILE = 'C:\\DICOM\\root\\case_file\\fuji_film_x_ray.json'
backup_path = 'C:\\DICOM\\root\\backup\\'

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
    
# Method For Sending Email and Write Logs
def send_mail_or_logging(error_message, error):
    logger.error(f'{error_message} : {error}')

    body = f"""
    Dear Team,

    This is an automated alert from the Laboratory Information System.

        --> {error_message} :: Below are the details of the incident:

        - Filename: fuji_film_x_ray.py
        - Connetion Type: {CONNECTION_TYPE}
        - Machine Name: {MACHINE_NAME}
        - Machine Host Address: {HOST_ADDRESS}
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

# Method For Setup Logger
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

# Method For Remove old Logs Form Log File
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

# Method For Load JSON Data
def load_json(file_path):
    try:
        # Open the file and load existing data
        if os.path.exists(file_path):
            with open(file_path, 'r') as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = [[]]
        else:
            with open(file_path, 'w') as json_file:
                json.dump([[]], json_file, indent=4)
            existing_data = [[]]
        return existing_data
    
    except Exception as e:
        send_mail_or_logging('Exception during load json file', e)
        existing_data = [[]]
        return existing_data

# Method For Save Data in JSON File
def save_json(file_path, data):
    try:
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
    except Exception as e:
        send_mail_or_logging('Exception during save data in json file', e)

# Method for Add New Case Entry In Case File
def add_new_case_entry(case_entry, file_path):
    """Add a new case entry to the JSON file."""
    try:
        existing_data = load_json(file_path)

        existing_data[0].append(case_entry)
        save_json(file_path, existing_data)
    except Exception as e:
        send_mail_or_logging('Exception during add entry in json file', e)

# Method for Remove old Case Entry From Case File
def remove_old_case_entry(file_path):
    try:
        while True:
            existing_data = load_json(file_path)

            cutoff_date = datetime.now() - timedelta(days=1)

            new_case_entry_list = [
                entry for entry in existing_data[0]
                if datetime.strptime(entry["timestamp"], '%Y-%m-%d %H:%M:%S') > cutoff_date
            ]

            existing_data[0] = new_case_entry_list

            save_json(file_path, existing_data)

            time.sleep(86400)
    except Exception as e:
        send_mail_or_logging('Exception during remove old entry from json file', e)

# Method For Fetch Dicom image Instance from Server
def fetch_dicom_instances(orthanc_url):
    try:
        response = requests.get(f'{orthanc_url}/instances')
        if response.status_code != 200:
            logger.error("Error fetching instances:", response.status_code, response.text)
            return None
        instances = response.json()
        return instances
    except Exception as e:
        send_mail_or_logging('Exception during fetching dicom instances', e)
        return None

# Method For Download Dicom Instance
def download_dicom_instances(orthanc_url, instance_id):
    try:
        dicom_response = requests.get(f'{orthanc_url}/instances/{instance_id}/file')
        if dicom_response.status_code == 200:
            temp_dicom_path = os.path.join(output_directory, f'temp_{instance_id}.dcm')
            with open(temp_dicom_path, 'wb') as dicom_file:
                dicom_file.write(dicom_response.content)
                return temp_dicom_path
        else:
            logger.error(f"Error downloading {instance_id}: {dicom_response.status_code}")
    except Exception as e:
        send_mail_or_logging('Exception during downloading dicom instances', e)
        return None

# Method Extract PatientId From Dicom Image
def extract_patient_id_from_dicom_files(temp_dicom_path):
    try:
        dicom_data = dcmread(temp_dicom_path)
        patient_id = dicom_data.AccessionNumber if 'AccessionNumber' in dicom_data else 'unknown_patient'
        return patient_id
    except Exception as e:
        send_mail_or_logging('Exception during extracting case no', e)
        return None

# Method For Move Dicom Image To main op Folder
def move_dicom_files_to_output_folder(output_directory, patient_id, instance_id):
    try:
        final_dicom_path = os.path.join(output_directory, f'{patient_id}_{instance_id}.dcm')
        temp_dicom_path = os.path.join(output_directory, f'temp_{instance_id}.dcm')
        os.rename(temp_dicom_path, final_dicom_path)
        return final_dicom_path
    except Exception as e:
        send_mail_or_logging('Exception during move dicom files to output folder', e)
        return None

# Get Series ID from an Instance
def get_series_id(orthanc_url, instance_id):
    try:
        instance_info = requests.get(f'{orthanc_url}/instances/{instance_id}')
        if instance_info.status_code == 200:
            instance_data = instance_info.json()
            return instance_data.get('SeriesInstanceUID', None)
        else:
            logger.error(f"Error fetching instance {instance_id}: {instance_info.status_code}")
    except Exception as e:
        send_mail_or_logging('Exception during get series no', e)
        return None

# Delete Series from the server
def delete_series_from_server(orthanc_url, series_id):
    try:
        delete_response = requests.delete(f'{orthanc_url}/series/{series_id}')
        if delete_response.status_code == 204:
            logger.info(f'Deleted series {series_id} from Orthanc server.')
        else:
            logger.error(f'Error deleting series {series_id}: {delete_response.status_code} - {delete_response.text}')
    except Exception as e:
        send_mail_or_logging('Exception during deleting series from server', e)

# Method For Delete Dicom Image From Server
def delete_dicom_instance_from_server(orthanc_url, instance_id):
    try:
        delete_response = requests.delete(f'{orthanc_url}/instances/{instance_id}')

        # Check if deletion was successful (HTTP status code 204)
        if delete_response.status_code == 200:
            logger.info(f'DELETED INSTACE             /// {instance_id} ///')
        elif delete_response.status_code == 204:
            response_json = delete_response.json()
            if 'RemainingAncestor' in response_json and response_json['RemainingAncestor']:
                ancestor_path = response_json['RemainingAncestor']['Path']
                logger.info(f'Deleting remaining ancestor at path: {ancestor_path}')
                requests.delete(f'{orthanc_url}{ancestor_path}')
            else:
                logger.error(f'Error deleting instance {instance_id}: {delete_response.status_code}, {delete_response.text}')
        else:
            logger.error(f'Error deleting instance {instance_id}: {delete_response.status_code}, {delete_response.text}')

    except Exception as e:
        send_mail_or_logging('Exception during deleting dicom instance from server', e)

# Method For Notify API Which is Notify To Backend
def notify_api(api_url, case_id, file_path):
    try:
        data = {
            "patient_case_no": case_id,
            "lab_branch_id": LAB_BRANCH_ID,
            "file_path": file_path,

        }

        # payload = {
        #     'data': {
        #         'platform': 'Python',
        #         'branch_id': LAB_BRANCH_ID 
        #     },
        #     'exp': datetime.now(timezone.utc) + timedelta(seconds=45)
        # }
        # jwt_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

        # header = {
        #     'authorization': f'{jwt_token}',
        #     'Content-Type': 'application/json'
        # }

        response = requests.post(api_url, json=data)
        if response.status_code == 200:
            case_details = {'status_code': 200, 'message': f'API notified successfully for case ID {case_id}', 'response': response.json(), 'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            add_new_case_entry(case_details, CASE_FILE)
            return case_details
        else:
            send_mail_or_logging(f'Exception during notify api call {case_id}', e)
            return {'status_code': response.status_code, 'message': f'API notification failed for case ID {case_id}: {response.text}', 'response': None}
    except Exception as e:
        send_mail_or_logging(f'Exception during notify api call {case_id}', e)
        return {'status_code': 500, 'message': f'Error notifying API for case ID {case_id}: {str(e)}', 'response': None}

# Method For Create New Zip If not Exixst Otherwise Update Existing Zip File
def create_or_update_zip_file(s3_client, output_directory, patient_id, s3_bucket_name, files, api_url):
    zip_file_path = None
    try:
        zip_file_name = f'{patient_id}.zip'
        zip_file_path = os.path.join(output_directory , zip_file_name)

        try:
            s3_client.head_object(Bucket=s3_bucket_name, Key=f'dicom_files/{LAB_BRANCH_ID}/{zip_file_name}')
            print(f"ZIP FILE ALREADY EXISTS     /// dicom_files/{zip_file_name} ///")

            existing_zip_path = os.path.join(output_directory, f'existing_{zip_file_name}')
            s3_client.download_file(s3_bucket_name, f'dicom_files/{LAB_BRANCH_ID}/{zip_file_name}', existing_zip_path)

            with zipfile.ZipFile(existing_zip_path, 'r') as zipf:
                zipf.extractall(output_directory)
                print(f'EXTRACTED                   /// {existing_zip_path} ///.')

            for file in files:
                new_dicom_file_name = os.path.basename(file)
                os.rename(file, os.path.join(output_directory, new_dicom_file_name))

            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for root, _, filenames in os.walk(output_directory):
                    for filename in filenames:
                        if filename.endswith('.dcm') and not filename.endswith('.zip'):
                            zipf.write(os.path.join(root, filename), filename)
            print(f'CREATED UPDATED ZIP FILE    /// {zip_file_path} ///')

        except Exception as e:
            print(f'ZIP FILE DOSE NOT EXIST ON  /// {zip_file_name} /// ')
            # Create a new ZIP file
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for file in files:
                    print(f"FILE NAME                   /// {file} ///")
                    zipf.write(file, os.path.basename(file))
            print(f'CREATED NEW ZIP FILE        /// {zip_file_path} ///')

        try:
            s3_client.upload_file(zip_file_path, s3_bucket_name, f'dicom_files/{LAB_BRANCH_ID}/{zip_file_name}')
            print(f'UPLOADED TO S3 BUCKET NAME  /// {s3_bucket_name} ///')

            success_reposne = notify_api(api_url, patient_id, zip_file_name)
            print(f"API RESPONSE                /// {success_reposne}")
            print("\n**********************************************")
            print("***           UPLOAD PROCESS DONE          ***")
            print("**********************************************\n")

            os.remove(zip_file_path)
        except Exception as e:
            send_mail_or_logging(f'Error uploading {zip_file_path} to S3', e)

    except Exception as e:
        send_mail_or_logging('Exception during create and update zip file', e)

# Method For Delete .dcm image and Zip File From Op Folder
def clear_output_directory(output_directory):
    try:
        for root, dirs, files in os.walk(output_directory):
            for file in files:
                if file.endswith(".dcm") or file.startswith("existing_") or file.endswith(".zip"):
                    file_path = os.path.join(root, file)
                    try:
                        shutil.copy2(file_path,backup_path )
                        os.remove(file_path)
                        print(f'Removed file: {file_path}')
                    except OSError as e:
                        print(f'Error removing file {file_path}: {str(e)}')
    except Exception as e:
        send_mail_or_logging('Exception during clear op directory', e)

# Main Method For All Process
def send_dicom_image_to_healthray(s3_client, orthanc_url, output_directory, s3_bucket_name, processed_instances, api_url):
    try:
        counter = 0
        while True:

            instances = fetch_dicom_instances(orthanc_url)
            if instances is None:
                time.sleep(5)
                continue
            pateint_id_files = {}

            for instance_id in instances:
                if instance_id in processed_instances:
                    delete_dicom_instance_from_server(orthanc_url, instance_id)
                    continue
                print(f"DOWNLOADING INSTANCES       /// {instance_id} ///")

                dicom_file = download_dicom_instances(orthanc_url, instance_id)

                if dicom_file is None:
                    continue

                patient_id = extract_patient_id_from_dicom_files(dicom_file)
                # patient_id = "B395"

                if patient_id not in pateint_id_files:
                    pateint_id_files[patient_id] = []

                final_dicom_path = move_dicom_files_to_output_folder(output_directory, patient_id, instance_id)
                pateint_id_files[patient_id].append(final_dicom_path)
                print(f'MOVED TO FINAL PATH         /// {final_dicom_path} ///')

                delete_dicom_instance_from_server(orthanc_url, instance_id)

                processed_instances.add(instance_id)

            for patient_id, files in pateint_id_files.items():
                create_or_update_zip_file(s3_client, output_directory, patient_id, s3_bucket_name, files, api_url)
                counter = 0

            clear_output_directory(output_directory)

            if counter == 0:
                print("\n**********************************************")
                print("***    WAITING FOR NEW DICOM INSTANCE...   ***")
                print("**********************************************\n")
                counter = 1
                time.sleep(5)
    except Exception as e:
        send_mail_or_logging('Exception in main function', e)

if __name__ == '__main__':
    try:

        threading.Thread(target=remove_old_logs_from_log_file, args=(LOG_FILE_LIST,), daemon=True).start()
        time.sleep(2)
        threading.Thread(target=remove_old_case_entry, args=(CASE_FILE,), daemon=True).start()
        time.sleep(2)

        # Configuration
        orthanc_url = 'http://localhost:8042'
        output_directory = 'C:\\DICOM\\root\\dicom_data\\'

        # AWS S3 Configuration
        s3_bucket_name = ''
        aws_access_key_id = ''
        aws_secret_access_key = ''
        region_name = ''
        api_url = f'{API_URL}/patient_report_result/upload_case_zip_file'

        # Create S3 client
        s3_client = boto3.client('s3',
                                aws_access_key_id=aws_access_key_id,
                                aws_secret_access_key=aws_secret_access_key,
                                region_name=region_name)

        # Create output directory if it doesn't exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        processed_instances = set()

        # main Fuction For All Processes
        send_dicom_image_to_healthray(s3_client, orthanc_url ,output_directory, s3_bucket_name, processed_instances, api_url)
    
    except Exception as e:
        send_mail_or_logging('Exception in calling main function', e)