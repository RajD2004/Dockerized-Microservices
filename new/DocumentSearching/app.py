import sqlite3
import os
import json
import requests
from flask import Flask, request, jsonify
import base64
from UserManagement.users import *
from UserManagement.helperFunctions import *
from DocumentManagement.app import *


app = Flask(__name__)

def file_hash(filename: str) -> str:
    with open(filename, 'rb') as f:
        file_data = hashlib.file_digest(f, 'sha256')
    
    return file_data.hexdigest()


# Route to search documents
@app.route('/search', methods=['GET'])
def search_documents():
    status_code = 1
    try:

        filename = request.args.get('filename')
        jwt = request.headers.get('Authorization')
        validation_dict = extract_jwt(jwt)
        
        if validation_dict['validation_status'] == 'False':
            return jsonify({'status': 2, 'data' : 'NULL'})
        
        #get groups associated with document
        getGroupsURL = "http://127.0.0.1:9001/get_groups"
        params = {'filename': filename}
        groups_data = requests.get(url=getGroupsURL, params=params)
        groups_d = groups_data.json()

        if groups_d['status'] == 2:
            return jsonify({'status': 3, 'data' : 'NULL'})
        
        groups = dict(groups_d['groups']).values()

        #get group of user
        user = Users(username=validation_dict['username'])
        user_data = user.get_user()
        user_group = user_data[4]

        if user_group not in groups:
            return jsonify({'status': 3, 'data' : 'NULL'})
        
        #search for document
        try:
            doc_searchURL = "http://127.0.0.1:9001/get_document"
            params = {'filename': filename}
            doc_data = requests.get(url=doc_searchURL, params=params)
            doc_data = doc_data.json()
        except Exception as e:
            return jsonify({'status': 501, 'data' : str(e)})

        if doc_data['status'] == 2:
            return jsonify({'status': 3, 'data' : 'NULL'})
        
        file_info = doc_data['document']

        username = file_info[0]

        #get log info
        try:
            log_infoURL = "http://127.0.0.1:9003/log_info"
            params = {'filename': filename}
            log_data = requests.get(url=log_infoURL, params=params)
            log_data = log_data.json()
        except Exception as e:
            return jsonify({'status': 502, 'data' : str(e)})
        
        last_mod, total_mods = log_data['last_mod'], log_data['total_mods']

        f_hash = file_hash(filename)

        data = {'filename' : filename, 'owner' : username, 'last_mod' : last_mod, 'total_mod' : total_mods, 'hash' : f_hash}

        logURL = "http://127.0.0.1:9003/add_log"
        params = {'username' : username, 'event_type': 'document_search', 'filename' : filename}
        requests.post(url=logURL, data=params)

        return jsonify({'status': 1, 'data' : data})
        
    except Exception as e:
        return jsonify({'status': 500, 'data' : str(e)})

if __name__ == "__main__":
    app.run(port=9002, debug=True)
