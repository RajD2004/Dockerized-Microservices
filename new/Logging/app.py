import sqlite3
import os
import json
from flask import Flask, request, jsonify
import time
from UserManagement.users import *
from UserManagement.helperFunctions import *
from DocumentManagement.app import *
import requests

app = Flask(__name__)
db_name = "Logging/logs.db"
sql_file = "Logging/Logging.sql"

def get_db_4() -> sqlite3.Connection:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs';")
    l = cursor.fetchone()
    if not l or len(l) == 0:
        with open(sql_file, 'r') as f:
            cursor.executescript(f.read())
        conn.commit()
    
    return conn

@app.route('/add_log', methods=['POST'])
def add_Log():
    '''
    params:
        id : integer primary key (None)
        username : str   //form
        event_type : str  //form
        file_name : str   //form
        event_date : time.time()
    '''
    try:
        conn = get_db_4()
        cursor = conn.cursor()
        username, filename, e_type, e_date = request.form['username'], request.form['filename'], request.form['event_type'], time.time()
        cursor.execute('INSERT INTO logs (username, event_type, file_name, event_date) VALUES (?,?,?,?);', (username, e_type, filename, e_date))
        conn.commit()
        return 'SUCCESS', 200
    except Exception as e:
        return str(e), 500

@app.route('/view_log', methods=['GET'])
def view_log():
    '''
    params:
        post:
            username : str
            filename : str
        headers:
            Authorization : JWT : str
    '''

    try:
        conn = get_db_4()
        groups = []
        with conn:
            cursor = conn.cursor()
            filename = request.args['filename']
            jwt = request.headers['Authorization']
            jwt_data = extract_jwt(jwt)
            
            if jwt_data['validation_status'] == 'False':
                return jsonify({'status' : 2, 'data' : 'NULL'})

            #get groups associated with the filename 
            URL1 = "http://127.0.0.1:9001/get_groups"
            params = {'filename' : filename}
            gd = requests.get(url = URL1, params=params)
            group_data = gd.json()

            if group_data['status'] != 1:
                return jsonify({'status' : 3, 'data' : 'NULL'})
            
            groups = list(group_data['groups'].values())

            #get user group
            user = Users(username=jwt_data['username'])
            user_data = user.get_user()
            grp = user_data[4]

            if grp not in groups:
                #filename not exists or group not valid
                return jsonify({'status' : 3, 'data' : 'NULL', 'groups' : groups, 'grp' : grp})
            
            #status = 1 
            #get the log information
            cursor.execute("SELECT * FROM logs WHERE username = ? OR file_name = ?", (jwt_data['username'], filename))
            log_data = cursor.fetchall()
            data = {}
            for lst in log_data:
                data[lst[0]] = {'event' : lst[2], 'user' : lst[1], 'filename' : lst[3]}
            
            return jsonify({'status' : 1, 'data' : data})
        
    except Exception as e:
        return jsonify({'status' : 500, 'data' : str(e)})
    
@app.route('/log_info', methods = ['GET'])
def log_info():
    '''
    params:
        get:
            filename : str
    return:
        last_mod : username 
        total_mods : int
    '''

    #get log information
    conn = get_db_4()
    with conn:
        cursor = conn.cursor()
        filename = request.args['filename']
        cursor.execute('SELECT * FROM logs WHERE file_name = ? ORDER BY event_date DESC', (filename,)) 
        log_data = cursor.fetchone()  

        ret_data = {}
        ret_data['last_mod'] = log_data[1]

        cursor.execute('SELECT COUNT(*) FROM logs WHERE file_name = ?', (filename,))
        total_mods = cursor.fetchone()
        total_mods = total_mods[0]

        ret_data['total_mods'] = total_mods
    
    return jsonify(ret_data)
        

@app.route('/clear', methods=['GET'])
def clear_Log():
    try:
        conn = get_db_4()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM logs;')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name = "logs";')
        conn.commit()
        return 'SUCCESS', 200
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(port = 9003, debug=True)
