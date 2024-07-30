def img(message_context):
    path = ' '.join(message_context.args)
    return open(path, 'rb')


def logo(message_context):
    return open('../logo.png', 'rb')


cmds = [
    ('img', 'Returns an image.\n    /img <path>', img),
    ('logo', 'Returns a logo (testing purpose).\n    /logo', logo),
]