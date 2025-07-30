

Main Process (app start):
├── start_receiving_data(connection_access_2)
│   ├── 🧹 remove_old_logs_from_log_file()
│   │     └── Every 60 min: deletes `.log` files older than 1 day from log folder
│   └── 🔁 continuous_receiving_data()
│         ├── ⬅️ Reads from serial port using connection.read() (1 byte)
│         ├── 📂 Creates a result file: C:/ASTM/root/report_file/access_2_<timestamp>.txt
│         ├── 📥 Receives test result bytes (starts on b'\x05' [ENQ])
│         ├── ✍️ Writes full data to file
│         └── 🛑 When it sees b'\x04' (EOT), closes the file
│
└── 🌐 uvicorn.run(app, host, port) ← starts FastAPI server
     └── @app.post("/create_case/COM1")
          ├── ✅ Accepts request: CreateCaseRequest (JSON body)
          └── 🎯 background_tasks.add_task(...)
                  └── retry_api_call(...)
                        ├── 🧠 Calls: create_case_in_machine()
                        │     ├── 🔁 ENQ sent to machine
                        │     ├── ✅ Waits for ACK
                        │     ├── ✍️ Sends H, P, O, L ASTM frames (test info)
                        │     └── ✅ Logs response status
                        └── ❌ Retries if error (max 3 attempts)

