from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
import telegram
import logging
import persistence
import socket
import subprocess
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

updater = Updater(token, use_context=True)


def is_not_allowed(user_id):
    return user_id not in map(lambda x: x[0], allowed_ids) 


def start(update, context):
    logging.info("========================= START")
    user = update.message.from_user
    user_id = user.id
    message = update.message.text
    message_chat_id = update.message.chat_id
    full_name = user.full_name
    username = user.username
    global allowed_ids
    global waiting_for_first_connection
    persistence.record_msg(db_file, user_id, message_chat_id, full_name, username, message)
    logging.info("waiting_for_first_connection (%s): '%s'" % (waiting_for_first_connection, allowed_ids))
    if waiting_for_first_connection:
        persistence.add_allowed_id(db_file, user_id, message_chat_id)
        allowed_ids = persistence.get_allowed_ids(db_file)
        waiting_for_first_connection = False
        context.bot.send_message(message_chat_id, text="You are now admin :)")
        logging.info("Added new admin (%s): '%s'" % (user_id, message))
        return

    if is_not_allowed(user_id):
        logging.info("Refused (%s): '%s'" % (user_id, message))
        logging.info("Allowed ids: %s" % str(allowed_ids))
        return

    persistence.update_chat_id(db_file, user_id, message_chat_id)


def command_ip(update, context):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    message = "{0}".format(s.getsockname()[0])
    s.close()
    context.bot.send_message(chat_id=update.message.chat_id, text=message)


def command_web_ip(update, context):
    result = requests.get("https://ifconfig.me/ip")
    context.bot.send_message(chat_id=update.message.chat_id, text=result.text)


def help_bot(update, context):
    user = update.message.from_user
    user_id = user.id
    message_chat_id = update.message.chat_id
    logging.info("HELP (%s)" % (user_id,))
    with open('./README.md', 'r') as file:
        context.bot.send_message(chat_id=message_chat_id, text=file.read(), parse_mode=telegram.ParseMode.MARKDOWN)


def whoami(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=update.message.from_user.id)


def chat_id(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=update.message.chat_id)


def img(update, context):
    path = ' '.join(context.args)
    with open(path, 'rb') as file:
        context.bot.send_photo(chat_id=update.message.chat_id,photo=file)


def logo(update, context):
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open('./logo.png', 'rb'))


def exec_cmd(update, context):
    #TODO: get error output
    result = subprocess.run(context.args, stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    context.bot.send_message(chat_id=update.message.chat_id, text=output)


def exec_cmd_bck(update, context):
    subprocess.Popen(context.args)
    context.bot.send_message(chat_id=update.message.chat_id, text="Running command")


def get(update, context):
    result = requests.get(context.args[0])
    context.bot.send_message(chat_id=update.message.chat_id, text=result.text)


def down(update, context):
    path = ' '.join(context.args)
    if path.startswith('/'):
        context.bot.send_document(chat_id=update.message.chat_id, document=open(path, 'rb'))
    else:
        context.bot.send_document(chat_id=update.message.chat_id, document=open(("./documents/%s" % path), 'rb'))


def msg_all(update, context):
    message = ' '.join(context.args).upper()
    user = update.message.from_user
    user_id = user.id
    msg_broadcast = ("%s %s: %s" % (user_id, user.first_name, message))
    for each_chat in map(lambda x: x[0], persistence.get_admin_chat_ids(db_file)):
        if each_chat != 0:
            context.bot.send_message(each_chat, text=msg_broadcast)


def sql_do(update, context):
    query = ' '.join(context.args)
    result = persistence.sql_do(db_file, query)
    context.bot.send_message(chat_id=update.message.chat_id, text=str(result))


def store(update, context):
    key = context.args[0]
    value = ' '.join(context.args[1:])
    persistence.store(db_file, key, value)
    context.bot.send_message(chat_id=update.message.chat_id, text=("Stored value on key %s" % (key,)) )


def get_value(update, context):
    key = context.args[0]
    value = persistence.get_value(db_file, key)
    if len(value) == 0:
        context.bot.send_message(chat_id=update.message.chat_id, text=f'No value for key {key}')
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text=value[0][0])


def get_all_values(update, context):
    value = persistence.get_all_values(db_file)
    if len(value) == 0:
        context.bot.send_message(chat_id=update.message.chat_id, text=f'No values on store')
    else:
        all_values = ''
        for v in value:
            all_values += f' {v[0]}: {v[1]}'
        context.bot.send_message(chat_id=update.message.chat_id, text=all_values)


def on_text(update, context):
    user = update.message.from_user
    user_id = user.id
    full_name = user.full_name
    username = user.username
    message = update.message.text
    message_chat_id = update.message.chat_id
    logging.info("Received message (%s): '%s'" % (user_id, message))
    persistence.record_msg(db_file, user_id, message_chat_id, full_name, username, message)


def on_contact(update, context):
    user = update.message.from_user
    user_id = user.id
    contact_id = update.message.contact.user_id
    contact_name = update.message.contact.first_name
    message_chat_id = update.message.chat_id
    global allowed_ids
    if is_not_allowed(user_id):
        logging.info("Refused contact: '%s'" % user_id)
        return
    logging.info("Received Contact (%s): '%s'" % (user_id, contact_id))
    persistence.add_allowed_id(db_file, contact_id, 0)
    allowed_ids = persistence.get_allowed_ids(db_file)
    context.bot.send_message(message_chat_id, text=("Now %s is admin" % contact_name))
    logging.info("Allowed ids: %s" % str(allowed_ids))


def on_document(update, context):
    user = update.message.from_user
    user_id = user.id
    full_name = user.full_name
    username = user.username
    message_chat_id = update.message.chat_id
    doc_name = update.message.document.file_name
    logging.info("Received Document (%s): '%s'" % (user_id, doc_name))
    persistence.record_doc(db_file, user_id, message_chat_id, full_name, username, doc_name)
    if is_not_allowed(user_id):
        logging.info("Refused document: '%s'" % user_id)
        return
    update.message.document.get_file().download("./documents/%s" % doc_name)


dispatcher = updater.dispatcher

cmds = [
    ('help', 'Display helpfull information on how to setup bot', help_bot),
    ('ip', 'Gets the machine local ip', command_ip),
    ('webip', 'Gets the machine external ip', command_web_ip),
    ('logo', 'Returns a logo (testing purpose)', logo),
    ('whoami', 'Returns your user id', whoami),
    ('chatid', 'Returns your chat id', chat_id),
    ('img', 'Returns an image. img <path>', img),
    ('exec', 'Executes a command. exec <command>', exec_cmd),
    ('execa', 'Executes a command on background. execa <command>', exec_cmd_bck),
    ('get', 'Makes a get request and returns the result. get <url>', get),
    ('down', 'Downloads a file from the server. down <file name|file path>', down),
    ('msg_all', 'Sends a message to all users. msg_all <message>', msg_all),
    ('sql', 'Runs a sql query on bot sqlite db. sql <sql command>', sql_do),
    ('store', 'Stores a value on a map. store <key> <value>', store),
    ('value', 'Gets a value from the map. value <key>', get_value),
    ('values', 'Gets all values from the map. values', get_all_values),
]


def closure(closure_alias, closure_callback):
    def run_cmd_if_allowed(update, context):
        if is_not_allowed(update.message.from_user.id):
            logging.info("Refused %s: '%s'" % (closure_alias, update.message.from_user.id))
            return
        logging.info("Received message '%s' '%s'" % (closure_alias, ' '.join(context.args)))
        closure_callback(update, context)
    return run_cmd_if_allowed


for cmd in cmds:
    alias = cmd[0]
    callback = cmd[2]
    dispatcher.add_handler(CommandHandler(command=alias, callback=closure(alias, callback), pass_args=True))

all_commands = ""

for cmd in cmds:
    all_commands = all_commands + ("%s - %s\n" % (cmd[0], cmd[1]))


def error_callback(update, context):
    error_description = f'Update:\n"{update}"\n caused error:\n"{context.error}"'
    logging.error(error_description)
    context.bot.send_message(chat_id=update.message.chat_id, text=error_description)


def commands(update, context):
    if is_not_allowed(update.message.from_user.id):
        logging.info("Refused commands: '%s'" % (update.message.from_user.id,))
        return
    context.bot.send_message(chat_id=update.message.chat_id, text=all_commands)


dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('cmds', commands))

dispatcher.add_handler(MessageHandler(Filters.text, on_text))
dispatcher.add_handler(MessageHandler(Filters.contact, on_contact))
dispatcher.add_handler(MessageHandler(Filters.document, on_document))

dispatcher.add_error_handler(error_callback)

logging.info("Allowed ids: %s" % str(allowed_ids))

logging.info("Starting bot")
updater.start_polling()

updater_bot = updater.bot

for chat in map(lambda x: x[0], persistence.get_admin_chat_ids(db_file)):
    if chat != 0:
        updater_bot.send_message(chat, text="Bot started")


@app.route('/broadcast')
def broadcast():
    tokenparam = request.args.get('token')
    msg = request.args.get('msg')

    if tokenparam == token:
        for chat in map(lambda x: x[0], persistence.get_admin_chat_ids(db_file)):
            if chat != 0:
                updater_bot.send_message(chat, text=msg)
    return "Sent {}".format(msg)


app.run()
