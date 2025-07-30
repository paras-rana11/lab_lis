# https://github.com/nishishailesh/astm_general/tree/master

##############################################################################
# pip install mysql-connector-python
# pip install flask
# pip install flask_cors

# 'mysql-connector-python','flask','flask-cors'

############################### For Create .exe ###############################
# pyinstaller --onefile general_api.py
############################### After update spec file ########################
# pyinstaller general_api.spec
###############################################################################


import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "headers": "Content-Type"}})


my_user = 'root'
my_pass = 'Root@1234'
my_host = 'localhost'
my_db = 'lis'

@app.route('/get_patient_data', methods=['GET'])
def get_patient_data():
    try:
        pid = request.args.get('pid')
        
        if pid:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Root@1234',
                database='lis'
            )
            cursor = conn.cursor(dictionary=True)
            query = f"SELECT * FROM machineData WHERE patientId = '{pid}'"
            cursor.execute(query)
            result = cursor.fetchall()

            cursor.close()
            conn.close()

            if result:
                response = {
                    "data": result,
                    "message": "LIS results retrieved successfully",
                    "statusState": "success",
                    "status": 200
                }
            else:
                response = {
                    "data": [],
                    "message": "Report Not Ready",
                    "statusState": "success",
                    "status": 200
                }
        else:
            # Case when pid is not provided
            response = {
                "data": [],
                "message": "Case ID Not Found",
                "statusState": "fail",
                "status": 422
            }
        return jsonify(response)

    except Exception as e:
        response = {
            "data": [],
            "message": "Internal Server Error",
            "statusState": "error",
            "status": 500
        }
        return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)

