from os import environ

BotToken = environ.get('BOT_TOKEN')
if BotToken == '' or BotToken == None:
    with open('../telegram.txt', 'r') as fp:
        BotToken = fp.read()