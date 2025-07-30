Great question, Paras! Let's break this into **two parts** — one for the **Main API (LIS)** and one for the **Machine API**. I’ll show:

* **Which files get created**
* **When they are created**
* **What data is saved**
* **What format it's saved in**
* **Why (purpose)**
* With **examples**

---

## 🧠 Part 1: **Main API (LIS Side)** — `case_receive_api.py` type code

### 📁 Files Created:

| File Name                     | Format | When It’s Created             | What It Saves                             | Why / Purpose                   |
| ----------------------------- | ------ | ----------------------------- | ----------------------------------------- | ------------------------------- |
| `case_payload.json`           | JSON   | When LIS receives a case      | Full raw case payload                     | For debugging/logging raw input |
| `case_creation_api.json`      | JSON   | After sending case to machine | Sent case + machine response (if success) | Tracking sent cases             |
| `case_creation_api_fail.json` | JSON   | If machine API call fails     | Failed payload, error message             | For retry/error tracing         |

---

### ✅ Example Flow (Main API):

#### Request comes from LIMS:

```json
{
  "patient_id": "P001",
  "sample_type": "serum",
  "test_ids": "GLU,CRE"
}
```

### → File: `case_payload.json`

```json
{
  "timestamp": "2025-07-28 11:30:25",
  "payload": {
    "patient_id": "P001",
    "sample_type": "serum",
    "test_ids": "GLU,CRE"
  }
}
```

### → If success: `case_creation_api.json`

```json
{
  "machine": "access_2",
  "status": "success",
  "case_id": "A2-P001-00001"
}
```

### → If fail: `case_creation_api_fail.json`

```json
{
  "machine": "access_2",
  "status": "fail",
  "error": "Timeout",
  "payload": { ... }
}
```

---

## ⚙️ Part 2: **Machine API** (Machine-specific FastAPI, e.g., `access_2_api.py`)

### 📁 Files Created:

| File Name                          | Format     | When It’s Created                | What It Saves                     | Why / Purpose     |
| ---------------------------------- | ---------- | -------------------------------- | --------------------------------- | ----------------- |
| `complate_case_for_access_2.json`  | JSON       | After result is parsed           | Marks case as complete/incomplete | Final case status |
| `access_2_2025-07-28-12-00-45.txt` | Plain text | When receiving ASTM from machine | Raw ASTM data from COM port       | For raw storage   |
| `logging_for_access_2.log`         | Text log   | During full lifecycle            | Normal logs: sending, ACK, status | Monitoring        |
| `logging_for_access_2_error.log`   | Text log   | When errors happen               | Error tracebacks, failed records  | Debugging         |

---

### ✅ Example Flow (Machine API):

#### Machine receives ASTM frame like:

```
\x021H|\^&|||ACCESS2^1|||||host|20250728113025\x0341\x0D\x0A
```

### → File: `access_2_2025-07-28-12-00-45.txt`

```text
\x021H|\^&|||ACCESS2^1|||||host|20250728113025\x0341\x0D\x0A
\x021P|1||P001||DOE^JOHN||...\x03A9\x0D\x0A
```

### → After parsing result → `complate_case_for_access_2.json`

```json
{
  "case_id": "A2-P001-00001",
  "status": "completed",
  "result": {
    "GLU": "105",
    "CRE": "0.8"
  }
}
```

### → Logging (`logging_for_access_2.log`)

```
[2025-07-28 12:00:50] Sending case A2-P001-00001 to Access 2
[2025-07-28 12:00:52] Received ACK from analyzer
```

### → If error → `logging_for_access_2_error.log`

```
[2025-07-28 12:01:00] ERROR: Checksum mismatch at frame 2
```

---

## 🔄 File Opening & Closing

* All `.json` and `.txt` files are opened using Python `with open(...)` so they close automatically after writing.
* `.log` files are usually open via Python `logging` module — these stay open or append in background.
* Result `.txt` (ASTM) is opened **on each case** and closed after complete data is received.

---

## 🧪 Summary Table (ALL FILES)

| Code Side   | File                              | Format    | Purpose                 | Example Event                        |
| ----------- | --------------------------------- | --------- | ----------------------- | ------------------------------------ |
| Main API    | `case_payload.json`               | JSON      | Log original payload    | LIMS sends a case                    |
| Main API    | `case_creation_api.json`          | JSON      | Log success response    | Machine API accepts case             |
| Main API    | `case_creation_api_fail.json`     | JSON      | Log failure             | Machine API times out                |
| Machine API | `access_2_*.txt`                  | ASTM text | Store raw analyzer data | Result comes in                      |
| Machine API | `complate_case_for_access_2.json` | JSON      | Store completed case    | Parser converts raw → result         |
| Machine API | `logging_for_access_2.log`        | Text log  | Track flow              | Case sent, ACK received              |
| Machine API | `logging_for_access_2_error.log`  | Text log  | Debugging               | If invalid frame / checksum mismatch |

---

If you want, I can give you the **code lines** where these files are created and written inside both the LIS and Machine code too.

Shall I include that?
