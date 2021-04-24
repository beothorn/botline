# Botline

This is a telegram bot that can run some commands.

# Setup

This bot needs python 3.6 or higher

Install the dependencies:

```
sudo apt install python3-pip
pip3 install python-telegram-bot --upgrade
pip3 install requests
pip3 install Flask
```

Create a bot using the [botfather](https://core.telegram.org/bots#3-how-do-i-create-a-bot)

Run using the TOKEN:

```
python3 run_bot.py 'TOKEN GOES HERE' mybot
```

Then send a command /start to the bot to get admin rights, all other users are ignored.

# Commands

## /help

Prints this readme.

## /cmds

Prints all commands in the format required by botfather for autocomplete.

## /ip

Gets the local ip.

## /webip

Gets the external ip.

## /logo

Sends back an image (for testing purposes)

## /start

Sends a welcome text (for testing purposes)

## /whoami

Returns your user id

## /chatid

Returns your chat id

## /exec shell command

Executes a shell command. 

example: 
```
/exec ls
```

## /execa shell command

Executes a shell command async. 

example: 
```
/exec wget http://www.example.com/foo.zip
```

## /img image path

Sends back the image on path

example: 

```
/img /home/user/image.png
```
## /msg_all message

Send a message to all admins

example: 

```
broadcast this is a test
```
## /sql query

Runs a sql query on bot sqlite db.

example: 

```
sql SELECT * FROM msg_received
```

## /get url 

Does a get request and prints the returned body.

Protocol (http or https) is required

example: 
```
/get https://icanhazip.com/
```

## /down

Gets a file from a path or from document folder
example:
```
/down /home/user/foo.txt
/down foo.txt
```
## "/store key value" and "/value key" 

Stores and recovers values from a map.

example: 
```
/store foo hello world
/value foo
```
# Url requests

To send a message to all admins call, from the machine running the bot call the url:
```
http://localhost:5000/broadcast?token=TOKENHERE&msg=THEMESSAGE
```

# Add more Admins

Every contact sent by an admin also becomes an admin

# Send and Receive files

Every file is saved on the documents folder. To get the file use command getdoc
