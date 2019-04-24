from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
import telegram
import logging
import persistence
import socket
import subprocess
import sqlite3
import os
import sys
import requests
from flask import Flask, request
app = Flask(__name__)

if len(sys.argv) < 3:
    print('Usage: python run_bot.py TOKEN handle')
    exit()

token = sys.argv[1]
handle = sys.argv[2]

db_file = 'botbase.db'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

exists = os.path.isfile(db_file)
if not exists:
    logging.info('Will create db file')
    persistence.create_db(db_file)
    logging.info('Created db file')

persistence.add_bot(db_file, token, handle)

allowed_ids = persistence.get_allowed_ids(db_file)

waiting_for_first_connection = len(allowed_ids) == 0

updater = Updater(token)

def is_not_allowed(user_id):
    logging.info("Allowed ids: %s" % str(allowed_ids))
    return user_id not in map(lambda x: x[0], allowed_ids) 

def start(bot, update):
    user = update.message.from_user
    user_id = user.id
    if is_not_allowed(user_id):
        logging.info("Refused /start: '%s'" % (user_id))
        return
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")

def logo(bot, update):
    user = update.message.from_user
    user_id = user.id
    if is_not_allowed(user_id):
        logging.info("Refused /logo: '%s'" % (user_id))
        return
    with open('./logo.png', 'rb') as file:
        bot.send_photo(chat_id=update.message.chat_id,photo=file)

def command_ip(bot, update):
    user = update.message.from_user
    user_id = user.id
    if is_not_allowed(user_id):
        logging.info("Refused /ip: '%s'" % (user_id))
        logging.info("Allowed ids: %s" % str(allowed_ids))
        return
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    message = "Ip is {0}".format(s.getsockname()[0])
    s.close()
    bot.send_message(chat_id=update.message.chat_id, text=message)

def help_bot(bot, update):
    user = update.message.from_user
    user_id = user.id
    chat_id = update.message.chat_id
    if is_not_allowed(user_id):
        logging.info("Refused /start: '%s'" % (user_id))
        return
    with open('./README.md', 'r') as file:
        bot.send_message(chat_id=chat_id, text=file.read(), parse_mode=telegram.ParseMode.MARKDOWN)

def on_text(bot, update):
    user = update.message.from_user
    user_id = user.id
    message = update.message.text
    chat_id = update.message.chat_id
    global allowed_ids
    global waiting_for_first_connection
    persistence.record_msg(db_file, user_id, chat_id, message)
    if waiting_for_first_connection :
        persistence.add_allowed_id(db_file, user_id, chat_id)
        allowed_ids = persistence.get_allowed_ids(db_file)
        waiting_for_first_connection = False
        bot.send_message(chat_id, text="You are now admin :)")
        logging.info("Added new admin (%s): '%s'" % (user_id, message))
        return

    if is_not_allowed(user_id):
        logging.info("Refused (%s): '%s'" % (user_id, message))
        logging.info("Allowed ids: %s" % str(allowed_ids))
        return

    persistence.update_chat_id(db_file, user_id, chat_id)

    commands = message.split(' ')
    if len(commands) < 2:
        logging.info("Bad command (%s): '%s'" % (user_id, message))
        bot.send_message(chat_id, text="bad command")
        return

    command = commands[0]
    command_args = commands[1:]

    if command.lower() == 'img':
        logging.info("Command Img (%s): '%s'" % (user_id, message))
        with open(command_args[0], 'rb') as file:
            bot.send_photo(chat_id,photo=file)
        return

    if command.lower() == 'exec':
        logging.info("Command Exec (%s): '%s'" % (user_id, message))
        result = subprocess.run(command_args, stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        bot.send_message(chat_id=update.message.chat_id, text=output)
        return

    if command.lower() == 'execa':
        logging.info("Command Exec (%s): '%s'" % (user_id, message))
        subprocess.Popen(command_args)
        bot.send_message(chat_id=update.message.chat_id, text="Running command")
        return

    if command.lower() == 'get':
        logging.info("Command Get (%s): '%s'" % (user_id, message))
        result = requests.get(command_args[0]) 
        bot.send_message(chat_id, text=result.text)
        return

    if command.lower() == 'getdoc':
        logging.info("Command Get Doc (%s): '%s'" % (user_id, message))
        bot.send_message(chat_id, text="Not implemented yet")
        return

    if command.lower() == 'getf':
        logging.info("Command Get File (%s): '%s'" % (user_id, message))
        bot.send_message(chat_id, text="Not implemented yet")
        return

    logging.info("Received: '%s'" % message)
    message="Commands: Img, Exec"
    bot.send_message(chat_id, text=message)

def on_contact(bot, update):
    user = update.message.from_user
    user_id = user.id
    contact_id = update.message.contact.user_id
    chat_id = update.message.chat_id
    global allowed_ids
    if is_not_allowed(user_id):
        logging.info("Refused contact: '%s'" % (user_id))
        return
    logging.info("Received Contact (%s): '%s'" % (user_id, contact_id))
    persistence.add_allowed_id(db_file, contact_id, 0)
    allowed_ids = persistence.get_allowed_ids(db_file)

def on_document(bot, update):
    user = update.message.from_user
    user_id = user.id
    chat_id = update.message.chat_id
    doc_name = update.message.document.file_name
    logging.info("Received Document (%s): '%s'" % (user_id, doc_name))
    persistence.record_doc(db_file, user_id, chat_id, doc_name)
    if is_not_allowed(user_id):
        logging.info("Refused document: '%s'" % (user_id))
        return
    update.message.document.get_file().download("./documents/%s" % doc_name)


dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('logo', logo))
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('ip', command_ip))
dispatcher.add_handler(CommandHandler('help', help_bot))
dispatcher.add_handler(MessageHandler(Filters.text, on_text))
dispatcher.add_handler(MessageHandler(Filters.contact, on_contact))
dispatcher.add_handler(MessageHandler(Filters.document, on_document))

logging.info("Allowed ids: %s" % str(allowed_ids))

logging.info("Starting bot")
updater.start_polling()

bot = updater.bot

for chat in map(lambda x: x[0], persistence.get_admin_chat_ids(db_file)):
    if chat != 0:
        bot.send_message(chat, text="Bot started")

@app.route('/broadcast')
def broadcast():
    tokenparam = request.args.get('token')
    msg = request.args.get('msg')

    if tokenparam == token:
        for chat in map(lambda x: x[0], persistence.get_admin_chat_ids(db_file)):
            bot.send_message(chat, text=msg)
    return "Sent {}".format(msg)

app.run()
#updater.idle()
