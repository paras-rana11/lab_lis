######################################################################################################################

# pip install mysql-connector-python

# Note :-
    # In Accurex machine only use db script because machine automatic save report file in local computer so no need to run data get script.
    # directly run db script and save data in main db.

######################################################################################################################

import json
import os
import time
import mysql.connector
from mysql.connector import Error

# Configuration
my_host = '192.168.4.197'
my_user = 'root'
my_pass = 'root'
my_db = 'lis'

folder_path = 'C:\\Program Files\\LIS'


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

# Method for process all file in given folder
def process_all_files(folder_path):
    final_results = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith('astm'):
            new_filename = filename.replace('.astm', '.txt')
            new_file_path = os.path.join(folder_path, new_filename)
            os.rename(file_path, new_file_path)
            text_data = read_file(new_file_path)
        else:
            text_data = read_file(file_path)
        if not text_data:
            continue
        extractors = {
            'txt' : extract_report_data_accurex
        }
        extractor = next((ext for prefix, ext in extractors.items() if filename.endswith(prefix)), None)
        if extractor:
            results = extractor(text_data)
            if isinstance(results, list):
                for result in results:
                    if send_to_mysql(result):
                        try:
                            os.remove(file_path)
                            pass
                        except Exception as e:
                            pass
                    final_results.append(result)
        else:
            pass
    return final_results

while True:
    all_results = process_all_files(folder_path)
    for result in all_results:
        print(f"Data Inserted :- {result}")
    time.sleep(2)


