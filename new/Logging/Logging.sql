DROP TABLE IF EXISTS logs;

CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    event_type TEXT NOT NULL,
    file_name TEXT,
    event_date REAL NOT NULL
);