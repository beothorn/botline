def down(message_context):
    path = ' '.join(message_context["args"])
    if path.startswith('/'):
        return open(path, 'rb')
    else:
        return open(f'{message_context["dir"]}/{path}', 'rb')


commands_that_return_document = [
    ('down', 'Downloads a file from the server.\n    /down <file name|file path>', down),
]
