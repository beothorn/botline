
def help_bot(message_context) -> str:
    try:
        with open('./README.md', 'r') as file:
            file_contents = file.read()
        return (file_contents
                #.replace("_", "\\_")
                #.replace("*", "\\*")
                #.replace("[", "\\[")
                #.replace("]", "\\]")
                #.replace("`", "\\`")
                #.replace("#", "\\#")
                #.replace(".", "\\.")
                #.replace("!", "\\!")
        )
    except FileNotFoundError:
        return "Help file not found. You are on your own :("
    except Exception as e:
        return str(e)


commands_that_return_markdown = [
    ('help', 'Display helpful information on how to setup bot.\n    /help', help_bot),
]