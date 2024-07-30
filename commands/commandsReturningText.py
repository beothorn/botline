import socket
import requests
import subprocess
import persistence


def command_ip(message_context) -> str:
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip


def command_web_ip(message_context) -> str:
    response = requests.get('https://api.ipify.org?format=json')
    ip_data = response.json()
    return ip_data['ip']


def who_am_i(message_context) -> str:
    return message_context.user_id


def chat_id(message_context) -> str:
    return message_context.chat_id


def exec_cmd(message_context) -> str:
    # Execute the command and capture both stdout and stderr
    result = subprocess.run(message_context.args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=message_context.dir)
    output = result.stdout.decode('utf-8')
    error_output = result.stderr.decode('utf-8')

    # Combine stdout and stderr
    combined_output = f"Output:\n{output}\n\nErrors:\n{error_output}"

    return combined_output


def exec_cmd_bck(message_context) -> str:
    subprocess.Popen(message_context.args, cwd=message_context.dir)
    return "Running command"


def get(message_context) -> str:
    result = requests.get(message_context.args[0])
    return result.text


def list_admins(message_context) -> str:
    admin_list = []
    for admin_info in map(lambda x: f'user_id: {x[0]}, full_name: {x[1]}, username: {x[2]}',
                          persistence.get_admins(message_context.db_file)):
        admin_list.append(str(admin_info))
    return '\n'.join(admin_list)


def delete_admin(message_context) -> str:
    if len(persistence.get_admins(message_context.db_file)) == 1:
        return "Can't delete the only admin, please add another admin and then delete this."
    persistence.delete_admin(message_context.db_file, message_context.args[0])
    return f'Deleted admin id {message_context.args[0]}'


def sql_do(message_context) -> str:
    query = ' '.join(message_context.args)
    result = persistence.sql_do(message_context.db_file, query)
    return str(result)


async def store(message_context) -> str:
    key = message_context.args[0]
    value = ' '.join(message_context.args[1:])
    persistence.store(message_context.db_file, key, value)
    return "Stored value on key %s" % (key,)


def get_value(message_context) -> str:
    key = message_context.args[0]
    value = persistence.get_value(message_context.db_file, key)
    if len(value) == 0:
        return f'No value for key {key}'
    else:
        return value[0][0]


def get_all_values(message_context) -> str:
    value = persistence.get_all_values(message_context.db_file)
    if len(value) == 0:
        return f'No values on store'
    else:
        all_values = ''
        for v in value:
            all_values += f' {v[0]}: {v[1]}'
        return all_values

commands_that_return_text = [
    ('lsadmins', 'List all admins.\n    /lsadmins', list_admins),
    ('rmadmin', 'Deletes a admin.\n    /rmadmin <id>', delete_admin),
#    ('broadcast', 'Sends a message to all users.\n    /broadcast <message>', msg_all),
    ('chatid', 'Returns your chat id.\n    /chatid', chat_id),
    ('exec', 'Executes a command.\n    /exec <command>', exec_cmd),
    ('execa', 'Executes a command on background.\n    /execa <command>', exec_cmd_bck),
    ('get', 'Makes a get request and returns the result.\n    /get <url>', get),
    ('ip', 'Gets the machine local ip.\n    /ip', command_ip),
    ('sql', 'Runs a sql query on bot sqlite db.\n    /sql <sql command>', sql_do),
    ('store', 'Stores a value on a map.\n    /store <key> <value>', store),
    ('value', 'Gets a value from the map.\n    /value <key>', get_value),
    ('values', 'Gets all values from the map.\n    /values', get_all_values),
    ('webip', 'Gets the machine external ip.\n    /webip', command_web_ip),
    ('whoami', 'Returns your user id.\n    /whoami', who_am_i),
]