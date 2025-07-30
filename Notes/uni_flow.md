🟢 Main Process Starts (Python __main__)
├── 📦 Initialize MachineConnectionSerial (COM3, machine_name)
│     └── Try get_connection()
│           └── serial.Serial(port=COM3)
│           └── connection_object now active
│
├── 🧹 Background Thread: remove_old_logs_from_log_file()
│     └── Every 24 hrs → deletes old `.log` lines (>10 days)
│
└── 🔁 Infinite While Loop:
      ├── Check connection status
      ├── If not connected → retry get_connection()
      ├── 🔁 Call communicate_with_machine(connection)
      │     └── Loop:
      │           ├── Read 1 byte from COM3
      │           ├── If byte == ENQ (0x05):
      │           │     ├── Start new file → C:/ASTM/root/report_file/<timestamp>.txt
      │           │     └── Write 1st byte and send ACK (0x06)
      │           ├── If byte == LF (0x0A):
      │           │     ├── Write accumulated data to file
      │           │     └── Send ACK (0x06)
      │           ├── If byte == EOT (0x04):
      │           │     ├── Final write + close file
      │           │     └── Log file closed
      │           └── Else: Keep reading
      │
      └── Wait 5s, repeat


