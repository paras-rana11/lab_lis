import os
import time
import pydicom
from pydicom.uid import ExplicitVRLittleEndian
from pynetdicom import AE, QueryRetrievePresentationContexts
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelMove, StudyRootQueryRetrieveInformationModelFind


class QueryRetrieveLevel:
    PATIENT = "PATIENT"
    STUDY = "STUDY"
    SERIES = "SERIES"
    IMAGE = "IMAGE"


def retrieve_dicom_images(machine_ip, machine_port, output_folder):
    ae = AE(ae_title=b'MICRODICOM')
    ae.add_requested_context(StudyRootQueryRetrieveInformationModelMove)
    ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)
    ae.add_requested_context(ExplicitVRLittleEndian)

    assoc = ae.associate(machine_ip, machine_port)
    while True:
        if assoc.is_established:
            print("Association established with the machine.")

            # Example query to find studies
            query_dataset = pydicom.Dataset()
            query_dataset.QueryRetrieveLevel = QueryRetrieveLevel.STUDY
            query_dataset.PatientID = '*'  # Add any specific PatientID if needed

            responses = assoc.send_c_find(query_dataset, StudyRootQueryRetrieveInformationModelFind)

            for status, identifier in responses:
                if status.Status in (0xFF00, 0xFF01):  # Pending status codes
                    study_instance_uid = identifier.StudyInstanceUID

                    # C-MOVE request to move images
                    move_dataset = pydicom.Dataset()
                    move_dataset.QueryRetrieveLevel = QueryRetrieveLevel.STUDY
                    move_dataset.StudyInstanceUID = study_instance_uid
                    move_dataset.PatientID = identifier.PatientID

                    move_responses = assoc.send_c_move(move_dataset, 'MICRODICOM',
                                                       StudyRootQueryRetrieveInformationModelMove)

                    for move_status, move_identifier in move_responses:
                        if move_status.Status in (0xFF00, 0xFF01):  # Pending status codes
                            print(f'Received image: {move_identifier.SOPInstanceUID}')

                            # Saving image
                            filename = os.path.join(output_folder,
                                                    f'{move_identifier.PatientID}_{move_identifier.StudyDate}_{move_identifier.SOPInstanceUID}.dcm')
                            with open(filename, 'wb') as f:
                                f.write(move_identifier.PixelData)

                            print(f'Image saved as {filename}')
                        elif move_status.Status == 0x0000:  # Success
                            print('Move operation completed successfully.')
                        else:
                            print(f'Move operation failed with status: 0x{move_status.Status:04X}')
                elif status.Status == 0x0000:
                    print('Query completed successfully.')
                else:
                    print(f'Query failed with status: 0x{status.Status:04X}')

            time.sleep(1)

            assoc.release()
        else:
            print("Association Rejected, Aborted or Never Connected.")
        time.sleep(2)


if __name__ == '__main__':
    output_folder = "DICOM_IMAGE_FOLDER"
    machine_ip = "192.168.1.197"
    machine_port = 11112

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f'SERVER_IP: {machine_ip}')
    print(f'SERVER_PORT: {machine_port}')
    print(f'OUTPUT_FOLDER: {output_folder}')

    retrieve_dicom_images(machine_ip, machine_port, output_folder)


