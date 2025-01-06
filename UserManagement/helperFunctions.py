import sqlite3
import requests
import os
from flask import Flask, request, jsonify
import hmac
import hashlib
import base64 
import json
import time

app = Flask(__name__)
db_name = "users.db"
file_name = "UserManagement/users.sql"

def get_db() -> sqlite3.connect:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cursor.fetchone():
        with open(file_name, 'r') as f:
            cursor.executescript(f.read())
        conn.commit()
    
    return conn

def validate_password(password : str, first : str, last : str, username : str, salt : str) -> bool | str:
    '''
    password:
        length > 8
        atleast 1 small letter
        atleast 1 big letter
        atleast 1 number 
        cannot contain username 
        cannot contain first or last name
        cannot match any previous passwords
    '''

    conn = get_db()
    cursor = conn.cursor()

    #length atleast 8
    if len(password) < 8: return False

    #has lower case letter
    has_lower = False
    for ch in password:
        if ch.islower(): has_lower = True
    if not has_lower: return False

    #has upper case letter
    has_upper = False
    for ch in password:
        if ch.isupper(): has_upper = True
    if not has_upper: return False

    #has atleast 1 number
    has_num = False
    for ch in password:
        if ch.isnumeric(): has_num = True
    if not has_num: return False

    #does not contain first name
    if first.lower() in password.lower(): return False

    #does not contain last name
    if last.lower() in password.lower(): return False

    #does not match any past password
    cursor.execute("SELECT hash_password FROM past_passwords WHERE username = ?;",(username,))
    pass_lst = cursor.fetchall()
    past_lst = [i[0] for i in pass_lst]

    hashed_password = hashlib.sha256((password + salt).encode(encoding="utf-8"))
    hashed_password = hashed_password.hexdigest()
    if hashed_password in past_lst: return False

    conn.close()

    return hashed_password

def validate_username(username : str) -> bool:
    '''
    RETURNS FALSE IF USERNAME ALREADY IN DATABASE
    '''
    conn = get_db()
    cursor = conn.cursor()

    result = []
    cursor.execute('SELECT * FROM users WHERE username = ?;',(username,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return False
    else:
        return True

def validate_email(email : str) -> bool:
    '''
    RETURNS FALSE IF EMAIL IN DATABASE
    '''
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE email = ?',(email,))

    result = cursor.fetchone()

    conn.close()
    if result:
        return False
    else:
        return True

def create_jwt(header : dict, payload : dict) -> str:
    '''
    header : header = header.encode() and urlsafe_b46encode(header).decode()
    payload : payload = payload.encode() and urlsafe_b64encode(header).decode()
    signature : signature = hashlib.sha256(key.encode()).hexdigest()
    '''

    header_encoded, payload_encoded = json.dumps(header).encode(), json.dumps(payload).encode()
    header_hash = base64.urlsafe_b64encode(header_encoded).decode()
    payload_hash = base64.urlsafe_b64encode(payload_encoded).decode()
    data_hashed = (header_hash + '.' + payload_hash)

    #get key
    with open('UserManagement/Key.txt', 'r') as fp:
        key = fp.read()
    
    signature = hmac.new(key.encode(), data_hashed.encode(), hashlib.sha256).hexdigest()

    jwt = data_hashed + '.' + signature
    return jwt

def validate_jwt() -> bool:
    pass