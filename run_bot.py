from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
import logging
import bot_config
import persistence
import socket
import subprocess
import sqlite3
import os
import sys

if len(sys.argv) < 2:
    print 'Usage: python run_bot.py TOKEN'
    exit()

token = sys.argv[1]

db_file = 'botbase.db'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

exists = os.path.isfile(db_file)
if not exists:
    logging.info('Will create db file')
    persistence.create_db(db_file)
    logging.info('Created db file')

allowed_ids = persistence.get_allowed_ids(db_file)

waiting_for_first_connection = len(allowed_ids) == 0

updater = Updater(token)

def is_not_allowed(user_id):
    return user_id not in allowed_ids

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
    persistence.record_msg(db_file, user_id, message)

    if waiting_for_first_connection :
        persistence.add_allowed_id(db_file, user_id)
        allowed_ids = persistence.get_allowed_ids(db_file)
        bot.send_message(chat_id=update.message.chat_id, text="You are now admin :)")
        return
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
