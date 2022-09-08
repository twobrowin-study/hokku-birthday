from os import environ

BotToken = environ.get('BOT_TOKEN')
if BotToken == '' or BotToken == None:
    with open('../telegram.txt', 'r') as fp:
        BotToken = fp.read()

SheetsAccJson = environ.get('SHEETS_ACC_JSON')
SheetsSecret = '../serviceacc.json'
if SheetsAccJson != None and SheetsAccJson != '':
    with open(SheetsSecret, 'w') as fp:
        fp.write(SheetsAccJson)

SheetsName = environ.get('SHEETS_NAME')

SheetHbs               = environ.get('SHEET_HBS')
SheetHbsName           = environ.get('SHEET_HBS_NAME')
SheetHbsDate           = environ.get('SHEET_HBS_DATE')
SheetHbsAdditionalText = environ.get('SHEET_HBS_ADD_TEXT')

SheetEmoji = environ.get('SHEET_EMOJI')
SheetHokku = environ.get('SHEET_HOKKU')

SheetMainText              = environ.get('SHEET_MAIN_TEXT')
SheetMainTextCondition     = environ.get('SHEET_MAIN_TEXT_CONDITION')
SheetMainTextConditionOne  = environ.get('SHEET_MAIN_TEXT_CONDITION_ONE')
SheetMainTextConditionMany = environ.get('SHEET_MAIN_TEXT_CONDITION_MANY')
SheetMainTextText          = environ.get('SHEET_MAIN_TEXT_TEXT')

SheetToWhomSend   = environ.get('SHEET_TO_WHOM_SEND')
SheetToWhomSendId = environ.get('SHEET_TO_WHOM_SEND_ID')