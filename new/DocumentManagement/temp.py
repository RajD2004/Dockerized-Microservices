import json
import base64
from UserManagement.users import *
from UserManagement.helperFunctions import *


def extract_jwt(jwt: str) -> dict:
    conn = get_db()
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


jwt = 'eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJhYmlnYWlsIn0=.9f8f49704d3cc7e898730f0ee2a0d92813b4b196ba5b9c16219139ceb4d2aab7'

print(extract_jwt(jwt))