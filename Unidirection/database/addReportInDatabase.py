# pip install mysql-connector-python

import json
import logging
import os
import re
import time
import uuid
import hashlib
import mysql.connector
from mysql.connector import Error

# Configuration
my_host = '127.0.0.1'
my_user = 'root'
my_pass = 'Root@1234'
my_db = 'lis'
folder_path = '/home/dhruveel/Desktop/Dhruveel/machine_integration_main_project/machine_integration_main_project/attachments'

# stored_license_key = "34ad7747ef4f423ca6234c0a6de73eedff591ea67235ae8e84486a90ae731b56"
#
#
# def get_mac_address():
#     mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
#     return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])
#
#
# def generate_license_key(mac_address):
#     key = hashlib.sha256(mac_address.encode()).hexdigest()
#     return key
#
#
# def check_license(license_key, mac_address):
#     generated_key = generate_license_key(mac_address)
#     return generated_key == license_key
#
#
# # License check
# current_mac = get_mac_address()
# if not check_license(stored_license_key, current_mac):
#     print("Invalid license. This executable can only run on the registered system.")
#     logging.error("Invalid license. This executable can only run on the registered system.")
#     sys.exit(1)

def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        return None

def get_connection():
    try:
        con = mysql.connector.connect(
            host=my_host,
            user=my_user,
            password=my_pass,
            database=my_db
        )
        if con.is_connected():
            return con
    except Error as e:
        return None

def run_query(con, prepared_sql, data_tpl):
    try:
        cur = con.cursor()
        cur.execute(prepared_sql, data_tpl)
        con.commit()
        msg = "Rows affected: {}".format(cur.rowcount)
        return cur
    except Exception as e:
        return None

def close_cursor(cur):
    try:
        cur.close()
    except Exception as e:
        pass

def close_connection(con):
    try:
        con.close()
    except Exception as e:
        pass

# Method for save data in mysql database
def send_to_mysql(data):
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
        return False
    finally:
        close_connection(con)
    return True

# Method for Beckman Coulter Access 2 Machine
def extract_report_data_access_2(access_data):
    lines = access_data.strip().split('\x02')
    machine_name, patient_name, test_name, test_result = 'ACCESS', 'N/A', 'N/A', 'N/A'
    final_list = []
    for line in lines:
        if line.startswith('1H'):
            machine_name = line.split('|')[4]
        elif line.startswith('3O'):
            patient_name = line.split('|')[2]
        elif line.startswith('4R'):
            test_data = line.split('|')
            test_name = test_data[2].replace('^', '').rstrip('1')
            test_result = test_data[3].replace('>', '').replace('<', '')
    final_list.append((machine_name, patient_name, {test_name: test_result}))
    return final_list
    # return (machine_name, patient_name, {test_name: test_result})

# Method for Beckman Coulter AU 480 Machine
def extract_report_data_au_480(au_data):
    machine_name, patient_name = "AU_480", "N/A"
    final_list = []
    sub_data = au_data.strip().split()
    if len(sub_data) > 3:
        patient_name = sub_data[3]
    
    pattern = r'(\d{3})\s+(\d+\.\d+)'
    matches = re.findall(pattern, au_data)
    result = {key: value for key, value in matches}
    
    final_list.append((machine_name, patient_name, result))
    return final_list
    # return (machine_name, patient_name, result)

# Method for Cobas E 411 Machine
def extract_report_data_e_411(hl7_message):
    machine_id = 'e_411'
    final_list = []
    patient_id_match = re.search(r'3O\|1\|([^|]+)', hl7_message)
    patient_id = patient_id_match.group(1) if patient_id_match else None
    results = re.findall(r'R\|\d+\|\^\^\^(\d+)\^\^[^\|]+\|([^\|]+)', hl7_message)
    formatted_results = {result[0]: result[1] for result in results}
    converted_results = convert_values(formatted_results)
    final_list.append((machine_id, patient_id, converted_results))
    return final_list
    # return (machine_id, patient_id, converted_results)

# Method for remove -1 and 1 for Cobas E 411
def convert_values(input_dict):
    output_dict = {}
    for key, value in input_dict.items():
        # Handle values with '-1^' or '1^'
        if '-1^' in value:
            value = value.replace('-1^', '')
        elif '1^' in value:
            value = value.replace('1^', '')
        output_dict[key] = value
    return output_dict

# Method for Cobas C 111 Machine
def extract_report_data_c_111(data):
    # Use fixed 'c111' value
    c111 = 'c111'
    lines = data.split("\n")
    pid = ''
    final_list = []
    
    for line in lines:
        if line.__contains__('3O'):
            pid = re.sub(r'\^\d', '', line.split("|")[3]).replace("^","")
            # pid_field = line.split("|")[3]
            # pid = re.sub(r'\^\d+', '', pid_field).replace("^", "")
            
    # Extract results in the desired format
    result_pattern = re.compile(r"(\d)R\|\d\|\^\^\^(\d+)\|([\d.]+)\|[^|]*")
    results = result_pattern.findall(data)

    results_dict = {code: value for _, code, value in results}
    final_list.append((c111, pid, results_dict))
    return final_list
    # return (c111, pid, results_dict)

# Method for Cobas C 311 Machine
def extract_report_data_c_311(data):
    c311 = 'c311'
    lines = data.split("\n")
    pid_field = None  # Initialize with a default value
    final_list = []
    result_dict = {}
    formatted_lines = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if line.startswith(("R|", "O|", "P|", "L|", "C|")):
            if buffer:  
                formatted_lines.append(buffer)
                buffer = ""
            buffer = line 
        else:
            buffer += line
    if buffer:
        formatted_lines.append(buffer)
        
    for line in formatted_lines:
        if line.__contains__('O'):
            pid_field = line.split("|")[2].split('-')[0].strip()
        elif line.startswith('R'):
            parts = line.split('|')
            if len(parts) >= 4:
                test_id = parts[2].replace('^', ' ').replace('/', ' ').strip()
                if '\x02' in test_id:
                    test_id = test_id.split('\x02')[1]
                test_value = parts[3]
                result_dict[test_id] = test_value

    if pid_field:
        final_list.append((c311, pid_field, result_dict))
    return final_list

# Method for Sysmex Machine
def extract_common_report_data_for_sysmex(text):
    lines = text.split('\n')
    formatted_data = []

    obx_data = ""
    for line in lines:
        # Check if line starts with "R", indicating a new OBX segment
        if line.startswith("R"):
            if obx_data:
                formatted_data.append(obx_data.strip())
            obx_data = line  # Initialize with the current line
        elif obx_data and line.strip():
            # Join the current line to the OBX data, ensuring proper spacing
            obx_data += "|" + line.strip()
        else:
            if obx_data:
                # Append the final OBX data segment
                formatted_data.append(obx_data.strip())
                obx_data = ""
            # Append non-OBX lines directly to the formatted dataw
            formatted_data.append(line)

    # Append any remaining OBX data
    if obx_data:
        formatted_data.append(obx_data.strip())
    
    if formatted_data:
        machine_name = 'sysmex'
        patients = []  # Store multiple patient records
        patient_name = None
        report_data = {}

        for line in formatted_data:
            if line.startswith('O'):
                if patient_name and report_data:
                    patients.append((machine_name, patient_name, report_data))
                    report_data = {}

                patient_name = line.split('|')[3].replace('^M', '').replace('^F', '').replace('^', '').strip()
            elif line.startswith('R'):
                if len(line.split('|')) > 3:
                    field_name = line.split('|')[2].replace('^1', '').replace('^', '')
                    value = line.split('|')[3].strip()
                    report_data[field_name] = value

        # Append the last patient's data after the loop
        if patient_name and report_data:
            patients.append((machine_name, patient_name, report_data))

        return patients

# Method for XN 350 Machine
def extract_report_data_xn_350(text):
    return extract_common_report_data_for_sysmex(text, 'XN-350')

# Method for XN 550 Machine
def extract_report_data_xn_550(text):
    return extract_common_report_data_for_sysmex(text, 'XN_550')

# Method for XN 330 Machine
def extract_report_data_xn_330(text):
    return extract_common_report_data_for_sysmex(text, 'XN-330')

# Method for XP 100 Machine
def extract_report_data_xp_100(text):
    return extract_common_report_data_for_sysmex(text, 'XP-100')

# Method for XP 100 Machine
def extract_report_data_xn_1000(text):
    return extract_common_report_data_for_sysmex(text, 'XP-1000')

# Method for SNIBE MAGLUMI Machine
def extract_report_data_maglumi(text):
    
    machine_name = "snibe"
    reports = text.strip().split("\n\n")  
    final_list = []
    for report_block in reports:
        lines = report_block.split("\n")
        pid = ""
        report = {}
        
        for line in lines:
            if line.startswith("SPM"):
                data_pid = line.split("|")
                pid = data_pid[2].replace("^", "")
            elif line.startswith("OBX"):
                data_report = line.split("|")
                report_name = data_report[3]
                report_data = data_report[5].split("^")[0]
                
                if report_name not in report:
                    report[report_name] = []
                report[report_name].append(float(report_data))
        
        # for key in report:
        #     report[key] =[ ', '.join(report[key])]
        final_list.append((machine_name,pid,report))
    return final_list    
    # return (machine_name, pid, report)

# Method for CELL TAK @+ Machine
def extract_report_data_celltak(text):
    lines = text.split("\n")
    machine_name = "celltak_@+"
    pid = ""
    report_data = {}
    final_list = []
    for line in lines:
        if line.startswith("P"):
            pid = line.split("|")[4]
        elif line.startswith("R"):
            report_name = line.split("|")[2].replace("^","")
            report_value = line.split("|")[3]
            report_data[report_name] = report_value
    
    final_list.append((machine_name,pid,report_data))
    return final_list
    # return (machine_name,pid,report_data)

# Method for CELL TAK @+ Mek 6500 Machine
def remove_starting_chars(data):
    return [re.sub(r'^\x05|\x03|\x02', '', item) for item in data]

# Method for CELL TAK @+ Mek 6500 Machine
def extract_report_data_cell_tak_6500(data):
    lines = data.split('\n')
    data_line = remove_starting_chars(lines)
    patientId = None
    machine_name = 'cell_tak'
    patients = []
    result_dict = {}
    for line in data_line:
        
        if line.startswith('2P'):
            patientId = line.split('  ')
            if len(patientId) >=2:
                patientId = line.split('  ')[1].split('^')[0].strip()
            else:
                patientId = patientId[0].replace('MEK3',' ').strip()
        elif re.match(r'^[0-7]R\|',line):
            test_name = line.split('|')[2].split('^')
            if len(test_name) > 4:
                test_name = test_name[3]
            else:
                test_name = test_name[3]
            test_result = line.split('|')[3]
            result_dict[test_name] = test_result
    if patientId and result_dict:
        patients.append((machine_name, patientId, result_dict))
    return patients

# Method for Horiba H 500 Machine
def extract_report_data_horiba_h_500(data):
    lines = data.split('\n')
    lines = remove_starting_chars(lines)
    patientId = None
    machine_name = 'h500'
    patients = []
    result_dict = {}

    for line in lines:
        if line.startswith('2P'):
            patientId = line.split('|')[3]
        elif re.match(r'^[0-9]R\|',line):
            test_name = line.split('|')[2].split('^')[3]
            test_result = line.split('|')[3]
            result_dict[test_name] = test_result

    if patientId and result_dict:
        patients.append((machine_name, patientId, result_dict))
    return patients

# Method for Fuji Film Machine
def extract_report_data_nx_600(text):
    data = text.split(",")
    pid = data[5].strip()

    report_data = {}
    final_list = []
    i = 12  
    while i < len(data):
        if i + 2 < len(data):
            test_name = data[i].strip()
            test_result = data[i+2].split()[0]
            report_data[test_name] = test_result
            i += 7
        else:
            break
    final_list.append(("fuji_film",pid,report_data))
    return final_list
    # return ("fuji_film",pid,report_data)

# Method for Fuji Film Machine
def extract_report_data_nx_700(text):
    data = text.split(",")
    pid = data[5].strip()

    report_data = {}
    final_list = []
    i = 12  
    while i < len(data):
        if i + 2 < len(data):
            test_name = data[i].strip()
            test_result = data[i+2].split()[0]
            report_data[test_name] = test_result
            i += 7
        else:
            break
    final_list.append(("fuji_film",pid,report_data))
    return final_list

# Method for Wondfo Finacare Machine
def extract_report_data_fiameter(text):
    lines = text.split("\n")
    pid = ''
    machine_name = "fincare"
    result_dict ={}
    final_list = []
    for line in lines:
        if line.startswith('PID'):
            pid = line.split('|')[5]
        elif line.startswith('OBX'):
            obx = line.split('|')
            test_name = obx[4].split()
            test_result = obx[5].split()
            filtered_test_result = [v for v in test_result if any(char.isdigit() for char in v)]
            result_dict.update(dict(zip(test_name, filtered_test_result)))
    final_list.append((machine_name,pid,result_dict))
    return final_list

# Method for Tisenc Accre 8 Machine
def extract_report_data_accre_8(text):
    reports = text.split("MSH")  # Split the data by the 'MSH' delimiter to separate each report
    machine_name = "accre_8"
    extracted_data = []

    for report in reports:
        if not report.strip():  # Skip any empty or whitespace-only parts
            continue
        
        lines = report.split("\n")
        pid = ''
        report_data = {}
        
        for line in lines:
            if line.startswith('PID'):
                pid = line.split('|')[5]
            elif line.startswith('OBX'):
                test_name = line.split('|')[4]
                test_result = line.split('|')[5]
                report_data[test_name] = test_result
        
        if pid and report_data:  # Ensure we have valid data before adding it to the list
            extracted_data.append((machine_name, pid, report_data))

    return extracted_data

# Method for Agappe Mispa Machine
def extract_report_data_mispa_nano(text):
    lines = text.split('\n')
    formatted_data = []

    obx_data = ""
    for line in lines:
        # Check if line starts with "R", indicating a new OBX segment
        if line.startswith("R"):
            if obx_data:
                formatted_data.append(obx_data.strip())
            obx_data = line  # Initialize with the current line
        elif obx_data and line.strip():
            # Join the current line to the OBX data, ensuring proper spacing
            obx_data += "|" + line.strip()
        else:
            if obx_data:
                # Append the final OBX data segment
                formatted_data.append(obx_data.strip())
                obx_data = ""
            # Append non-OBX lines directly to the formatted data
            formatted_data.append(line)

    # Append any remaining OBX data
    if obx_data:
        formatted_data.append(obx_data.strip())

    if formatted_data:
        machine_name = 'mispa'
        patients = []  # Store multiple patient records
        patient_name = None
        report_data = {}

        for line in formatted_data:
            if line.startswith('O'):
                if patient_name and report_data:
                    patients.append((machine_name, patient_name, report_data))
                    report_data = {}
                    patient_name = None
                patient_name = re.sub(r"^(\d+)(\/[A-Za-z])$", r"\1", line.split('|')[3])
            elif line.startswith('R'):
                report_name = line.split('|')[2].split('^')[1]
                report_value = line.split('|')[3].replace('^', '').strip()
                report_data[report_name] = report_value

        # Append the last patient's data after the loop
        if patient_name and report_data:
            patients.append((machine_name, patient_name, report_data))

        return patients

# Method for Electrolyzer Analyzer Gastat Machie 
def extract_report_data_electrolyzer_analyzer_gastat(data):
    byte_specifications = [
        (1, 2, "String ID"),
        (3, 5, "Data Length"),
        (6, 25, "Specimen ID"),
        (26, 45, "P-ID"),
        (46, 65, "Patient Name"),
        (66, 85, "Dummy"),
        (86, 90, "Height (cm)"),
        (91, 95, "Weight (kg)"),
        (96, 96, "Sex"),
        (97, 99, "Age"),
        (100, 109, "Date of Birth"),
        (110, 119, "Department Name"),
        (120, 247, "Comments"),
        (248, 267, "Space 1"),
        (268, 287, "Space 2"),
        (288, 307, "Space 3"),
        (308, 317, "Date"),
        (318, 325, "Time"),
        (326, 330, "pH"),
        (331, 335, "pCO2"),
        (336, 340, "pO2"),
        (341, 345, "Na"),
        (346, 350, "K"),
        (351, 355, "Cl"),
        (356, 360, "Ca"),
        (361, 365, "Glc"),
        (366, 370, "La"),
        (371, 375, "Hb"),
        (376, 380, "SO2"),
        (381, 385, "FO2Hb"),
        (386, 390, "FCOHb"),
        (391, 395, "FMetHb"),
        (396, 400, "FHHb"),
        (401, 405, "Bil"),
        (406, 410, "tHb"),
        (411, 415, "Barometric Pressure"),
        (416, 419, "Patient Temp"),
        (420, 424, "FiO2"),
        (425, 429, "Respiratory Volume"),
        (430, 432, "Breathing Rate"),
        (433, 452, "Measure Appliance"),
        (453, 472, "Sample Type"),
        (473, 492, "Sample Area"),
        (493, 512, "Operator ID"),
        (513, 532, "Doctor ID"),
        (533, 542, "Sampling Date"),
        (543, 547, "Sampling Time"),
        (548, 557, "Birth Weight"),
        (558, 567, "Pregnancy Period"),
        (568, 572, "AG"),
        (573, 577, "AG(K)"),
        (578, 581, "HCO3-act"),
        (582, 585, "HCO3-std"),
        (586, 590, "MCHC"),
        (591, 595, "BE"),
        (596, 600, "BE(ecf)"),
        (601, 605, "BE(B)"),
        (606, 609, "BB"),
        (610, 614, "ctCO2"),
        (615, 618, "ctCO2(P)"),
        (619, 623, "ctCO2(B)"),
        (624, 628, "CO2/dry air"),
        (629, 632, "Hct"),
        (633, 637, "pH(T)"),
        (638, 642, "pH(P,st)"),
        (643, 647, "H+"),
        (648, 652, "PCO2(T)"),
        (653, 657, "PO2(T)"),
        (658, 662, "sO2(est)"),
        (663, 667, "ctO2"),
        (668, 672, "ctO2(Hb)"),
        (673, 677, "BO2"),
        (678, 682, "p50"),
        (683, 687, "p50(T)"),
        (688, 692, "p50(st)"),
        (693, 697, "O2sat(est)"),
        (698, 702, "PO2/FIO2"),
        (703, 707, "Ca++(7.4)"),
        (708, 712, "PO2(A,T)"),
        (713, 717, "PAO2"),
        (718, 722, "PO2(A-a)"),
        (723, 727, "PO2(A-a)(T)"),
        (728, 731, "PO2(a/A)"),
        (732, 736, "PO2(a/A)(T)"),
        (737, 740, "RI"),
        (741, 745, "RI(T)"),
        (746, 749, "ctO2(a)"),
        (750, 754, "ctO2(B)"),
        (755, 759, "ctO2(v)"),
        (760, 764, "ctO2(a-v)"),
        (765, 769, "ctO2([a-v]/a)"),
        (770, 774, "VO2"),
        (775, 779, "DO2"),
        (780, 784, "Qt"),
        (785, 789, "Qsp/Qt"),
        (790, 794, "Qsp/Qt(est)"),
        (795, 799, "OER"),
        (800, 814, "Space"),
        (815, 834, "Parameter Status"),
        (835, 835, "CR")
    ]

    extracted_data = {}
    specimen_id = None
    patients = []

    try:
        for start, end, field_name in byte_specifications:
            value = data[start - 1:end].strip() 
            if field_name == "Specimen ID":
                specimen_id = value
            else:
                extracted_data[field_name] = value if value else "'"  

    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    patients.append(("gastst", specimen_id, extracted_data))
    return patients

# Method for Mindray BS 240 Machie 
def extract_report_data_mindray_bs_240(data):
    lines = data.split('\n')
    machine_name = 'Mindry_BS_240'
    patientId = None
    report_data = {}
    patients = []
    for line in lines:
        if line.startswith('O'):
            if patientId and report_data:
                patients.append((machine_name, patientId, report_data))
                report_data = {}
                patientId = None
            if len(line.split('|'))>= 3:
                patientId = line.split('|')[3].strip()
        elif line.startswith('R'):
            if len(line.split('|'))>= 2:
                report_name = line.split('|')[2].replace('^F', '').replace('^', '')
                report_value = line.split('|')[3].replace('^', '')
                report_data[report_name] = report_value

    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))

    return patients

def extract_report_data_mindray_cl_900_i(data):
    lines = data.split('\n')
    machine_name = 'Mindry_CL_900_I'
    patientId = None
    report_data = {}
    patients = []
    for line in lines:
        if line.startswith('O'):
            if patientId and report_data:
                patients.append((machine_name, patientId, report_data))
                report_data = {}
                patientId = None
            patientId = line.split('|')[3]
        elif line.startswith('R'):
            report_name = line.split('|')[2].replace('^F', '').replace('^', '')
            report_value = line.split('|')[3].replace('^', '')
            report_data[report_name] = report_value

    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))

    return patients

# Method for Mindray BS 240 Machie 
def extract_report_data_mindray_bc_5130(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "Mindray_BC_5130"
    report_data = {}
    patients = []
    for line in lines:

        if line.startswith('PID'):
            if patientId and report_data:
                patients.append((machine_name, patientId, report_data))
                report_data = {}
                patientId = None
            patientId = line.split('|')[3].replace('^MR', '').replace('^', '')
        elif line.startswith('OBX'):
            if line.split('|')[2] == 'IS':
                continue
            report_name = line.split('|')[3].split('^')[1]
            report_value = line.split('|')[5]
            report_data[report_name] = report_value

    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))

    return patients

def extract_report_data_mindray_bc_5150(data):
    lines = data.split('\x02\x0b')  # Splitting based on potential delimiter
    machine_name = "BC_5150"
    patients = []
    
    for block in lines:
        formatted_data = []
        obx_data = ""
        
        for line in block.split('\n'):
            line = line.strip()
            if line.startswith("OBX"):
                if obx_data:
                    formatted_data.append(obx_data.strip())
                obx_data = line  
            elif obx_data and line:
                obx_data += " " + line.strip()
            else:
                if obx_data:
                    formatted_data.append(obx_data.strip())  
                    obx_data = ""  
                formatted_data.append(line)  
        if obx_data:
            formatted_data.append(obx_data.strip())  
        
        # Extract patient data
        patient_id = None
        report_data = {}

        for line in formatted_data:
            if line.startswith('OBR'):
                if patient_id and report_data:
                    patients.append((machine_name, patient_id, str(report_data)))
                    report_data = {}
                parts = line.split('|')
                if len(parts) > 3:
                    patient_id = parts[3].replace('^MR', '').replace('^', '').strip()
            elif line.startswith('OBX'):
                parts = line.split('|')
                if len(parts) > 5 and parts[2] != 'IS':  
                    report_name = parts[3].split('^')[1] if '^' in parts[3] else parts[3]
                    report_value = parts[5]
                    report_data[report_name] = report_value

        if patient_id and report_data:
            patients.append((machine_name, patient_id, str(report_data)))

    return patients

def extract_report_data_mindray_bc_700(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "Mindray_BC_700"
    report_data = {}
    patients = []
    for line in lines:

        if line.startswith('OBR'):
            if patientId and report_data:
                patients.append((machine_name, patientId, report_data))
                report_data = {}
                patientId = None
            patientId = line.split('|')[3].strip()
        elif line.startswith('OBX'):
            if line.split('|')[2] == 'IS':
                continue
            report_name = line.split('|')[3].split('^')[1]
            report_value = line.split('|')[5]
            report_data[report_name] = report_value

    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))

    return patients

def extract_report_data_mindray_bc_700_astm(data): 
    lines = data.split('\x02')
    machine_name = "BC_700"
    patientId = None
    report_data = {}
    patients = []

    for line in lines:
        if line.startswith('3O'):
            if len(line.split('|'))>=3:
                patientId = line.split('|')[2].strip()
        elif re.match(r'^[0-7]R\|',line):
            if len(line.split('|'))>=4:
                r_data = line.split('|')
                report_data[r_data[2].split('^')[1]] = r_data[3].strip()
    
    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))
    
    return patients

# Method for Accurex 
def extract_report_data_accurex(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "Accurex"
    report_data = {}
    patients = []
    for line in lines:
        if line.strip().startswith('P'):
            patientId = line.split('|')[3]
        elif line.strip().startswith('R'):
            test_name = line.split('|')[2]
            test_result = line.split('|')[8]
            report_data[test_name] = test_result

    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))

    return patients

# Method for AIA 360 Tosoh Machine
def extract_report_data_aia_360_tosoh(data):
    lines = data.strip().split('\x02')
    machine_name, patient_name, test_name, test_result = 'ACCESS', 'N/A', 'N/A', 'N/A'
    final_list = []
    for line in lines:
        if line.startswith('1H'):
            machine_name = line.split('|')[4]
        elif line.startswith('3O'):
            patient_name = line.split('|')[2]
        elif line.startswith('4R'):
            test_data = line.split('|')
            test_name = test_data[2].replace('^', '').rstrip('1')
            test_result = test_data[3].replace('>', '').replace('<', '')
    final_list.append((machine_name, patient_name, {test_name: test_result}))
    return final_list

# Method for EverLife Machine
def extract_report_data_everlife_dynacount_3d(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "everlife_dynacount"
    report_data = {}
    patients = []
    for line in lines:

        if line.startswith('PID'):
            if patientId and report_data:
                patients.append((machine_name, patientId, report_data))
                report_data = {}
                patientId = None
            patientId = line.split('|')[3].replace('^MR', '').replace('^', '')
        elif line.startswith('OBX'):
            if line.split('|')[2] == 'IS':
                continue
            report_name = line.split('|')[3].split('^')[1]
            report_value = line.split('|')[5]
            report_data[report_name] = report_value

    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))

    return patients

# Method for Urin Machine
def extract_report_data_urin_uriquikpro(data):
    lines = data.split('\n')
    
    formatted_data = []
    
    obx_data = ""
    
    for line in lines:
        if line.startswith("OBX"):
            if obx_data:
                formatted_data.append(obx_data.strip()) 
            obx_data = line  
        elif obx_data and line.strip(): 
            obx_data += "|" + line.strip()
        else:
            if obx_data:
                formatted_data.append(obx_data.strip()) 
                obx_data = "" 
            formatted_data.append(line)  
    if obx_data:
        formatted_data.append(obx_data.strip())

    patients = []
    if formatted_data:
        machine_name = "urin"
        patientId = None
        report_data = {}
        for line in formatted_data:

            if line.startswith('PID'):
                if patientId and report_data:
                    patients.append((machine_name, patientId, report_data))
                    report_data = {}
                    patientId = None
                patientId = line.split('|')[2].strip()
            elif line.startswith('OBX'):
                if line.split('|')[2] == 'IS':
                    continue
                report_name = line.split('|')[3]
                report_value = line.split('|')[5]
                report_data[report_name] = report_value

        if patientId and report_data:
            patients.append((machine_name, patientId, report_data))

        return patients
    else:
        return patients

def extract_report_data_u_120(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "U_120"
    report_data = {}
    patients = []
    for line in lines:
        if line.startswith(" No."):
            patientId = line.split()[1].strip()
        elif len(line.split()) == 3:
            report_data[line.split()[0]] = line.split()[2]
        elif len(line.split()) == 2:
            report_data[line.split()[0]] = line.split()[1]
    
    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))
    return patients

def extract_report_data_st_200(data):
    cleaned_text = re.sub(r'\x1b.', '', data)
    
    lines = cleaned_text.split('\n')
    machine_name = "ST_200"
    patientId = None
    report_data = {}
    patients = []
    
    for line in lines:
        line = line.strip()  
        if not line:
            continue  

        if line.replace('\x00','').startswith("Patient ID:"):
            pid = line.split(':')[1].strip()
            patientId = "DHL" + pid

        elif "=" in line:
            parts = line.replace('\x00','').split('=')
            if len(parts) >= 2:
                key = parts[0].strip()
                value = parts[1].split()[0].strip()
                report_data[key] = value
        
        elif line.startswith("Date:"):
            parts = line.replace('\x00','').split()
            if len(parts) >= 3:
                report_data["Date:"] = parts[-1]  
        elif "_" in line:
            report_data["_"] = "_"
    
    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))
    return patients

# Function to extract data from machine EM 200
def extract_report_data_em_200(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "EM_200"
    report_data = {}
    patients = []

    # Initialize variables to process R and C blocks
    current_r_line = ""
    concatenated_lines = []

    for i, line in enumerate(lines):
        line = line.strip()

        if line.startswith("P"):
            patientId = line.split("|")[5]

        elif line.startswith("R"):
            # If already processing an "R" block, finalize it
            if current_r_line:
                concatenated_lines.append(current_r_line)
            # Start a new "R" block
            current_r_line = line

        elif current_r_line and line.startswith("C"):
            # Finalize the current "R" block with "C"
            current_r_line += " " + line
            concatenated_lines.append(current_r_line)
            current_r_line = ""

        elif current_r_line:
            # Concatenate lines within an "R" block
            current_r_line += " " + line

    # Add any remaining "R" block
    if current_r_line:
        concatenated_lines.append(current_r_line)

    # Process concatenated lines to extract report data
    for line in concatenated_lines:
        if line.startswith("R"):
            test = line.split("|")
            testname = test[2].replace("^", "")
            testvalue = test[3]
            report_data[testname] = testvalue

    patients.append((machine_name, patientId, report_data))
    return patients


#function to extract data from URIT 50 machine
def extract_report_data_urit_50(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "U_120"
    report_data = {}
    patients = []
    for line in lines:
        if line.startswith("NO."):
            patientId = line.split()[0].strip().replace("NO.","")
            patientId_2 = str(int(patientId))
        elif len(line.split()) >= 3:
            report_data[line.split()[0]] = line.split()[2]
        elif len(line.split()) == 2:
            report_data[line.split()[0]] = line.split()[1].replace("-","")
    if patientId and report_data:
        patients.append((machine_name, "S" + patientId_2, report_data))

    return patients

def extract_report_data_coagulation_ca_51(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "CA_51"
    report_data = {}
    patients = []
    for line in lines:
        if line:
            line_data = line.split()
            patientId = "S" + str(int(line_data[8]))
            test_name = line_data[9]
            test_value = line_data[10]
            report_data[test_name] = test_value

            if patientId and report_data:
                patients.append((machine_name,patientId,report_data))
    return patients

def extract_report_data_qline_biotech_astira_cms(text):
    messages = text.strip().split("\n\n")
    machine_name = "QLINE_BIOTECH"
    final_list = []
    
    for message in messages:
        lines = message.splitlines()
        result_dict = {}
        obr_field = None
        
        for line in lines:
            if line.startswith('OBR'):
                fields = line.split('|')
                obr_field = fields[2] if len(fields) > 1 else ''
            elif line.startswith('OBX'):
                obx_fields = line.split('|')
                test_name = obx_fields[3].split('^')[0] if len(obx_fields) > 3 else ''
                test_result = obx_fields[4] if len(obx_fields) > 4 else ''
                result_dict[test_name] = test_result
        final_list.append((machine_name, obr_field, result_dict))
    return final_list

def extract_report_data_aggpe_cell_counter(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "Cell_Couter"
    report_data = {}
    patients = []
    for line in lines:

        if line.startswith('OBR'):
            if patientId and report_data:
                patients.append((machine_name, patientId, report_data))
                report_data = {}
                patientId = None
            patientId = line.split('|')[3].strip()
        elif line.startswith('OBX'):
            if line.split('|')[2] == 'IS':
                continue
            report_name = line.split('|')[3].split('^')[1]
            report_value = line.split('|')[5]
            report_data[report_name] = report_value

    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))

    return patients

# function to extract data from ichroma 2 machine
def extract_report_data_ichroma_2(data):
    lines = data.split('\n')
    list_of_records = []
    machine_name = "ICHROMA 2"
    for line in lines:
        if line:
            patient_id = line.split("|")[4]
            if patient_id:
                test_name = line.split("|")[7]
                test_value = line.split("|")[10][2:]
                if test_name and test_value:
                    list_of_records.append((machine_name, patient_id, {test_name: test_value}))

    return list_of_records

def extract_report_data_unikon_5(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "UNIKON_5"
    report_data = {}
    patients = []
    for line in lines:
        if line.startswith('OBR'):
            if patientId and report_data:
                patients.append((machine_name, patientId, report_data))
                report_data = {}
                patientId = None
            patientId = line.split('|')[3].strip()
        elif line.startswith('OBX'):
            if line.split('|')[2] == 'IS':
                continue
            report_name = line.split('|')[3].split('^')[1]
            report_value = line.split('|')[5]
            report_data[report_name] = report_value

    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))

    return patients

def extract_report_data_electra_pro_m(data):
    lines = data.split('\n')
    patientId = None
    machine_name = 'ELECTRA_PRO_M'
    patients = []
    result_dict = {}
    for line in lines:
        if line.startswith('O'):
            if patientId and result_dict:
                patients.append((machine_name, patientId, result_dict))
            # patients = []
                result_dict = {}
            patientId = line.split('|')[2].strip()
        elif line.startswith('R'):
            test_name = line.split('|')[2].split('^')
            test_name = test_name[-1]
            test_result = line.split('|')[3]
            result_dict[test_name] = test_result
    if patientId and result_dict:
        patients.append((machine_name, patientId, result_dict))
    return patients

#function to extract data from Hema_580 Machine
def extract_report_hema_580(data):
    machine_name = "Hema_580"
    final_list = []
    patient_id = None
    result_dict = {}
    lines = data.split('\n')
    cleaned_data = [entry.replace('\x02', '').replace('\x03', '').replace('\x05', '') for entry in lines]
    for line in cleaned_data:
        if line.startswith("3O"):
            patient_id=line.split("|")[2]
        elif re.match(r'^[0-7]R\|',line):
            test_name = line.split("|")[2].split("^")[3].strip()
            test_value = line.split("|")[3]
            if test_name and test_value:
                result_dict[test_name] = test_value
    final_list.append((machine_name, patient_id, result_dict))
    
    return final_list

def extract_report_data_erba_h_360(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "H360"
    report_data = {}
    patients = []
    formatted_data = []
    
    obx_data = ""
    
    for line in lines:
        if line.startswith("OBX"):
            if obx_data:
                formatted_data.append(obx_data.strip()) 
            obx_data = line  
        elif obx_data and line.strip(): 
            obx_data += "" + line.strip()
        else:
            if obx_data:
                formatted_data.append(obx_data.strip()) 
                obx_data = "" 
            formatted_data.append(line)  
    if obx_data:
        formatted_data.append(obx_data.strip())

    for line in formatted_data:
        if line.startswith('OBR'):
            # print(line)
            if patientId and report_data:
                patients.append((machine_name, patientId, report_data))
                report_data = {}
                patientId = None
            patientId = line.split('|')[5].replace('^', '').strip()
        elif line.startswith('OBX'):
            if line.split('|')[2] == 'IS':
                continue
            report_name = line.split('|')[3].split('^')[1]
            report_value = line.split('|')[5]
            report_data[report_name] = report_value

    if patientId and report_data:
        patients.append((machine_name, patientId, report_data))

    return patients


def extract_report_data_mispa_fab_120(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "FAB_120"
    report_data = {}
    patients = []
    formatted_data = []
    
    obx_data = ""
    
    for line in lines:
        if line.startswith("OBX"):
            if obx_data:
                formatted_data.append(obx_data.strip()) 
            obx_data = line  
        elif obx_data and line.strip(): 
            obx_data += "" + line.strip()
        else:
            if obx_data:
                formatted_data.append(obx_data.strip()) 
                obx_data = "" 
            formatted_data.append(line)  
    if obx_data:
        formatted_data.append(obx_data.strip())

    for line in formatted_data:
        if line.startswith('OBR'):
            # print(line)
            if patientId and report_data:
                patients.append((machine_name, patientId, str(report_data)))
                report_data = {}
                patientId = None
            patientId = line.split('|')[3].replace('^MR', '').replace('^', '')
        elif line.startswith('OBX'):
            if line.split('|')[2] == 'IS':
                continue
            report_name = line.split('|')[3].strip()
            report_value = line.split('|')[5]
            report_data[report_name] = report_value

    if patientId and report_data:
        patients.append((machine_name, "D"+ patientId, str(report_data)))

    return patients

def extract_report_data_xl_200(data):
    lines = data.split('\n')
    patientId = None
    machine_name = "XL_200"
    report_data = {}
    patients = []

    # Initialize variables to process R and C blocks
    current_r_line = ""
    concatenated_lines = []

    for i, line in enumerate(lines):
        line = line.strip()

        if line.startswith("P"):
            patientId = line.split("|")[5]

        elif line.startswith("R"):
            # If already processing an "R" block, finalize it
            if current_r_line:
                concatenated_lines.append(current_r_line)
            # Start a new "R" block
            current_r_line = line

        elif current_r_line and line.startswith("C"):
            # Finalize the current "R" block with "C"
            current_r_line += " " + line
            concatenated_lines.append(current_r_line)
            current_r_line = ""

        elif current_r_line:
            # Concatenate lines within an "R" block
            current_r_line += " " + line

    # Add any remaining "R" block
    if current_r_line:
        concatenated_lines.append(current_r_line)

    # Process concatenated lines to extract report data
    for line in concatenated_lines:
        if line.startswith("R"):
            test = line.split("|")
            testname = test[2].replace("^", "")
            testvalue = test[3]
            report_data[testname] = testvalue

    patients.append((machine_name, patientId, report_data))
    return patients

def merge_broken_lines(data):
    merged_lines = []
    try:
        lines = data.splitlines()

        for line in lines:
            line = line.strip()
            if merged_lines and not re.match(r'^[A-Z]\|\d+\|', line) and not re.match(r'^(OBX|MSH|PID|PV1|OBR)\|', line):
                merged_lines[-1] += line  # continuation of previous line
            else:
                merged_lines.append(line)
        return merged_lines
    except Exception as e:
        return merged_lines

def extract_data_from_bk_240(data):
    try:
        lines = merge_broken_lines(data)

        machine_name = 'BK_200'
        patient_id = None
        report_data = {}
        patients = []

        for line in lines:
            if line.startswith('OBR'):
                if patient_id and report_data:
                    patients.append((machine_name, patient_id, str(report_data)))
                    patient_id = None
                    report_data = {}

                patient_id = line.split('|')[2]
                if '-' in patient_id:
                    patient_id = patient_id.split('-')[0]

            elif line.startswith('OBX'):
                test_name = line.split('|')[4]
                test_result = line.split('|')[5]
                report_data[test_name] = test_result

        if patient_id and report_data:
            patients.append((machine_name, patient_id, str(report_data)))

        return patients
    except Exception as e:
        return []

def extract_report_data_elite_580(data):
    patients = []
    try:
        lines = merge_broken_lines(data)
        patientId = None
        machine_name = "ELITE_580"
        report_data = {}
        for line in lines:
            if line.startswith('OBR'):
                if patientId and report_data:
                    patients.append((machine_name, patientId, str(report_data)))
                    report_data = {}
                    patientId = None

                patientId = line.split('|')[3].strip()
            elif line.startswith('OBX'):
                if line.split('|')[2] == 'IS':
                    continue
                report_name = line.split('|')[3].split('^')[1]
                report_value = line.split('|')[5]
                report_data[report_name] = report_value

        if patientId and report_data:
            patients.append((machine_name, patientId, str(report_data)))

        return patients
    except Exception as e:
        return patients

def extract_data_from_vitek(data):
    try:
        test_data = remove_control_characters(data)

        machine_name = 'VITEK_2'
        patient_id = None
        result_dict = {}
        results = []

        lines = test_data.split('|')

        test_name_list = []
        test_result_list = []

        for line in lines:
            if line.startswith('pi'):
                if patient_id and result_dict:
                    results.append((machine_name, patient_id, str(result_dict))) 

                patient_id = re.sub(r'[piPI]', '', line).strip()

            elif line.startswith('a2'):
                if 'a2' in line:
                    test_name = line.replace('a2','').strip()
                    test_name_list.append(test_name)

            elif line.startswith('a3'):
                if 'a3' in line:
                    test_result = line.replace('a3','').strip()
                    test_result_list.append(test_result)

        result_dict = dict(zip(test_name_list, test_result_list))

        if patient_id and result_dict:
            results.append((machine_name, patient_id, str(result_dict))) 

        return results
    except Exception as e:
        return []

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
        return None

def merge_broken_lines_for_gem(text):
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
        return []

def extract_report_data_from_gem_premier_3000(data):
    results = []
    try:
        machine_name = 'GEM_PREMIER_3000'
        patient_id = None
        result_dict = {}
        formated_text = remove_control_characters(data)

        merged_lines = merge_broken_lines_for_gem(formated_text)

        for line in merged_lines:
            if line.startswith('O'):

                if patient_id and result_dict:
                    results.append((machine_name, patient_id, str(result_dict)))

                patient_id = line.split('|')[3]

            elif line.startswith('R'):
                test_name = line.split('|')[2].replace('^^^','').strip()
                if '\x02' in test_name:
                    test_name = test_name.replace('\x02','').strip()

                test_value = line.split('|')[3]
                if '\x02' in test_value:
                    test_value = test_value.replace('\x02','').strip()

                result_dict[test_name] = test_value
        
        if patient_id and result_dict:
            results.append((machine_name, patient_id, str(result_dict)))

        return results

    except Exception as e:
        return results
    
def extract_report_data_hemax_53(data):
    patients = []
    try:
        lines = data.split('\n')
        patientId = None
        machine_name = "HEMAX_53"
        report_data = {}
        for line in lines:

            if line.startswith('PID'):
                if patientId and report_data:
                    patients.append((machine_name, patientId, str(report_data)))
                    report_data = {}
                    patientId = None
                patientId = line.split('|')[2].strip()
                if '-' in patientId:
                    patientId = patientId.split('-')[0]
            elif line.startswith('OBX'):
                if line.split('|')[2] == 'IS':
                    continue
                report_name = line.split('|')[4].strip()
                report_value = line.split('|')[6]
                report_data[report_name] = report_value

        if patientId and report_data:
            patients.append((machine_name, patientId, str(report_data)))

        return patients
    except Exception as e:
        return patients

def is_numeric(val):
    try:
        float(val)
        return True
    except ValueError:
        return False

def extract_data_from_hemax_33(data):
    results = []
    try:
        machine_name = 'HEMAX_33_UYO'
        patient_id = None
        result_dict = {}
 
        list_data = data.split(',')
        i = 16
        if list_data:
            patient_id = list_data[1]
 
            while i < len(list_data):
                if i+1 < len(list_data):
                    test_name = list_data[i]
                    test_result = list_data[i+1]
                    if test_name and test_result and is_numeric(test_name) == False:
                        if ' ' in test_result:
                            test_result = test_result.split()[0]
                        result_dict[test_name] = test_result
                    i += 3
 
        if patient_id and result_dict:
            results.append((machine_name, patient_id, str(result_dict)))
        return results
 
    except Exception as e:
        return results
    
def merge_broken_lines_for_bk_200(data):
    merged_lines = []
    try:
        lines = data.splitlines()
 
        for line in lines:
            line = line.strip()
            if merged_lines and not re.match(r'^[A-Z]\|\d+\|', line) and not re.match(r'^(OBX|MSH|PID|PV1|OBR)\|', line):
                merged_lines[-1] += line  # continuation of previous line
            else:
                merged_lines.append(line)
        return merged_lines
    except Exception as e:
        return merged_lines
 
def extract_data_from_bk_200(data):
    patients = []
    try:
        lines = merge_broken_lines_for_bk_200(data)
 
        machine_name = 'BK_200_UYO'
        patient_id = None
        report_data = {}
 
        for line in lines:
            if line.startswith('OBR'):
                if patient_id and report_data:
                    patients.append((machine_name, patient_id, str(report_data)))
                    patient_id = None
                    report_data = {}
 
                patient_id = line.split('|')[2]
                if '-' in patient_id:
                    patient_id = patient_id.split('-')[0]
 
            elif line.startswith('OBX'):
                test_name = line.split('|')[4]
                test_result = line.split('|')[5]
                report_data[test_name] = test_result
 
        if patient_id and report_data:
            patients.append((machine_name, patient_id, str(report_data)))
 
        return patients
    except Exception as e:
        return patients
# Method for process all file in given folder
def process_all_files(folder_path):
    try:
        final_results = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            text_data = read_file(file_path)
            if not text_data:
                continue
            extractors = {
                'xn_330_': extract_report_data_xn_330,
                'xp_100_': extract_report_data_xp_100,
                'xn_350_': extract_report_data_xn_350,
                'xn_550_': extract_report_data_xn_550,
                'xn_1000_': extract_report_data_xn_1000,
                'e_411_': extract_report_data_e_411,
                'c_111_': extract_report_data_c_111,
                'c_311_': extract_report_data_c_311,
                'access_2_': extract_report_data_access_2,
                'au_480_': extract_report_data_au_480,
                'maglumi_800_' : extract_report_data_maglumi,
                'celltak_': extract_report_data_celltak,
                'cell_tak_6500_': extract_report_data_cell_tak_6500,
                'nx_600_': extract_report_data_nx_600,
                'nx_700_': extract_report_data_nx_700,
                'fiameter_': extract_report_data_fiameter,
                'accre_8_': extract_report_data_accre_8,
                'mispa_nano_': extract_report_data_mispa_nano,
                'bc_5130_': extract_report_data_mindray_bc_5130,
                'bc_5150_': extract_report_data_mindray_bc_5150,
                'bc_700_': extract_report_data_mindray_bc_700,
                'bc_700': extract_report_data_mindray_bc_700_astm,
                'cl_900_i_': extract_report_data_mindray_cl_900_i,
                'bs_240_': extract_report_data_mindray_bs_240,
                'accurex_' : extract_report_data_accurex,
                'electrolyzer_analyzer_gastat_': extract_report_data_electrolyzer_analyzer_gastat,
                'aia_360_': extract_report_data_aia_360_tosoh,
                'h_500': extract_report_data_horiba_h_500,
                'everlife_dynacount_3d_': extract_report_data_everlife_dynacount_3d,
                'urin_uriquikpro_':extract_report_data_urin_uriquikpro,
                'u_120_':extract_report_data_u_120,
                'st_200_': extract_report_data_st_200,
                'urit_50': extract_report_data_urit_50,
                'em_200': extract_report_data_em_200,
                'h_360_': extract_report_data_erba_h_360,
                'ca_51': extract_report_data_coagulation_ca_51,
                'qline_biotech': extract_report_data_qline_biotech_astira_cms,
                'aggappe_cell_counter': extract_report_data_aggpe_cell_counter,
                'ichroma_2_': extract_report_data_ichroma_2,
                'unikon_5_': extract_report_data_unikon_5,
                'electra_pro_m_': extract_report_data_electra_pro_m,
                'hema_580_': extract_report_hema_580,
                'mispa_fab_120_': extract_report_data_mispa_fab_120,
                'xl_200_': extract_report_data_xl_200,
                'bk_240_': extract_data_from_bk_240,
                'bk_200_': extract_data_from_bk_200,
                'hemax_33_': extract_data_from_hemax_33,
                'hemax_53_': extract_report_data_hemax_53,
                'elite_580_': extract_report_data_elite_580,
                'vitek_': extract_data_from_vitek,
                'gem_premier_3000_': extract_report_data_from_gem_premier_3000
            }
            extractor = next((ext for prefix, ext in extractors.items() if filename.startswith(prefix)), None)
            if extractor:
                results = extractor(text_data)
                if isinstance(results, list):
                    for result in results:
                        if send_to_mysql(result):
                            try:
                                # os.remove(file_path)
                                # file_path = None
                                pass
                            except Exception as e:
                                pass
                        final_results.append(result)
                else:
                    try:
                        if file_path:
                            # os.remove(file_path)
                            # file_path = None
                            pass
                    except Exception as e:
                        pass
            else:
                try:
                    if file_path:
                        # os.remove(file_path)
                        # file_path = None
                        pass
                except Exception as e:
                    pass
        return final_results
    except Exception as e:
        print(f"Exception Occur :- {e}")

while True:
    all_results = process_all_files(folder_path)
    for result in all_results:
        print(f"Data Inserted :- {result}")
    time.sleep(2)


