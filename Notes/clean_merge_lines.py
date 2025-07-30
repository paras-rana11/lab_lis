import os
os.chdir(".")

def clean_and_merge_broken_lines(data):

    control_chars = ['\x02', '\x03', '\x04', '\x05', '\x06', '\x15', '\x17', '\x1c', '\x0b']
    for sym in control_chars:
        data = data.replace(sym, '')

    lines = data.replace('\r', '').split('\n')

    cleaned_lines = []
    current_line = ""
    # change prefix according the data
    known_prefixes = ('MSH|', 'PID|', 'OBR|', 'OBX|', 'DSC|')

    for line in lines:
        line = line.strip()

        if line.startswith(known_prefixes):
            if current_line:
                cleaned_lines.append(current_line)
            current_line = line
        else:
            current_line += " " + line

    # Add the last segment
    if current_line:
        cleaned_lines.append(current_line)

    return cleaned_lines


file_path = 'C:\\All\\LIS\\lis4 (merge broken)\\fincare1.txt'

with open(file_path, 'r') as f:
    data = f.read()
    
result = clean_and_merge_broken_lines(data)

print("\n====> Final Result: ")
for r in result:
    print("\nR: ", r)
    
    
    
data = """
MSH|^~\&|FineCarePlus|飞测ⅡPlus^00:21:9B:1A:E0:4A^FS-113|POCT|POCT_SERVER^^PC|20240831111807||ORU^R01^ORU_R01|202408300001|P|2.4||||0|CHN|UTF8
PID|202408300001||||jayalakshmi||19660831|F
OBR|202408300001|F2071A20E|1||||20240830183832|20240830183832|||||||Whole blood|sridhar ramadasu 
OBX|202408300001|NM||HbA1c  eGA(ADA)   HBA1C(IFCC)|12.6 %  314.9 md/dl  114.2 mmol/mol↑|%|0.0-6.5||||||12.6|20240830183832
DSC|1|F


MSH|^~\&|FineCarePlus|飞测ⅡPlus^00:21:9B:1A:E0:4A^FS-113|POCT|POCT_SERVER^^PC|20240831111826||ORU^R01^ORU_R01|202408210002|P|2.4||||0|CHN|UTF8
PID|202408210002||||susheela||19680831|F
OBR|202408210002|F2071A20E|2||||20240821132159|20240821132159|||||||Whole blood|sridhar ramadasu 

OBX|202408210002|NM||HbA1c  eGA(ADA)   HBA1C(IFCC)|1.1 %  2.1 md/dl  3.1 mmol/mol|%|0.0-6.5||||||5.3|20240821132159
OBX|202408210002|NM||HbA1c  (ADA)
(IFCC)  |1.2 %  
2.2 md/dl  3.2 mmol/mol|%|0.0-6.5||||||5.3|20240821132159
DSC|1|F


"""

