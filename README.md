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

Create a bot using the [botfather](https://core.telegram.org/bots#3-how-do-i-create-a-bot)

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

## exec shell command

Executes a shell command. 

example: 
```
exec ls
```

## execa shell command

Executes a shell command async. 

example: 
```
exec wget http://www.example.com/foo.zip
```

## img image path

Sends the image for the given path

example: 

```
img /home/user/image.png
```

## get url 

Does a get request and prints the returned body.

example: 
```
get https://icanhazip.com/
```

## getdoc

Gets a file from the documents folder

example: 
```
getdoc foo.txt
```

## getf

Gets a file from a path
example:
```
getf /home/user/foo.txt
```

# Url requests

To send a message to all admins call
```
http://localhost:5000/broadcast?token=TOKENHERE&msg=THEMESSAGE
```

# Add more Admins

Every contact sent by an admin also becomes an admin

# Send and Receive files

Every file is saved on the documents folder. To get the file use command getdoc
