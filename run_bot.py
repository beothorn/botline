from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from commands.commandsReturningText import commands_that_return_text

import logging
import persistence
import os
import sys
import configparser
from pathlib import Path
import re


bot_properties_file = 'bot.properties'

if os.path.isfile(bot_properties_file):
    logging.info(f"Using {bot_properties_file}")
    config = configparser.ConfigParser()
    config.read('bot.properties')
    token = config['bot_config']['token']
    handle = config['bot_config']['handle']
    db_file = config['bot_config']['db_file']
    current_dir = config['bot_config']['current_dir']
    enabled_cmd = config['cmds_config']['enabled_cmd']
    broadcast_unkown_messages = config['cmds_config']['broadcast_unkown_messages']
    buttons_rows_per_page = int(config['cmds_config']['buttons_rows_per_page'])
else:
    if len(sys.argv) < 3:
        print('Usage: python run_bot.py TOKEN handle')
        exit()
    token = sys.argv[1]
    handle = sys.argv[2]
    db_file = 'botbase.db'
    current_dir = "."
    enabled_cmd = 'explore,help,ip,webip,logo,whoami,chatid,img,exec,execa,get,down,broadcast,print,sql,store,value,values'
    buttons_rows_per_page = 10
    logging.info('All commands are enabled, to disable them use a bot.properties file')

current_dir = str(Path(current_dir).absolute())

logging.info(f'Enabled commands {enabled_cmd}')
allowed = enabled_cmd.split(',')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

exists = os.path.isfile(db_file)
if not exists:
    logging.info('Will create db file')
    persistence.create_db(db_file)
    logging.info('Created db file')

persistence.add_bot(db_file, token, handle)

logging.info("Admins: %s" % str(persistence.get_admin(db_file)))

waiting_for_first_connection = len(persistence.get_admin(db_file)) == 0


def is_allowed(user_id):
    return user_id in map(lambda x: x[0], persistence.get_admin(db_file))


def is_not_allowed(user_id):
    return not is_allowed(user_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("========================= START")
    user = update.message.from_user
    user_id = user.id
    message = update.message.text
    message_chat_id = update.message.chat_id
    full_name = user.full_name
    username = user.username
    global waiting_for_first_connection
    persistence.record_msg(db_file, user_id, message_chat_id, full_name, username, message)
    logging.info("waiting_for_first_connection (%s): '%s'" % (waiting_for_first_connection, persistence.get_admin(db_file)))
    if waiting_for_first_connection:
        persistence.add_admin(db_file, user_id, message_chat_id, full_name, username)
        waiting_for_first_connection = False
        logging.info("Added new admin (%s): '%s'" % (user_id, message))
        await update.message.reply_text("You are now admin\nUse /help to see what you can do")
        return

    if is_not_allowed(user_id):
        logging.info("Refused (%s): '%s'" % (user_id, message))
        logging.info("Admins: %s" % str(persistence.get_admin(db_file)))
        return

    persistence.update_admin_info(db_file, user_id, message_chat_id, full_name, username)
    logging.info(f'Updated admin user_id: {user_id}, message_chat_id: {message_chat_id}, '
                 f'full_name: {full_name}, username: {username}')
    await update.message.reply_text("You are now admin\nUse /help to see what you can do")


def broadcast(update, context, message):
    user = update.message.from_user
    user_id = user.id
    msg_broadcast = ("%s %s: %s" % (user_id, user.first_name, message))
    for each_chat in map(lambda x: x[0], persistence.get_admin_chat_ids(db_file)):
        if each_chat != 0:
            context.bot.send_message(each_chat, text=msg_broadcast)


async def msg_all(update, context):
    message = ' '.join(context.args)
    broadcast(update, context, message)


def list_directories():
    return [x.name for x in Path(current_dir).glob('*') if x.is_dir()]


def list_files():
    return [x.name for x in Path(current_dir).glob('*') if x.is_file()]


def parent_dir():
    path = Path(current_dir)
    return str(path.parent.absolute())


def all_dirs_keyboard(page):
    keyboard = []
    for d in list_directories():
        keyboard.append([InlineKeyboardButton(d, callback_data=f"EXPLORE goto_dir {d}")])
    remove_before = page*buttons_rows_per_page
    with_previous_removed = keyboard[remove_before:]
    remaining = len(with_previous_removed)
    with_remaining_removed = with_previous_removed[:buttons_rows_per_page]

    if page > 0 and remaining <= buttons_rows_per_page:
        with_remaining_removed.append([InlineKeyboardButton("<<", callback_data=f"EXPLORE list_dir {page - 1}")])

    if page == 0 and remaining > buttons_rows_per_page:
        with_remaining_removed.append([InlineKeyboardButton(">>", callback_data=f"EXPLORE list_dir {page + 1}")])

    if page > 0 and remaining > buttons_rows_per_page:
        with_remaining_removed.append([InlineKeyboardButton("<<", callback_data=f"EXPLORE list_dir {page - 1}"),
                                       InlineKeyboardButton(">>", callback_data=f"EXPLORE list_dir {page + 1}")])

    with_remaining_removed.append([InlineKeyboardButton("..", callback_data="EXPLORE goto_parent_dir")])
    with_remaining_removed.append([InlineKeyboardButton("Show files", callback_data="EXPLORE show_files")])
    with_remaining_removed.append([InlineKeyboardButton("Close", callback_data="EXPLORE close")])
    return with_remaining_removed


def all_files_keyboard(page):
    keyboard = []
    for f in list_files():
        keyboard.append([InlineKeyboardButton(f, callback_data=f"EXPLORE download {f}")])
    remove_before = page*buttons_rows_per_page
    with_previous_removed = keyboard[remove_before:]
    remaining = len(with_previous_removed)
    with_remaining_removed = with_previous_removed[:buttons_rows_per_page]

    if page > 0 and remaining <= buttons_rows_per_page:
        with_remaining_removed.append([InlineKeyboardButton("<<", callback_data=f"EXPLORE show_files {page - 1}")])

    if page == 0 and remaining > buttons_rows_per_page:
        with_remaining_removed.append([InlineKeyboardButton(">>", callback_data=f"EXPLORE show_files {page + 1}")])

    if page > 0 and remaining > buttons_rows_per_page:
        with_remaining_removed.append([InlineKeyboardButton("<<", callback_data=f"EXPLORE show_files {page - 1}"),
                                       InlineKeyboardButton(">>", callback_data=f"EXPLORE show_files {page + 1}")])

    with_remaining_removed.append([InlineKeyboardButton("Show directory", callback_data="EXPLORE list_dir 0")])
    with_remaining_removed.append([InlineKeyboardButton("Close", callback_data="EXPLORE close")])
    return with_remaining_removed


def on_explore_callback(update, context) -> None:
    global current_dir
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    if query.data == "EXPLORE goto_parent_dir":
        logging.info(f"Explore: leave {current_dir}")
        current_dir = parent_dir()
        logging.info(f"Explore: go to {current_dir}")
        query.edit_message_text(text=current_dir, reply_markup=InlineKeyboardMarkup(all_dirs_keyboard(0)))
        return

    if query.data == "EXPLORE show_files":
        logging.info(f"Explore: show files for {current_dir}")
        query.edit_message_text(text=current_dir, reply_markup=InlineKeyboardMarkup(all_files_keyboard(0)))
        return

    list_dir_with_page = re.search('EXPLORE list_dir (\\d+)', query.data)
    if list_dir_with_page:
        page = list_dir_with_page.group(1)
        logging.info(f"Explore: show dir page {page} of {current_dir}")
        query.edit_message_text(text=current_dir, reply_markup=InlineKeyboardMarkup(all_dirs_keyboard(int(page))))
        return

    goto_dir = re.search('EXPLORE goto_dir (.*)', query.data)
    if goto_dir:
        logging.info(f"Explore: leave {current_dir}")
        current_dir = f'{current_dir}/{goto_dir.group(1)}'
        logging.info(f"Explore: go to {current_dir}")
        query.edit_message_text(text=current_dir, reply_markup=InlineKeyboardMarkup(all_dirs_keyboard(0)))
        return

    show_files = re.search('EXPLORE show_files (\\d+)', query.data)
    if show_files:
        page = show_files.group(1)
        logging.info(f"Explore: show files page {page} of {current_dir}")
        query.edit_message_text(text=current_dir, reply_markup=InlineKeyboardMarkup(all_files_keyboard(int(page))))
        return

    download_file = re.search('EXPLORE download (.*)', query.data)
    if download_file:
        download_file_path = f'{current_dir}/{download_file.group(1)}'
        logging.info(f"Explore: download file {download_file_path}")
        context.bot.send_document(chat_id=update.callback_query.message.chat.id, document=open(download_file_path, 'rb'))
        query.edit_message_text(text=f"Uploaded: {download_file_path}")
        return

    if query.data == "EXPLORE close":
        query.edit_message_text(text=f"Current dir is now {current_dir}")
        return

    query.edit_message_text(text=f"Selected option: {query.data}")


async def explore(update, context):
    logging.info(f"Explore: {current_dir}")
    update.message.reply_text(text=current_dir, reply_markup=InlineKeyboardMarkup(all_dirs_keyboard(0)))


last_document = None


async def print_and_callback(update, context, file):
    logging.info(f"Will try to print {file}")
    import cups
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_name = list(printers.keys())[0]
    conn.printFile(printer_name, file, "", {})
    await update.message.reply_document(f'Will try to print {file}')


async def print_file(update, context):
    logging.info(f"Received print command with args: {context.args}")
    if context.args:
        await print_and_callback(update, context, ' '.join(context.args))
    else:
        if last_document:
            await print_and_callback(update, context, last_document)
        else:
            await update.message.reply_document(f'No last document, please send one or use /print absolutePath')


def on_text(update, context):
    user = update.message.from_user
    user_id = user.id
    full_name = user.full_name
    username = user.username
    message = update.message.text
    message_chat_id = update.message.chat_id
    logging.info("Received message (%s): '%s'" % (user_id, message))
    persistence.record_msg(db_file, user_id, message_chat_id, full_name, username, message)
    if is_not_allowed(update.message.from_user.id):
        if broadcast_unkown_messages:
            broadcast(update, context, message)


def on_contact(update, context):
    user = update.message.from_user
    user_id = user.id
    contact_id = update.message.contact.user_id
    contact_name = update.message.contact.first_name
    message_chat_id = update.message.chat_id
    if is_not_allowed(user_id):
        logging.info("Refused contact: '%s'" % user_id)
        return
    logging.info("Received Contact (%s): '%s'" % (user_id, contact_id))
    persistence.add_admin(db_file, contact_id, 0, "", "")
    context.bot.send_message(message_chat_id, text=("Now %s is admin" % contact_name))
    logging.info("Admins: %s" % str(persistence.get_admin(db_file)))


def on_document(update, context):
    global last_document
    user = update.message.from_user
    user_id = user.id
    if is_not_allowed(user_id):
        logging.info("Refused document: '%s'" % user_id)
        return

    full_name = user.full_name
    username = user.username
    message_chat_id = update.message.chat_id
    doc_name = update.message.document.file_name
    logging.info("Received Document (%s): '%s'" % (user_id, doc_name))
    last_document = f'{current_dir}/{doc_name}'
    logging.info(f"Will save it to {last_document}")
    persistence.record_doc(db_file, user_id, message_chat_id, full_name, username, last_document)
    update.message.document.get_file().download(last_document)
    context.bot.send_message(message_chat_id, text=f'Saved file on {last_document}')


def to_be_implemented(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text='Not implemented yet.')


def closure_for_commands_that_return_text(closure_alias, closure_callback):
    global current_dir
    global db_file

    async def run_cmd_if_allowed(update, context):
        if is_not_allowed(update.message.from_user.id):
            logging.info("Refused %s: '%s'" % (closure_alias, update.message.from_user.id))
            return
        logging.info("Received command '%s' '%s'" % (closure_alias, ' '.join(context.args)))
        message_context = {
            "user_id": update.message.from_user.id,
            "chat_id": update.message.chat_id,
            "args": context.args,
            "dir": current_dir,
            "db_file": db_file,
            "text": update.message.text,
        }
        await update.message.reply_text(closure_callback(message_context))
    return run_cmd_if_allowed


def command_not_enabled(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="This command is not enabled, "
                                                                  "change bot.properties to enable it")


def error_callback(update, context):
    error_description = f'Update:\n"{update}"\n caused error:\n"{context.error}"'
    logging.error(error_description)
    if is_allowed(update.message.from_user.id):
        context.bot.send_message(chat_id=update.message.chat_id, text=error_description)


def commands(update, context):
    if is_not_allowed(update.message.from_user.id):
        logging.info("Refused commands: '%s'" % (update.message.from_user.id,))
        return
    context.bot.send_message(chat_id=update.message.chat_id, text=all_commands)

#application.add_handler(CommandHandler('start', start))
#application.add_handler(CommandHandler('cmds', commands))

#application.add_handler(CallbackQueryHandler(on_explore_callback, pattern='^EXPLORE .*$'))

#application.add_handler(MessageHandler(filters.TEXT, on_text))
#application.add_handler(MessageHandler(filters.CONTACT, on_contact))
#application.add_handler(MessageHandler(filters.VIDEO | filters.PHOTO | filters.Document.ALL, on_document))

#application.add_error_handler(error_callback)

logging.info("Admins: %s" % str(persistence.get_admin(db_file)))

logging.info("Starting bot")
#application.run_polling()

#updater_bot = application.bot

#for chat in map(lambda x: x[0], persistence.get_admin_chat_ids(db_file)):
#    if chat != 0:
#        updater_bot.send_message(chat, text=f'Bot {handle} started {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}')


###########################
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)


def main() -> None:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    for cmd in commands_that_return_text:
        alias = cmd[0]
        if alias in allowed:
            callback = cmd[2]
            application.add_handler(CommandHandler(alias, closure_for_commands_that_return_text(alias, callback)))
        else:
            application.add_handler(CommandHandler(alias, closure_for_commands_that_return_text(alias, command_not_enabled)))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

###########################


if __name__ == "__main__":
    main()