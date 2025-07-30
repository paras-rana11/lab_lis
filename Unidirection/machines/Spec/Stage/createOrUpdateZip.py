'requests' , 'pydicom' , 'boto3'


from pydicom import dcmread
import requests
import zipfile
import boto3
import time
import json
import os

# Method For Fetch Dicom image Instance from Server
def fetch_dicom_instances(orthanc_url):
    response = requests.get(f'{orthanc_url}/instances')
    if response.status_code != 200:
        print("Error fetching instances:", response.status_code, response.text)
        return none
    instances = response.json()
    return instances

# Method For Download Dicom Instance
def download_dicom_instances(orthanc_url, instance_id):
    dicom_response = requests.get(f'{orthanc_url}/instances/{instance_id}/file')
    if dicom_response.status_code == 200:
        temp_dicom_path = os.path.join(output_directory, f'temp_{instance_id}.dcm')
        with open(temp_dicom_path, 'wb') as dicom_file:
            dicom_file.write(dicom_response.content)
            return temp_dicom_path
    else:
        print(f"Error downloading {instance_id}: {dicom_response.status_code}")
    return None

# Method Extract PatientId From Dicom Image
def extract_patient_id_from_dicom_files(temp_dicom_path):
    dicom_data = dcmread(temp_dicom_path)
    patient_id = dicom_data.PatientID if 'PatientID' in dicom_data else 'unknown_patient'
    return patient_id

# Method For Move Dicom Image To main op Folder
def move_dicom_files_to_output_folder(output_directory, patient_id, instance_id):
    final_dicom_path = os.path.join(output_directory, f'{patient_id}_{instance_id}.dcm')
    temp_dicom_path = os.path.join(output_directory, f'temp_{instance_id}.dcm')
    os.rename(temp_dicom_path, final_dicom_path)
    return  final_dicom_path

# Get Series ID from an Instance
def get_series_id(orthanc_url, instance_id):
    instance_info = requests.get(f'{orthanc_url}/instances/{instance_id}')
    if instance_info.status_code == 200:
        instance_data = instance_info.json()
        return instance_data.get('SeriesInstanceUID', None)
    else:
        print(f"Error fetching instance {instance_id}: {instance_info.status_code}")
    return None

# Delete Series from the server
def delete_series_from_server(orthanc_url, series_id):
    delete_response = requests.delete(f'{orthanc_url}/series/{series_id}')
    if delete_response.status_code == 204:
        print(f'Deleted series {series_id} from Orthanc server.')
    else:
        print(f'Error deleting series {series_id}: {delete_response.status_code} - {delete_response.text}')

# Method For Delete Dicom Image From Server
def delete_dicom_instance_from_server(orthanc_url, instance_id):
    delete_response = requests.delete(f'{orthanc_url}/instances/{instance_id}')

    # Check if deletion was successful (HTTP status code 204)
    if delete_response.status_code == 200:
        print(f'DELETED INSTACE             /// {instance_id} ///')
    elif delete_response.status_code == 204:
        response_json = delete_response.json()
        if 'RemainingAncestor' in response_json and response_json['RemainingAncestor']:
            ancestor_path = response_json['RemainingAncestor']['Path']
            print(f'Deleting remaining ancestor at path: {ancestor_path}')
            requests.delete(f'{orthanc_url}{ancestor_path}')
        else:
            print(f'Error deleting instance {instance_id}: {delete_response.status_code}, {delete_response.text}')
    else:
        print(f'Error deleting instance {instance_id}: {delete_response.status_code}, {delete_response.text}')

# Method For Notify API Which is Notify To Backend
def notify_api(api_url, case_id, file_path):
# def notify_api(api_url, case_id, file_path, HEADER):
    try:
        data = {
            "patient_case_no": case_id,
            "lab_branch_id": 121,
            "file_path": file_path,

        }
        response = requests.post(api_url, json=data)
        if response.status_code == 200:
            return {'status_code': 200, 'message': f'API notified successfully for case ID {case_id}', 'response': response.json()}
        else:
            return {'status_code': response.status_code, 'message': f'API notification failed for case ID {case_id}: {response.text}', 'response': None}
    except Exception as e:
        return {'status_code': 500, 'message': f'Error notifying API for case ID {case_id}: {str(e)}', 'response': None}

# Method For Create New Zip If not Exixst Otherwise Update Existing Zip File
def create_or_update_zip_file(s3_client, output_directory, patient_id, s3_bucket_name, files, api_url):
# def create_or_update_zip_file(s3_client, output_directory, patient_id, s3_bucket_name, files, api_url, HEADER):
    final_response_list = []
    zip_file_name = f'{patient_id}.zip'
    zip_file_path = os.path.join(output_directory , zip_file_name)

    try:
        s3_client.head_object(Bucket=s3_bucket_name, Key=f'dicom_files/{zip_file_name}')
        print(f"ZIP FILE ALREADY EXISTS     /// dicom_files/{zip_file_name} ///")

        existing_zip_path = os.path.join(output_directory, f'existing_{zip_file_name}')
        s3_client.download_file(s3_bucket_name, f'dicom_files/{zip_file_name}', existing_zip_path)

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

    except:
        print(f'ZIP FILE DOSE NOT EXIST ON  /// {zip_file_name} /// ')
        # Create a new ZIP file
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for file in files:
                print(f"FILE NAME                   /// {file} ///")
                zipf.write(file, os.path.basename(file))
        print(f'CREATED NEW ZIP FILE        /// {zip_file_path} ///')

    try:
        s3_client.upload_file(zip_file_path, s3_bucket_name, f'dicom_files/{zip_file_name}')
        print(f'UPLOADED TO S3 BUCKET NAME  /// {s3_bucket_name} ///')
        success_reposne = notify_api(api_url, patient_id, zip_file_name)
        # success_reposne = notify_api(api_url, patient_id, zip_file_name, HEADER)
        print(f"API RESPONSE                /// {success_reposne}")
        print("\n**********************************************")
        print("***           UPLOAD PROCESS DONE          ***")
        print("**********************************************\n")
        os.remove(zip_file_path)
    except Exception as e:
        print(f'Error uploading {zip_file_path} to S3: {str(e)}')



# Method For Delete .dcm image and Zip File From Op Folder
def clear_output_directory(output_directory):
    for root, dirs, files in os.walk(output_directory):
        for file in files:
            if file.endswith(".dcm") or file.startswith("existing_") or file.endswith(".zip"):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f'Removed file: {file_path}')
                except OSError as e:
                    print(f'Error removing file {file_path}: {str(e)}')

# Main Method For All Process
def main(s3_client, orthanc_url, output_directory, s3_bucket_name, processed_instances, api_url):
# def main(s3_client, orthanc_url, output_directory, s3_bucket_name, processed_instances, api_url, HEADER):
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

            # patient_id = extract_patient_id_from_dicom_files(dicom_file)
            patient_id = "D208"

            if patient_id not in pateint_id_files:
                pateint_id_files[patient_id] = []

            final_dicom_path = move_dicom_files_to_output_folder(output_directory, patient_id, instance_id)
            pateint_id_files[patient_id].append(final_dicom_path)
            print(f'MOVED TO FINAL PATH         /// {final_dicom_path} ///')

            delete_dicom_instance_from_server(orthanc_url, instance_id)

            processed_instances.add(instance_id)

        for patient_id, files in pateint_id_files.items():
            create_or_update_zip_file(s3_client, output_directory, patient_id, s3_bucket_name, files, api_url)
            # create_or_update_zip_file(s3_client, output_directory, patient_id, s3_bucket_name, files, api_url, HEADER)
            counter = 0

        clear_output_directory(output_directory)

        if counter == 0:
            print("\n**********************************************")
            print("***    WAITING FOR NEW DICOM INSTANCE...   ***")
            print("**********************************************\n")
            counter = 1
            time.sleep(5)

if __name__ == '__main__':
    # Configuration
    orthanc_url = 'http://localhost:8042'
    output_directory = 'C:\\DICOM\\root\\dicom_data\\'

    # JWT secret key and API
    jwt_secret_key = ''
    API_URL = ""

    # # Generate JWT token
    # jwt_token = jwt.encode({"data": {"platform": "Python"}}, jwt_secret_key, 'HS256')
    # HEADER = {'Authorization': f'{jwt_token}'}


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
    main(s3_client, orthanc_url ,output_directory, s3_bucket_name, processed_instances, api_url)
    # main(s3_client, orthanc_url ,output_directory, s3_bucket_name, processed_instances, api_url, HEADER)