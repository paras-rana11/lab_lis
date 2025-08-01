📄 Program Overview: Machine Data Parser & MySQL Inserter

🔧 Purpose:  
This program monitors a local folder for result files generated by lab analyzers (like Hemax 330, Sysmex XP-100, etc.), extracts patient test results, and saves them to a MySQL database. It supports file parsing, JSON formatting, and robust error handling.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
🔁 Execution Flow:

1. Set DB credentials and folder path
2. Loop indefinitely:
   - List all files in the input folder
   - For each file:
     - Detect analyzer by filename prefix
     - Parse test data using correct extractor
     - Format data into [machineName, patientId, testData]
     - Insert into MySQL via prepared statement
     - Optionally delete processed file
3. Sleep 2 seconds and repeat

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
🔧 Key Classes & Functions:

✅ get_connection()  
• Establishes connection to MySQL database  
• Uses credentials defined at top of script

✅ send_to_mysql(data)  
• Accepts [machineName, patientId, testDataDict]  
• Converts to JSON and inserts into machineData table  
• Logs error if DB connection or insert fails

✅ extract_report_data_<machine>()  
• Custom extractor for each analyzer  
• Extracts patient ID and test data from text  
• Returns a list of [machine, patient_id, test_dict]  
• Examples:
  - extract_report_data_xn_330()
  - extract_report_data_bc_5150()

✅ process_all_files(folder_path)  
• Main parser logic  
• Scans for files, detects machine type, extracts and inserts  
• Skips or logs errors gracefully  
• Supports file cleanup after insertion

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
📦 Example File Handling Flow:

| Filename Prefix | Machine       | Handler Function               |
|-----------------|---------------|--------------------------------|
| xn_330_         | Sysmex XN-330 | extract_report_data_xn_330()  |
| bc_5150_        | Mindray BC-5150| extract_report_data_bc_5150() |
| hemax_330_      | Hemax 330     | extract_report_data_hemax_330()|

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
🗃️ MySQL Table Used:

machineData  
| Column      | Type     | Description                      |
|-------------|----------|----------------------------------|
| machineName | VARCHAR  | Name/ID of the analyzer          |
| patientId   | VARCHAR  | Unique patient or sample ID      |
| test        | JSON     | Test name/value pairs in JSON    |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
📁 Default Paths:

| Purpose          | Path                                                                 |
|------------------|----------------------------------------------------------------------|
| Report Folder    | /home/.../attachments/ (Set via folder_path)                        |
| Processed Output | Inserted into MySQL only (optionally remove files after processing) |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
📬 Email Alert Setup:
(Optional – implement in send_mail_or_logging() if needed)

| Field       | Description                           |
|-------------|----------------------------------------|
| FROM_EMAIL  | Your sender email                      |
| TO_EMAIL    | Alert destination                      |
| PASSWORD    | App password / SMTP pass               |
| SMTP Server | smtp.gmail.com + TLS (port 587)        |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
🛠️ Setup Instructions:

1. Install required package:
   pip install mysql-connector-python

2. Update these values in the script:
   - my_host, my_user, my_pass, my_db
   - folder_path

3. Run the script:
   python machine_data_parser.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
📌 Debug Tips:

• Use print(repr(text_data)) to inspect raw file content  
• Enable logging to record failures  
• Use print(result) to inspect parsed JSON data before DB insert  
• Uncomment os.remove() to clean up processed files  

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━