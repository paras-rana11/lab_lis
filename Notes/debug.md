Sure! Here's your complete, polished **Markdown Quick Guide** to Python logging levels — explained simply with chart, examples, and memory tips:

---

## ✅ Python Logging Levels — Quick Guide

| Level      | Priority | Used For                      | Emoji 💡 Trick   |
| ---------- | -------- | ----------------------------- | ---------------- |
| `DEBUG`    | 10       | Internal steps for developers | 🔍 Deep dive     |
| `INFO`     | 20       | Routine app behavior          | ℹ️ Everything OK |
| `WARNING`  | 30       | Something *might* go wrong    | ⚠️ Heads-up      |
| `ERROR`    | 40       | An issue that broke something | ❌ Needs fixing   |
| `CRITICAL` | 50       | Whole system failure          | 🚨 Emergency!    |

---

### 🧠 Easy Mnemonic to Remember

> **“Don’t Ignore Warnings, Errors Crash!”**
> `DEBUG → INFO → WARNING → ERROR → CRITICAL`

---

### 🛠 Common Use Cases

| Situation                               | Log Level  |
| --------------------------------------- | ---------- |
| Sending ASTM message to analyzer        | `DEBUG`    |
| Machine connection started successfully | `INFO`     |
| Result delayed more than 2 minutes      | `WARNING`  |
| Machine disconnected unexpectedly       | `ERROR`    |
| Analyzer COM port permanently failed    | `CRITICAL` |

---

## 📁 Log File Handler Behavior (VERY IMPORTANT)

When you set:

```python
handler.setLevel(logging.INFO)
```

It means **"Only allow INFO and above"** (WARNING, ERROR, etc.), but **not DEBUG**.

| Handler Level | What It Captures                                 |
| ------------- | ------------------------------------------------ |
| `DEBUG`       | ✅ DEBUG, INFO, WARNING, ERROR, CRITICAL          |
| `INFO`        | ❌ (Skips DEBUG) ✅ INFO and above                 |
| `WARNING`     | ❌ (Skips DEBUG, INFO) ✅ WARNING and above        |
| `ERROR`       | ❌ (Skips DEBUG, INFO, WARNING) ✅ ERROR, CRITICAL |

---

## 📝 Summary Chart (Handler Behavior)

| Handler Level     | Captures...                                     |
| ----------------- | ----------------------------------------------- |
| `DEBUG` handler   | ✅ Everything                                    |
| `INFO` handler    | ✅ INFO → CRITICAL <br> ❌ Skips DEBUG            |
| `WARNING` handler | ✅ WARNING → CRITICAL <br> ❌ Skips DEBUG, INFO   |
| `ERROR` handler   | ✅ ERROR → CRITICAL <br> ❌ Skips all below ERROR |
| `CRITICAL` only   | ✅ CRITICAL only                                 |

---

### ✅ Tip:

* Use **DEBUG** log file if you want to capture everything.
* Use **INFO** log file for normal logs (but exclude debug).
* Use **ERROR** log file to track only failures and alerts.

---

Let me know if you want a ready-made function to set up these handlers with file names like `debug.log`, `info.log`, `error.log`.
