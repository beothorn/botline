import sqlite3
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def execute(db_file, query, values):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    #query_log = "QUERY => "+query
    #logger.info(query_log % values)
    cur.execute(query, values)
    conn.commit()

def create_db(db_file):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE bot_info(
        id                SERIAL       PRIMARY KEY,
        handle            TEXT         NOT NULL,
        token             TEXT         NOT NULL,
        started_at        TIMESTAMP    NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE storage(
        key               TEXT         PRIMARY KEY,
        value             TEXT         NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE msg_received(
        id                SERIAL       PRIMARY KEY,
        user_id           INT          NOT NULL,
        chat_id           INT          NOT NULL,
        full_name         TEXT,
        username          TEXT,
        created_at        TIMESTAMP    NOT NULL,
        message           TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE doc_received(
        id                SERIAL       PRIMARY KEY,
        user_id           INT          NOT NULL,
        chat_id           INT          NOT NULL,
        full_name         TEXT,
        username          TEXT,
        created_at        TIMESTAMP    NOT NULL,
        file_name         TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE allowed_ids(
        id                SERIAL       PRIMARY KEY,
        user_id           INT          NOT NULL,
        chat_id           INT          NOT NULL,
        full_name         TEXT,
        username          TEXT
    );
    """)
    connection.commit()

def record_msg(db_file, user_id, chat_id, full_name, username, message):
    execute(db_file, """INSERT INTO msg_received (user_id, chat_id, full_name, username, message, created_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""", (user_id, chat_id, full_name, username, message))

def record_doc(db_file, user_id, chat_id, full_name, username, file_name):
    execute(db_file, """INSERT INTO doc_received (user_id, chat_id, full_name, username, file_name, created_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""", (user_id, chat_id, full_name, username, file_name))

def get_allowed_ids(db_file):
    connection = sqlite3.connect(db_file)
    return connection.execute('SELECT user_id FROM allowed_ids').fetchall()

def get_admin_chat_ids(db_file):
    connection = sqlite3.connect(db_file)
    return connection.execute('SELECT chat_id FROM allowed_ids').fetchall()

def add_allowed_id(db_file, user_id, chat_id):
    execute(db_file, """INSERT INTO allowed_ids (user_id, chat_id) VALUES (?, ?)""", (user_id, chat_id))

def update_chat_id(db_file, user_id, chat_id):
    execute(db_file, """UPDATE allowed_ids SET chat_id = ? WHERE user_id = ?""", (chat_id, user_id))

def add_bot(db_file, token, handle):
    execute(db_file, """INSERT INTO bot_info (handle, token, started_at) VALUES (?, ?, CURRENT_TIMESTAMP)""", (handle, token))

def store(db_file, key, value):
    execute(db_file, """UPDATE storage SET value=? WHERE key=?""", (value, key))
    execute(db_file, """INSERT INTO storage (value, key) SELECT ?, ? WHERE (Select Changes() = 0)""", (value, key))

def get_value(db_file, key):
    connection = sqlite3.connect(db_file)
    return connection.execute('SELECT value FROM storage WHERE key = ?', (key,)).fetchall()
