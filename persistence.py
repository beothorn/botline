import bot_config
import sqlite3
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def execute(db_file, query, values):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    query_log = "QUERY => "+query
    logger.info(query_log % values)
    cur.execute(query, values)
    conn.commit()

def create_db(db_file):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE msg_received(
        id                SERIAL       PRIMARY KEY,
        user_id           INT          NOT NULL,
        created_at        TIMESTAMP    NOT NULL,
        message           TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE allowed_ids(
        id                SERIAL       PRIMARY KEY,
        user_id           INT          NOT NULL
    );
    """)
    connection.commit()

def record_msg(db_file, user_id, message):
    execute(db_file, """INSERT INTO msg_received (user_id, message, created_at) VALUES (%s, %s, current_date)""", (user_id, message))

def get_allowed_ids(db_file):
    connection = sqlite3.connect(db_file)
    return connection.execute('SELECT user_id FROM allowed_ids').fetchall()

def add_allowed_id(db_file, user_id):
    execute(db_file, """INSERT INTO allowed_ids (user_id) VALUES (%s)""", (user_id))

