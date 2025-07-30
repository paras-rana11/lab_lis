📡 HL7 vs ASTM Format Cheat Sheet (For Lab Devices)
---------------------------------------------------

🔷 ASTM Protocol

Code         | Socho jaise...               | Matlab
------------ | ---------------------------- | ------------------------
\x05 (ENQ)    | Machine knock kar rahi hai   | “Bhai, kuch bhejna hai”
\x06 (ACK)    | Aap gate khol rahe ho        | “Bhej do”
\x02 (STX)    | Data ki shuruat              | “Ab main likh raha hoon”
\x03 (ETX)    | Data ka end                  | “Line khatam”
\x04 (EOT)    | Machine goodbye keh rahi hai | “Mera kaam ho gaya”
\x0A (LF)     | New line                     | “Ek aur line aa gayi”

🔹 ASTM Format:
- Starts with:
    1H|\^&|||...
    or
    \x02 1H|\^&|||...

- Segments include:
    1H, 2P, 3O, 4R, L|1|N

- Delimiters:
    Pipe (|), Backslash (\), Caret (^)

- Control Characters Used:
    \x02 (STX): Start of data
    \x03 (ETX): End of data
    \x0D (CR): Segment end
    \x0A (LF): New line

=> If message starts with 1H| or control characters like \x02, it's ASTM.


🟢 HL7 Protocol

Code           | Socho jaise...                 | Matlab
-------------- | ------------------------------ | -------------------------------------
\x0B (VT)       | Machine bol rahi hai: "Start"  | HL7 message ki shuruat (Start Block)
\x1C (FS)       | Machine bol rahi hai: "Done"   | HL7 message ka end (End Block)
\x0D (CR)       | Enter dabaya                   | Line ka end (Segment separator)
\x0B...\x1C\x0D | Full message                   | Message from start to end

🔹 HL7 Format:
- Starts with: MSH|
- Common segments:
    MSH, PID, OBR, OBX
- Delimiters:
    Pipe (|), Caret (^), Tilde (~), Ampersand (&)

Example:
MSH|^~\&|AnalyzerName|DeviceID|...
PID|...
OBR|...
OBX|...

=> If message starts with MSH|, it's HL7.


📊 Protocol Comparison Table

Format   | Starts With        | Common Segments           | Used In
-------- | ------------------ | --------------------------| --------------------------------------------
HL7      | MSH|               | PID, OBR, OBX, MSH        | Hospital EMRs, HL7 Routers
ASTM     | 1H| or \x02        | 1H, 2P, 3O, 4R, L|1|N      | Lab analyzers (POCT, hematology, etc.)


🛠 How to Identify Format from a File

✔ Open the .txt or serial log file
✔ Check for:
   - MSH|         => HL7
   - 1H| or \x02  => ASTM

✔ In most devices, you can choose HL7 or ASTM from the settings menu.

✔ Refer to device manual or contact support if unsure.
