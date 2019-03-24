import bot_config
import sqlite3

connection = sqlite3.connect('botbase.db')

cursor = connection.cursor()
cursor.execute("DROP TABLE IF EXISTS Messages;")
cursor.execute("DROP TABLE IF EXISTS msg_received;")


cursor.execute("""
CREATE TABLE msg_received(
    id                SERIAL       PRIMARY KEY,
    user_id           INT          NOT NULL,
    created_at        TIMESTAMP    NOT NULL,
    message           TEXT
);
""")

connection.commit()
