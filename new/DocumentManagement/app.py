import sqlite3
import os
import json
import requests
from flask import Flask, request, jsonify
import base64
import sys
from UserManagement.helperFunctions import create_jwt
from UserManagement.users import *


app = Flask(__name__)
db_name = "DocumentManagement/documents.db"
sql_file = "DocumentManagement/DocumentManagement.sql"

def get_db_2() -> sqlite3.connect:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents';")
    l = cursor.fetchone()
    if not l or len(l) == 0:
        with open(sql_file, 'r') as f:
            cursor.executescript(f.read())
        conn.commit()
    
    return conn

# Helper function to extract JWT
def extract_jwt(jwt: str) -> dict:
    conn = get_db_2()
    with conn:
        cursor = conn.cursor()
        jwt_data = jwt.split(".")
        payload_enc = jwt_data[1]
        payload = json.loads(base64.b64decode(payload_enc))
        username = payload['username']
        validation_status = True

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {'username' : username}

        targ = create_jwt(header, payload)

        user = Users(username=username)
        user_data = user.get_user()

        if targ != jwt or not user_data:
            validation_status =  False

        elif user_data[2] != username:
            validation_status =  False
        
        else:
            validation_status =  True
        
        return {'username': username, 'validation_status': str(validation_status)}

# Route to create a document
@app.route('/create_document', methods=['POST'])
def create_document():
    status_code = 1
    m= ''
    username = ''
    try:
        conn = get_db_2()
        with conn:
            cursor = conn.cursor()
            user_filename = request.form['filename']
            validation_dict = extract_jwt(request.headers['Authorization'])
            username = validation_dict['username']
        

            if validation_dict['validation_status'] == "True":
         
                cursor.execute("SELECT * FROM documents where file_name = ?", (user_filename,))
                
                files_lst = cursor.fetchone()
          
                if files_lst:
                    cursor.execute('DELETE FROM documents WHERE file_name = ?', (user_filename,))
                
                body, group = request.form['body'], request.form['groups']
               
                cursor.execute("INSERT INTO documents VALUES (?, ?, ?, ?)", (validation_dict['username'], user_filename, body, group))
                with open(user_filename, 'w', newline='\n') as fp:
                    fp.write(body)
            else:
                status_code = 2
    
    except Exception as e:
        status_code = 2
    
    finally:
        if status_code == 1:
            logging_url = 'http://127.0.0.1:9003/add_log'
            post_data = request.form
            params = {'username': username, 'filename': request.form['filename'], 'event_type': 'document_creation'}
            requests.post(url = logging_url, data=params)    
    return jsonify({'status': status_code})

        
# Route to edit a document

@app.route('/edit_document', methods=['POST'])
def edit_document():
    status_code = 1
    username = ''
    try: 
        conn = get_db_2()
        with conn:
            cursor = conn.cursor()
            target_file, append_body = request.form['filename'], request.form['body']
            validation_dict = extract_jwt(request.headers['Authorization'])
            username = validation_dict['username']

            #verify jwt
            if validation_dict['validation_status'] == 'True':
                
                #check if file exists and extract all its information
                cursor.execute("SELECT * FROM documents WHERE file_name = ?", (target_file,))
                file_data = cursor.fetchone()

                #if file does not exist, status code is 3
                if not file_data:
                    status_code = 3
                
                else:
                    #get the group of user
                    user = Users(username=validation_dict['username'])
                    user_data = user.get_user()
                    user_group = user_data[4]

                    #get the groups associated with the file
                    file_groups = json.loads(file_data[3])

                    if user_group not in file_groups.values():
                        status_code = 3
                    
                    else:
                        new_body = file_data[2] + append_body

                        cursor.execute("UPDATE documents SET body = ? WHERE file_name = ?", (new_body, target_file))

                        with open(target_file, 'a', newline='\n') as fp:
                            fp.write(append_body)


            else:
                status_code = 2

    
    except Exception as e:
        status_code = 4
        #return jsonify({'status': status_code, 'message': str(e)})
    
    finally:
        if status_code == 1:
            logging_url = 'http://127.0.0.1:9003/add_log'
            post_data = request.form
            params = {'username': username, 'filename': request.form['filename'], 'event_type': 'document_edit'}
            requests.post(logging_url, data=params)
    
    return jsonify({'status': status_code})


@app.route('/clear', methods=['GET'])
def clear2():
    try:
        conn = get_db_2()
        with conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS documents")
        
        return 'DATABASE CLEARED SUCCESSFULLY', 200
    
    except Exception as e:
        return 'DATABSE NOT CLEARED. FAILURE!', 500 

@app.route('/get_groups', methods=['GET'])
def get_groups():
    '''
    params:
        get:
            filename : str
    '''
    try:
        conn = get_db_2()
        with conn:
            cursor = conn.cursor()
            filename = request.args.get('filename')
            cursor.execute("SELECT groups FROM documents WHERE file_name = ?", (filename,))
            groups = cursor.fetchone()
            groups = dict(json.loads(groups[0]))
            return jsonify({'status': 1, 'groups': groups})
    
    except Exception as e:
        return jsonify({'status': 2, 'message': str(e), 'groups': {}})

@app.route('/get_document', methods=['GET'])
def get_doc():
    '''
    params:
        get:
            filename : str
    '''
    try:
        conn = get_db_2()
        with conn:
            cursor = conn.cursor()
            filename = request.args.get('filename')
            cursor.execute("SELECT * FROM documents WHERE file_name = ?", (filename,))
            doc = cursor.fetchone()
            return jsonify({'status': 1, 'document': doc})
    
    except Exception as e:
        return jsonify({'status': 2, 'message': str(e), 'document': {}})


if __name__ == "__main__":
    app.run(port=9001, debug=True)
