DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS past_passwords;

CREATE TABLE users(
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    email TEXT,
    group_belongsto TEXT,
    hash_password TEXT,
    salt TEXT
);

CREATE TABLE past_passwords(
    username TEXT,
    hash_password TEXT,
    creation_time FLOAT
);