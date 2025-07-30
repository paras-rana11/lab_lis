from pydicom import dcmread
import requests
import zipfile
import boto3
import time
import json
import os

def upload_notify_server_to_s3(orthanc_url, output_directory, s3_bucket_name, aws_access_key_id, aws_secret_access_key, region_name, api_url):
    # Create S3 client
    s3_client = boto3.client('s3',
                             aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key,
                             region_name=region_name)

    # Create output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Function to upload zip file to S3
    def upload_to_s3(file_path, bucket_name):
        try:
            s3_client.upload_file(file_path, bucket_name, f'dicom_files/{os.path.basename(file_path)}')
            s3_path = f's3://{bucket_name}/dicom_files/{os.path.basename(file_path)}'
            return {'status_code': 200, 'message': f'Upload successful! File uploaded to {s3_path}', 's3_path': s3_path}
        except Exception as e:
            return {'status_code': 500, 'message': f'Error uploading {file_path} to S3: {str(e)}', 's3_path': None}

    # Function to notify API after file upload
    def notify_api(case_id, file_path):
        try:
            data = {
                "patient_case_no": case_id,
                "lab_branch_id": 71,
                "file_path": file_path,

            }
            response = requests.post(api_url, json=data)
            if response.status_code == 200:
                return {'status_code': 200, 'message': f'API notified successfully for case ID {case_id}', 'response': response.json()}
            else:
                return {'status_code': response.status_code, 'message': f'API notification failed for case ID {case_id}: {response.text}', 'response': None}
        except Exception as e:
            return {'status_code': 500, 'message': f'Error notifying API for case ID {case_id}: {str(e)}', 'response': None}

    # Step 1: Get the list of DICOM files (instances)
    response = requests.get(f'{orthanc_url}/instances')
    if response.status_code != 200:
        return {'status_code': response.status_code, 'message': f'Error fetching instances: {response.text}', 's3_path': None}

    instances = response.json()

    # Dictionary to group files by patient ID
    patient_files = {}

    # Step 2: Download each DICOM file
    for instance_id in instances:
        print(f'Downloading instance: {instance_id}')

        # Step 2.1: Get the DICOM file
        dicom_response = requests.get(f'{orthanc_url}/instances/{instance_id}/file')

        if dicom_response.status_code == 200:
            temp_dicom_path = os.path.join(output_directory, f'temp_{instance_id}.dcm')
            with open(temp_dicom_path, 'wb') as dicom_file:
                dicom_file.write(dicom_response.content)
            # print(f'Saved temporary file: {temp_dicom_path}')

            # Step 2.2: Read the DICOM file to get Patient ID
            # dicom_data = dcmread(temp_dicom_path)
            # patient_id = dicom_data.PatientID if 'PatientID' in dicom_data else 'unknown_patient'
            patient_id = "B395"

            # Create a list for this patient if it doesn't exist
            if patient_id not in patient_files:
                patient_files[patient_id] = []

            # Move the DICOM file to the appropriate patient ID path
            final_dicom_path = os.path.join(output_directory, f'{patient_id}_{instance_id}.dcm')
            os.rename(temp_dicom_path, final_dicom_path)
            patient_files[patient_id].append(final_dicom_path)
            # print(f'Moved to final path: {final_dicom_path}')

            # Step 2.3: Delete the DICOM file from the Orthanc server
            delete_response = requests.delete(f'{orthanc_url}/instances/{instance_id}')
            if delete_response.status_code == 204:  # 204 No Content indicates success
                print(f'Deleted instance {instance_id} from Orthanc server.')
            else:
                print(f'Error deleting instance {instance_id}: {delete_response.status_code}, {delete_response.text}')

        else:
            print(f"Error downloading {instance_id}: {dicom_response.status_code}")

    # Step 3: Create zip files for each patient and upload to S3
    upload_results = []
    for patient_id, files in patient_files.items():
        if files:
            zip_file_path = os.path.join(output_directory, f'{patient_id}.zip')
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for file in files:
                    zipf.write(file, os.path.basename(file))
                    os.remove(file)
            print(f'Created zip file: {zip_file_path}')

            # Step 4: Upload the zip file to S3 and get the result
            upload_result = upload_to_s3(zip_file_path, s3_bucket_name)
            upload_results.append(upload_result)
            if upload_result['status_code'] == 200:
                os.remove(zip_file_path)

                # Step 5: Notify API with case_id (patient_id) and filePath (S3 path)
                api_result = notify_api(patient_id, f"{patient_id}.zip")
                upload_results.append(api_result)

    return json.dumps(upload_results)

# Example usage:
orthanc_url = 'http://localhost:8042'
output_directory = 'downloaded_dicom_files'
s3_bucket_name = ''
aws_access_key_id = ''
aws_secret_access_key = ''
region_name = ''
api_url = 'http://192.168.1.61:4202/api/v1/patient_report_result/upload_case_zip_file'

while True:
    response = upload_notify_server_to_s3(orthanc_url, output_directory, s3_bucket_name, aws_access_key_id, aws_secret_access_key, region_name, api_url)
    if len(response) != 0:
        print(response)
    print("Check complete. Waiting for new instances...")
    time.sleep(5)
