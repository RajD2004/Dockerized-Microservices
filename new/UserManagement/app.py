from UserManagement.helperFunctions import *
from UserManagement.users import *


@app.route('/create_user', methods = ['POST'])
def create_user() -> dict:
    '''
    password fail:	status_code = 4
    email fail:	status_code = 3
    username fail:	status_code = 2
    success:	status_code = 1
    '''
    status_code = 1
    try:
        conn = get_db()
        cursor = conn.cursor()

        post_data = request.form

        password_valid = validate_password(post_data['password'], post_data['first_name'], post_data['last_name'], post_data['username'], post_data['salt'])

        if not password_valid:
            status_code = 4
        
        username_valid = validate_username(post_data['username'])

        if not username_valid:
            status_code = 2
        
        email_valid = validate_email(post_data['email_address'])

        if not email_valid:
            status_code = 3
        
        if status_code not in {2,3,4}:
            user = Users(post_data['first_name'], post_data['last_name'], post_data['username'], post_data['email_address'], post_data['group'], password_valid, post_data['salt'])
            user.add_user()
            cursor.execute('INSERT INTO past_passwords VALUES (?,?,?)', (post_data['username'], password_valid, time.time()))
            # logging_url = 'http://127.0.0.1:9003/add_log'
            # params = {'username': post_data['username'], 'filename': 'NULL', 'event_type': 'create_user'}
            # requests.post(logging_url, data=params)
            conn.commit()
        
        if not password_valid:
            password_valid = 'NULL'
        
        conn.close()
    
    except Exception as e:
        print(e)
        status_code = 5
        password_valid = 'NULL'
        return jsonify({'status' : status_code, 'pass_hash' : password_valid, 'exception' : str(e)})

    return jsonify({'status' : status_code, 'pass_hash' : password_valid})

@app.route('/login', methods = ['POST'])
def login_user() -> dict:
    '''
    status code 1 if success, status code 2 if failure for any reason
    '''
    status_code = 1
    try:
        conn = get_db()
        cursor = conn.cursor()
        jwt = 'NULL'
        here = 0
        with conn:
            #get the salt and see if user is in database
            cursor.execute('SELECT salt, hash_password FROM users WHERE username = ?;',(request.form['username'],))
            salt_lst = cursor.fetchone()

            if not salt_lst:
                status_code = 2  #if user not in data base
                here = 1
            
            else:
                salt, password = salt_lst[0], salt_lst[1]
                abc = request.form['password'] if 'password' in request.form else 'NULL'
                salt_password = (abc) + (salt)
                hash_pass = hashlib.sha256(salt_password.encode(encoding="utf-8"))
                hash_pass = hash_pass.hexdigest()

                if hash_pass != password:
                    status_code = 2
                    here = 2
                
                else:
                    #create a jwt
                    username = request.form['username']
                    header = {"alg": "HS256", "typ": "JWT"}
                    payload = {'username' : username}
                    jwt = create_jwt(header, payload)

    
    except Exception:
        status_code = 2
        jwt = 'NULL'
        return jsonify({'status' : status_code, 'jwt' : jwt})
    
    # finally:
    #     if status_code == 1:
    #         logging_url = 'http://127.0.0.1:9003/add_log'
    #         post_data = request.form
    #         params = {'username': post_data['username'], 'filename': 'NULL', 'event_type': 'login'}
    #         requests.post(logging_url, data=params)

    return jsonify({'status' : status_code, 'jwt' : jwt})



@app.route('/clear', methods = ['GET'])
def clear() -> None:
    try:
        conn = get_db()
        with conn:
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS users;')
            cursor.execute('DROP TABLE IF EXISTS past_passwords;')
        
        return 'DATABASE CLEARED SUCCESSFULLY', 200
    
    except Exception as e:
        print(e)
        return 'DATABASE CLEARING UNSUCCESSFUL', 500



if __name__ == "__main__":
    app.run(port=9000, debug=True)

