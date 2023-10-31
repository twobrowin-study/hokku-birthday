from random import randint
from datetime import datetime

from bot import Bot
from sheets_funcs import OpenSheets, GetTodayHbs, GetThreeEmojies
from sheets_funcs import GetHokku, GetMainText, GetToWhomSend
from picture import RequestPhoto

from settings import SheetHbsName, SheetHbsAdditionalText

from time import sleep
import traceback

def send_hb():
   sh = OpenSheets()
   today_hbs = GetTodayHbs(sh)
   today_hbs_names = today_hbs[SheetHbsName].values
   today_hbs_atext = today_hbs[SheetHbsAdditionalText].values
   if len(today_hbs_names) > 0:
      many_hbs = (len(today_hbs_names) > 1)
      
      emoji = GetThreeEmojies(sh)
      hokku = GetHokku(sh)
      search = f'Японская живопись {hokku[randint(0,2)]}'
      try:
         photo = RequestPhoto(search)
         print("\n{}: Got photo!".format(datetime.now()))
         has_photo = True
      except Exception as e:
         print("\n{}: Error in photo".format(datetime.now()))
         print(e)
         has_photo = False

      if many_hbs == False:
         additional_text = today_hbs_atext[0]
         caption = GetMainText(sh, many_hbs).format(
            name=today_hbs_names[0],
            three_random_emoji=emoji,
            hokku=hokku,
            additional_text_with_newlines="" if additional_text == "" else "\n\n" + additional_text
         )
      else:
         additional_text = ""
         for atext in today_hbs_atext:
            if atext != "":
               if additional_text == "":
                  additional_text = atext
               else:
                  additional_text += "\n\n" + atext
         caption = GetMainText(sh, many_hbs).format(
            count=len(today_hbs_names),
            three_random_emoji=emoji,
            list_of_people_by_tab_with_trailing_newline="- "+"\n- ".join(today_hbs_names),
            hokku=hokku,
            additional_text_with_newlines="" if additional_text == "" else "\n\n" + additional_text
         )

      for id in GetToWhomSend(sh):
         if has_photo:
            Bot.send_photo(id, photo=photo, caption=caption)
         else:
            Bot.send_message(id, caption)

if __name__ == "__main__":
   print("\n{}: Start sending hokku hb".format(datetime.now()))
   for i in range(0,100):
      try:
         send_hb()
      except Exception:
         print(traceback.format_exc())
         sleep(1)
         print(f"\n{datetime.now()}: Retry sending hokku hb try {i}")
         continue
      break
   print("\n{}: Done sending hokku hb".format(datetime.now()))