from UserManagement.helperFunctions import *

class Users:

    __slots__ = ['first_name', 'last_name', 'username', 'email', 'group', 'hash_password', 'salt']

    def __init__(self, first_name = None, last_name = None, username = None, email = None, group = None, hash_password = None, salt = None):
        '''
        CONSTRUCTOR FOR THE USERS CLASS. CREATES AN OBJECT WITH GIVEN INFORMATION  
        '''
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email
        self.group = group
        self.hash_password = hash_password
        self.salt = salt

    def add_user(self): 
        '''
        ADDS USER TO DATABASE
        '''
        conn = get_db()
        cursor = conn.cursor()
        with conn:
            cursor.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?);',(self.first_name, self.last_name, self.username, self.email, self.group, self.hash_password, self.salt))


    def get_user(self) -> tuple[tuple]:
        '''
        GETS INFORMATION ASSOCIATED WITH USERNAME FROM DATABASE
        '''
        conn = get_db()
        cursor = conn.cursor()
        result = tuple()
        with conn:
            cursor.execute("SELECT * FROM users WHERE username = ?;",(self.username,))
            result = cursor.fetchone()
        return result


    def __repr__(self):
        '''
        RETURNS OBJECT IN STRING FORMAT
        '''
        res_str = "first_name : {}\nlast_name : {}\nusername : {}\nemail : {}\nhash_password : {}\nsalt : {}".format(self.first_name,self.last_name,self.username,self.email,self.hash_password,self.salt)
                            
        return res_str

    def __str__(self):
        '''
        RETURNS OBJECT IN STRING FORMAT
        '''
        return self.__repr__()

