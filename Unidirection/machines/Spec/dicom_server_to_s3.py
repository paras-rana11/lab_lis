import requests
import os
import zipfile
from pydicom import dcmread
import boto3

# Configuration
orthanc_url = 'http://localhost:8042'
output_directory = 'downloaded_dicom_files'

# AWS S3 Configuration
s3_bucket_name = ''
aws_access_key_id = ''
aws_secret_access_key = ''
region_name = ''

# Create S3 client
s3_client = boto3.client('s3',
                         aws_access_key_id=aws_access_key_id,
                         aws_secret_access_key=aws_secret_access_key,
                         region_name=region_name)

# Create output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Step 1: Get the list of DICOM files (instances)
response = requests.get(f'{orthanc_url}/instances')
if response.status_code != 200:
    print("Error fetching instances:", response.status_code, response.text)
    exit(1)

instances = response.json()

# Dictionary to group files by patient ID
patient_files = {}

# Step 2: Download each DICOM file
for instance_id in instances:
    print(f'Downloading instance: {instance_id}')

    # Step 2.1: Get the DICOM file
    dicom_response = requests.get(f'{orthanc_url}/instances/{instance_id}/file')

    if dicom_response.status_code == 200:
        # Save the DICOM file temporarily
        temp_dicom_path = os.path.join(output_directory, f'temp_{instance_id}.dcm')
        with open(temp_dicom_path, 'wb') as dicom_file:
            dicom_file.write(dicom_response.content)
        print(f'Saved temporary file: {temp_dicom_path}')

        # Step 2.2: Read the DICOM file to get Patient ID
        dicom_data = dcmread(temp_dicom_path)
        patient_id = dicom_data.PatientID if 'PatientID' in dicom_data else 'unknown_patient'

        # Create a list for this patient if it doesn't exist
        if patient_id not in patient_files:
            patient_files[patient_id] = []

        # Move the DICOM file to the appropriate patient ID path
        final_dicom_path = os.path.join(output_directory, f'{patient_id}_{instance_id}.dcm')
        os.rename(temp_dicom_path, final_dicom_path)
        patient_files[patient_id].append(final_dicom_path)
        print(f'Moved to final path: {final_dicom_path}')

        # Step 2.3: Delete the DICOM file from the Orthanc server
        delete_response = requests.delete(f'{orthanc_url}/instances/{instance_id}')
        if delete_response.status_code == 204:  # 204 No Content indicates success
            print(f'Deleted instance {instance_id} from Orthanc server.')
        else:
            print(f'Error deleting instance {instance_id}: {delete_response.status_code}, {delete_response.text}')

    else:
        print(f"Error downloading {instance_id}: {dicom_response.status_code}")

# Step 3: Create zip files for each patient and upload to S3
for patient_id, files in patient_files.items():
    if files:
        zip_file_path = os.path.join(output_directory, f'{patient_id}.zip')
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for file in files:
                zipf.write(file, os.path.basename(file))
                os.remove(file)  # Delete the individual DICOM file after adding to zip
        print(f'Created zip file: {zip_file_path}')

        # Step 4: Upload the zip file to S3
        try:
            s3_client.upload_file(zip_file_path, s3_bucket_name, f'dicom_files/{os.path.basename(zip_file_path)}')
            print(f'Uploaded {zip_file_path} to S3 bucket {s3_bucket_name}')
            os.remove(zip_file_path)  # Delete the zip file after upload
        except Exception as e:
            print(f'Error uploading {zip_file_path} to S3: {str(e)}')

print("Download, compression, and upload complete.")
