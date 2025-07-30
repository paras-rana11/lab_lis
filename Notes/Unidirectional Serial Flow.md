
# 📄 Program Overview:  Serial Communication Logger

🔧 Purpose:
This program connects to a hematology analyzer (e.g., Hemax 330), listens to the serial port byte-by-byte, writes results to `.txt` files, and logs all operations. It supports automatic file creation, error handling, and log cleanup.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔁 Execution Flow:
1. Setup loggers
2. Establish serial connection
3. Start background thread to clean old log entries
4. Main loop:
   - Read one byte at a time
   - Check control bytes:
     • '\x05' → Start transmission
     • '\x0a' → New line / record
     • '\x04' → End transmission
   - Write data to report file
   - Log and handle exceptions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 Key Classes & Functions:

✅ MachineConnectionSerial:
- Handles all serial port communication:
1. __init__(): Initializes COM port and machine name
    • Handles serial port (connect, read, write)
2. get_connection(): Establishes connection using pyserial
3. read(): Reads 1 byte from serial
4. write(): Sends a byte back to machine
5. get_filename(): Generates a file path with timestamp
    • Creates new filenames, Example: (MACHINE_NAME)_(current_timestamp).txt
6. cleanup() / close_connection(): Closes serial safely
📌 Usage: This class is instantiated as CONNECTION_MACHINE_OBJECT



✅ communicate_with_machine(connection):
• Continuously reads data
• Listens for special control bytes:
   - '\x05' (ENQ): Start of file, send ACK, begin saving
   - '\x0a' (LF): Newline; write line to file
   - '\x04' (EOT): Close file, finalize write
• All actions inside try-except blocks for safety

✅ send_mail_or_logging(message, error):
• Logs error and optionally sends email alert

✅ setup_loggers():
• Logs info and errors in:
  - logging_for_machine.log
  - logging_for_machine_error.log

✅ remove_old_logs_from_log_file():
• Background thread
• Removes logs older than 10 days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Data Byte Flow Summary:

| Byte       | Meaning                  | Action Taken                             |
|------------|--------------------------|------------------------------------------|
| b'\x05'    | ENQ (Start)              | Start new file, send ACK, log start      |
| b'\x0a'    | LF (New Line)            | Write buffer to file, clear buffer       |
| b'\x04'    | EOT (End of Transmission)| Final write, close file, log done       |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Important Notes:
• File content is built line-by-line using `byte_array`
• Each line is flushed after a newline (`\x0a`)
• File is closed after `\x04` byte
• If exception occurs at any step, it is logged and optionally emailed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 Default File Paths:
• Log folder: C:\ASTM\root\log_file\
• Report folder: C:\ASTM\root\reports\ (based on current drive)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📬 Email Setup (for error alerts):
• Set in main code:
  - FROM_EMAIL = your email
  - PASSWORD = app password or SMTP
  - TO_EMAIL = your destination
• Uses smtplib with Gmail

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛠️ Setup Instructions:
• Install pyserial if not already:
    pip install pyserial
• Ensure machine is connected to correct COM port
• Run program via Python: 
    python your_script.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 Debug Tips:
• Print `repr(byte)` to see exact byte value
• Add `print(cur_file)` to confirm file paths
• Check logs for timestamped errors
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
