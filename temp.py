# e = b'PID|12345|PatientName|\xe0\xa4\xaa\xe0\xa4\xb0\xe0\xa5\x80\xe0\xa4\x95\xe0\xa5\x8d\xe0\xa4\xb7\xe0\xa4\xbe' 

# print(e.decode('utf-8'))

# byte_array = []

# byte = b'\x02'  

# byte_array.append(chr(ord(byte)))

# print(byte_array)

# print(ord(byte))

# print(chr(65))


# test_client_simulator.py
# import socket
# import time

# HOST = '127.0.0.1'  # Localhost for testing
# PORT = 5150

# dummy_data = [
#     b'\x05',
#     b'1H|\^&|||Analyzer^^|||||||P|1\r',
#     b'P|1||123456||Doe^John||19800101|M||||||||||||||||\r',
#     b'O|1|1001||^GLU||||||||1|||||F\r',
#     b'R|1|^^^GLU|5.6|mmol/L||N|N||F\r',
#     b'L|1|N\r',
#     b'\x04',
# ]

# def send_bytes():
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.connect((HOST, PORT))
#         for byte_data in dummy_data:
#             for byte in byte_data:
#                 s.send(bytes([byte]))  # send 1 byte at a time
#                 time.sleep(0.1)  # simulate machine delay
#         print("All data sent.")

# if __name__ == '__main__':
#     send_bytes()



# import os
# from datetime import datetime

# # Simulated static byte data (like from machine)
# dummy_data = [
#     b'\x05',
#     b'1H|\^&|||Analyzer^^|||||||P|1\r',
#     b'P|1||123456||Doe^John||19800101|M||||||||||||||||\r',
#     b'O|1|1001||^GLU||||||||1|||||F\r',
#     b'R|1|^^^GLU|5.6|mmol/L||N|N||F\r',
#     b'L|1|N\r',
#     b'\x04',
# ]

# # Output path
# SAVE_DIR = 'C:\\ASTM\\root\\report_file\\'
# os.makedirs(SAVE_DIR, exist_ok=True)

# # File name with timestamp
# timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
# file_path = os.path.join(SAVE_DIR, f"static_output_{timestamp}.txt")

# # Write byte-by-byte (like socket data)
# with open(file_path, 'w', encoding='latin1') as f:
#     for byte_line in dummy_data:
#         for byte in byte_line:
#             f.write(chr(byte))  # convert byte to character

# print(f"✅ Static test data written to: {file_path}")


# dict1= {'a':1, 'b':2}

# print(dict1.get('a'))


# test_ids = ['1','2','3','4','5','6','7','8','9','10']

# print("\\^".join(test_ids))


# formatted = PREFIX + SEPARATOR.join(list)
# jispe .join() lagega wo seprator bnega baki age ke sab prefix bnege

# formatted_test_id = "^^^" + "\^^^".join(test_ids)
# print(formatted_test_id) 


# test_ids = ['t1', '20', '30']
# ^^^10^\^^^20^\^^^30^
# print("^^^" + "^\^^^".join(test_ids) + "^")


