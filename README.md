# Botline

This is a telegram bot that can run some commands.

# Setup

This uses python 3.

Install the dependencies:

```
pip3 install python-telegram-bot --upgrade
pip3 install requests
pip3 install Flask
```

Create a bot using the botfather https://core.telegram.org/bots#3-how-do-i-create-a-bot

Run using the TOKEN:

```
python3 run_bot.py 'TOKEN GOES HERE'
```

Send a message to the bot to get admin rights, all other users are ignored.

# Commands

## /help

Prints this readme.

## /ip

Gets the local ip.

## /logo

Sends an image (for testing purposes)

## /start

Sends a welcome text (for testing purposes)

## exec shell_command

Executes a shell command. 

example: exec ls

## execa shell_command

Executes a shell command async. 

example: exec wget http://www.example.com/foo.zip

## img image_path

Sends the image for the given path

example: img /home/user/image.png

## get url 

example: get https://icanhazip.com/

# Url requests

To send a message to all admins call
```
http://localhost:5000/broadcast?token=TOKENHERE&msg=THEMESSAGE
```

# Add more Admins

Every contact sent by an admin also becomes an admin
