# Botline

This is a telegram bot that can run some commands.

# Setup

Install the dependencies:

```
pip install python-telegram-bot --upgrade
pip install requests
```

Create a bot using the botfather https://core.telegram.org/bots#3-how-do-i-create-a-bot

Run using the TOKEN:

```
python run_bot.py 'TOKEN GOES HERE'
```

Send a message to the bot to get admin rights, all other users are ignored.

# Commands

## /ip

Gets the local ip.

## /logo

Sends an image (for testing purposes)

## /start

Sends a welcome text (for testing purposes)


## exec shell_command

Executes a shell command. 

example: exec ls

## img image_path

Sends the image for the given path

example: img /home/user/image.png

## get url 

example: get https://icanhazip.com/
