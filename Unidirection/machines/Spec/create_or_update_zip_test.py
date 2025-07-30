import requests
import os
import zipfile
from pydicom import dcmread
import boto3
import time

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

def delete_all_files_in_output_directory():
    """Delete all files in the output directory."""
    for file_name in os.listdir(output_directory):
        file_path = os.path.join(output_directory, file_name)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f'Deleted file: {file_path}')
        except Exception as e:
            print(f'Error deleting file {file_path}: {str(e)}')

# Set to keep track of processed instance IDs
processed_instances = set()

while True:
    # Step 1: Get the list of DICOM files (instances)
    response = requests.get(f'{orthanc_url}/instances')
    if response.status_code != 200:
        print("Error fetching instances:", response.status_code, response.text)
        time.sleep(10)
        continue

    instances = response.json()

    # Dictionary to group files by patient ID
    patient_files = {}

    # Step 2: Download new DICOM files
    for instance_id in instances:
        if instance_id in processed_instances:
            continue

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

            # Mark this instance as processed
            processed_instances.add(instance_id)

        else:
            print(f"Error downloading {instance_id}: {dicom_response.status_code}")

    # Step 3: Create or update zip files for each patient and upload to S3
    for patient_id, files in patient_files.items():
        zip_file_name = f'{patient_id}.zip'
        zip_file_path = os.path.join(output_directory, zip_file_name)

        # Step 3.1: Check if the ZIP file already exists on S3
        try:
            s3_client.head_object(Bucket=s3_bucket_name, Key=f'dicom_files/{zip_file_name}')
            print(f'ZIP file {zip_file_name} already exists on S3. Updating...')

            # Step 3.2: Download the existing ZIP file
            existing_zip_path = os.path.join(output_directory, f'existing_{zip_file_name}')
            s3_client.download_file(s3_bucket_name, f'dicom_files/{zip_file_name}', existing_zip_path)

            # Step 3.3: Extract the existing ZIP file
            with zipfile.ZipFile(existing_zip_path, 'r') as zipf:
                zipf.extractall(output_directory)
                print(f'Extracted {existing_zip_path}.')

            # Step 3.4: Add new DICOM files to the extracted content
            for file in files:
                new_dicom_file_name = os.path.basename(file)
                os.rename(file, os.path.join(output_directory, new_dicom_file_name))  

            # Step 3.5: Create a new ZIP file with the updated content
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for root, _, filenames in os.walk(output_directory):
                    for filename in filenames:
                        if filename.endswith('.dcm') or filename == zip_file_name: 
                            zipf.write(os.path.join(root, filename), filename)
            print(f'Created updated ZIP file: {zip_file_path}')

        except Exception as e:
            print(f'ZIP file {zip_file_name} does not exist on S3. Creating new one...')
            # If the ZIP file does not exist, create a new one
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for file in files:
                    zipf.write(file, os.path.basename(file))  # Add the new DICOM files
            print(f'Created new ZIP file: {zip_file_path}')

        # Step 4: Upload the zip file to S3
        try:
            s3_client.upload_file(zip_file_path, s3_bucket_name, f'dicom_files/{zip_file_name}')
            print(f'Uploaded {zip_file_path} to S3 bucket {s3_bucket_name}')
            os.remove(zip_file_path) 
            if os.path.exists(existing_zip_path):
                os.remove(existing_zip_path) 

        except Exception as e:
            print(f'Error uploading {zip_file_path} to S3: {str(e)}')
    # if os.path.exists(output_directory):
    #     os.remove(final_dicom_path)
    delete_all_files_in_output_directory()
    print("Check complete. Waiting for new instances...")

    time.sleep(5)