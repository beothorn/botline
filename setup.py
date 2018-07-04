import bot_config
import psycopg2

try:
    conn = psycopg2.connect("dbname='{0}' user='{1}' host='{2}' password='{3}'".format(
        bot_config.dbname, bot_config.user, bot_config.host, bot_config.password))
except:
    print("No connection to db")

cur = conn.cursor()
cur.execute("""

DROP TABLE IF EXISTS Messages;
DROP TABLE IF EXISTS msg_received;

CREATE TABLE msg_received(
    id                SERIAL       PRIMARY KEY,
    user_id           INT          NOT NULL,
    created_at        TIMESTAMP    NOT NULL,
    message           TEXT
);

""")

