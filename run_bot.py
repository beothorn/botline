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
logging.info("Allowed ids: %s" % str(allowed_ids))

waiting_for_first_connection = len(allowed_ids) == 0

updater = Updater(token)

def is_not_allowed(user_id):
    return user_id not in map(lambda x: x[0], allowed_ids) 

def start(bot, update):
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

def command_ip(bot, update):
    user = update.message.from_user
    user_id = user.id
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    message = "Ip is {0}".format(s.getsockname()[0])
    s.close()
    bot.send_message(chat_id=update.message.chat_id, text=message)

def help_bot(bot, update):
    user = update.message.from_user
    user_id = user.id
    chat_id = update.message.chat_id
    logging.info("HELP (%s)" % (user_id,))
    with open('./README.md', 'r') as file:
        bot.send_message(chat_id=chat_id, text=file.read(), parse_mode=telegram.ParseMode.MARKDOWN)

def whoami(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.from_user.id)

def chat_id(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.chat_id)

def img(bot, update, args):
    path = ' '.join(args)
    with open(path, 'rb') as file:
        bot.send_photo(chat_id,photo=file)

def exec_cmd(bot, update, args):
    #TODO: get error output
    result = subprocess.run(args, stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    bot.send_message(chat_id=update.message.chat_id, text=output)

def exec_cmd_bck(bot, update, args):
    subprocess.Popen(args)
    bot.send_message(chat_id=update.message.chat_id, text="Running command")

def get(bot, update, args):
    result = requests.get(args[0]) 
    bot.send_message(chat_id=update.message.chat_id, text=result.text)

def down(bot, update, args):
    path = ' '.join(args) 
    if path.startswith('/'):
        bot.send_document(chat_id=chat_id, document=open(path, 'rb'))
    else:
        bot.send_document(chat_id=chat_id, document=open(("./documents/%s" % path ), 'rb'))

def msg_all(bot, update, args):
    message = ' '.join(args).upper()
    user = update.message.from_user
    user_id = user.id
    msg_broadcast = ("%s %s: %s" % (user_id, user.first_name, message))
    for chat in map(lambda x: x[0], persistence.get_admin_chat_ids(db_file)):
        if chat != 0:
            bot.send_message(chat, text=msg_broadcast)

def sql_do(bot, update, args):
    query = ' '.join(args)
    result = persistence.execute(db_file, query, ())
    bot.send_message(chat_id=update.message.chat_id, text=str(result))

def on_text(bot, update):
    user = update.message.from_user
    user_id = user.id
    message = update.message.text
    chat_id = update.message.chat_id
    logging.info("Received message (%s): '%s'" % (user_id, message))
    persistence.record_msg(db_file, user_id, chat_id, message)

def on_contact(bot, update):
    user = update.message.from_user
    user_id = user.id
    contact_id = update.message.contact.user_id
    contact_name = update.message.contact.first_name
    chat_id = update.message.chat_id
    global allowed_ids
    if is_not_allowed(user_id):
        logging.info("Refused contact: '%s'" % (user_id))
        return
    logging.info("Received Contact (%s): '%s'" % (user_id, contact_id))
    persistence.add_allowed_id(db_file, contact_id, 0)
    allowed_ids = persistence.get_allowed_ids(db_file)
    bot.send_message(chat_id, text=("Now %s is admin" % contact_name))
    logging.info("Allowed ids: %s" % str(allowed_ids))

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

cmds = [
    ('help', 'Display helpfull information on how to setup bot', help_bot),
    ('ip', 'Gets the machine local ip', command_ip),
    ('whoami', 'Returns your user id', whoami),
    ('chatid', 'Return your chat id', chat_id)
]

cmds_args = [
    ('img', 'Returns an image. img <path>', img),
    ('exec', 'Executes a command. exec <command>', exec_cmd),
    ('execa', 'Executes a command on background. execa <command>', exec_cmd_bck),
    ('get', 'Makes a get request and returns the result. get <url>', get),
    ('down', 'Downloads a file from the server. down <file name|file path>', down),
    ('msg_all', 'Sends a message to all users. msg_all <message>', msg_all),
#    ('msg_adm', 'Sends a message to all admins. msg_admin <message>', msg_adm),
    ('sql', 'Runs a sql query on bot sqlite db. sql <sql command>', sql_do)
]

def closure(alias, callback):
    def run_cmd_if_allowed(bot, update):
        if is_not_allowed(update.message.from_user.id):
            logging.info("Refused %s: '%s'" % (alias, update.message.from_user.id))
            return
        logging.info("Received message '%s'" % (alias,))
        callback(bot, update)
    return run_cmd_if_allowed

for cmd in cmds:
    alias = cmd[0]
    callback = cmd[2]
    dispatcher.add_handler(CommandHandler(command=alias, callback=closure(alias, callback), pass_args=False))

def closure_args(alias, callback):
    def run_cmd_if_allowed(bot, update, args):
        if is_not_allowed(update.message.from_user.id):
            logging.info("Refused %s: '%s'" % (alias, update.message.from_user.id))
            return
        logging.info("Received message '%s' '%s'" % (alias, ' '.join(args)))
        callback(bot, update, args)
    return run_cmd_if_allowed

for cmd in cmds_args:
    alias = cmd[0]
    callback = cmd[2]
    dispatcher.add_handler(CommandHandler(command=alias, callback=closure_args(alias, callback), pass_args=True))

all_commands = ""

for cmd in (cmds + cmds_args):
    all_commands = all_commands + ("%s - %s\n" % (cmd[0], cmd[1]))

def commands(bot, update):
    if is_not_allowed(update.message.from_user.id):
        logging.info("Refused commands: '%s'" % (update.message.from_user.id,))
        return
    bot.send_message(chat_id=update.message.chat_id, text=all_commands)

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('cmds', commands))

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
            if chat != 0:
                bot.send_message(chat, text=msg)
    return "Sent {}".format(msg)

app.run()
#updater.idle()
