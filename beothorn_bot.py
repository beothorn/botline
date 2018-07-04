from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
import logging
import bot_config
import socket
import subprocess
import psycopg2

updater = Updater(token=bot_config.token)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

try:
        conn = psycopg2.connect("dbname='{0}' user='{1}' host='{2}' password='{3}'".format(bot_config.dbname, bot_config.user, bot_config.host, bot_config.password))
except:
        print("I am unable to connect to the database")

def execute(conn, query, values):
    cur = conn.cursor()
    query_log = "QUERY => "+query
    logger.info(query_log % values)
    cur.execute(query, values)
    conn.commit()

def is_not_allowed(user_id):
    return user_id not in bot_config.allowed_ids

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")

def logo(bot, update):
    with open('/home/pi/dev/localScripts/logo.png', 'rb') as file:
        bot.send_photo(chat_id=update.message.chat_id,photo=file)

def command_ip(bot, update):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    message = "Ip is {0}".format(s.getsockname()[0])
    s.close()
    bot.send_message(chat_id=update.message.chat_id, text=message)

def chat(bot, update):
    user = update.message.from_user
    user_id = user.id
    message = update.message.text
    execute(conn, """INSERT INTO msg_received (user_id, message, created_at) VALUES (%s, %s, current_date)""", (user_id, message))

    if is_not_allowed(user_id):
        return
    commands = message.split(' ')
    if len(commands) < 2:
        bot.send_message(chat_id=update.message.chat_id, text="bad command")
        return
    command = commands[0]
    command_args = commands[1:]
    if command == 'Img':
        with open(command_args[0], 'rb') as file:
            bot.send_photo(chat_id=update.message.chat_id,photo=file)
        return
    if command == 'Exec':
        result = subprocess.run(command_args, stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        bot.send_message(chat_id=update.message.chat_id, text=output)
        return

    message="Commands: Img, Exec"
    bot.send_message(chat_id=update.message.chat_id, text=message)

dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('logo', logo))
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('ip', command_ip))
dispatcher.add_handler(MessageHandler(Filters.text, chat))

updater.start_polling()
updater.idle()
