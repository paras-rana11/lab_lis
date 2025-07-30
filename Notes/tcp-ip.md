Great — let's break this into two key parts:

---

## ✅ **1. Code Changes Based on Machine Role (TCP/IP Socket)**

### 🅰️ **Scenario A: Machine is TCP/IP Server (Machine is host)**

* Your **code acts as a client** (connects to machine IP and port).
* **You must know the machine’s IP and Port**.

🔧 **Your Code (Client)**:

```python
import socket

HOST = '192.168.1.100'  # Machine IP
PORT = 5000             # Machine port

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))  # Connect to machine
    while True:
        data = s.recv(1024)
        if not data:
            break
        print("Received:", data.decode())
```

---

### 🅱️ **Scenario B: Machine is TCP/IP Client (Machine connects to you)**

* Your **code acts as server** (listens on a port).
* **You must provide your IP and Port to machine’s configuration**.

🔧 **Your Code (Server)**:

```python
import socket

HOST = '0.0.0.0'   # Listen on all interfaces
PORT = 5000        # Port where machine will connect

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print("Received:", data.decode())
```

---

## ✅ **2. How to Know Machine is Host or Client?**

Check using any of these ways:

---

### ✅ **A. Device Manual / Integration Guide**

* 📘 Most devices clearly say:

  * *“Machine acts as TCP Server on port 5001”* → You must write client code.
  * *“Machine connects to LIS IP”* → You write server code.

---

### ✅ **B. Machine Configuration Interface**

Check inside device network settings:

* If it asks for **"Server IP & Port"** → Machine will **connect** → It's a **client**.
* If it shows its own IP and Port to receive → It will **listen** → It's a **server**.

---

### ✅ **C. Network Behavior Test**

Try using command-line tools:

```bash
# Test if machine is listening on port
telnet <MACHINE_IP> <PORT>
```

* If connected → It’s a server.
* If connection refused → Probably a client (needs to be pointed to your IP).

---

### ✅ **D. Vendor Support**

Ask the vendor:

* "Does your device act as TCP/IP server or client?"
* "What IP & Port does it use or need?"

---

## 🔁 Summary Table

| Machine Role      | Your Role in Code | Code Type                    | Who Initiates |
| ----------------- | ----------------- | ---------------------------- | ------------- |
| TCP Server (host) | TCP Client        | `socket.connect()`           | Your code     |
| TCP Client        | TCP Server        | `socket.bind()` & `accept()` | Machine       |

---


