import pygsheets

from settings import SheetsSecret, SheetsName

def OpenSheets():
    gc = pygsheets.authorize(service_file=SheetsSecret)
    sh = gc.open(SheetsName)
    return sh

def GetTodayHbs(sh):
    from settings import SheetHbs, SheetHbsName, SheetHbsDate
    from datetime import datetime

    today = datetime.today().strftime('%d.%m')

    wks = sh.worksheet_by_title(SheetHbs)
    df = wks.get_as_df()
    df[SheetHbsDate] = df[SheetHbsDate].apply(lambda date: '.'.join(date.split('.')[:2]))
    df_todays = df.loc[df[SheetHbsDate] == today]

    return df_todays[SheetHbsName].values

def GetThreeEmojies(sh):
    from settings import SheetEmoji
    import random

    wks = sh.worksheet_by_title(SheetEmoji)
    emojies = wks.cell((1,1)).value
    
    return ''.join(random.sample(emojies, 3))

def GetHokku(sh):
    from settings import SheetHokku
    import random

    wks = sh.worksheet_by_title(SheetHokku)
    all_hokku = wks.get_col(1)
    
    return "\n".join(random.sample(all_hokku, 3))

def GetMainText(sh, is_many):
    from settings import SheetMainText, SheetMainTextCondition, SheetMainTextText
    from settings import SheetMainTextConditionOne, SheetMainTextConditionMany

    wks = sh.worksheet_by_title(SheetMainText)
    df = wks.get_as_df()

    row = df.loc[df[SheetMainTextCondition] == SheetMainTextConditionOne].iloc[0]
    if is_many:
        row = df.loc[df[SheetMainTextCondition] == SheetMainTextConditionMany].iloc[0]
    
    return row[SheetMainTextText]

def GetToWhomSend(sh):
    from settings import SheetToWhomSend, SheetToWhomSendId

    wks = sh.worksheet_by_title(SheetToWhomSend)
    df = wks.get_as_df()

    to_whom_send_ids = []
    for _, row in df.iterrows():
        to_whom_send_ids += [ row[SheetToWhomSendId] ]
    return to_whom_send_ids