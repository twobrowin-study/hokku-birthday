from random import randint
from datetime import datetime

import sys

from bot import Bot
from sheets_funcs import OpenSheets, GetTodayHbs, GetThreeEmojies
from sheets_funcs import GetHokku, GetMainText, GetToWhomSend
from picture import RequestPhoto

def send_hb():
   sh = OpenSheets()
   today_hbs = GetTodayHbs(sh)
   if len(today_hbs) > 0:
      many_hbs = (len(today_hbs) > 1)
      
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
         caption = GetMainText(sh, many_hbs).format(
            name=today_hbs[0],
            three_random_emoji=emoji,
            hokku=hokku
         )
      else:
         caption = GetMainText(sh, many_hbs).format(
            count=len(today_hbs),
            three_random_emoji=emoji,
            list_of_people_by_tab_with_trailing_newline="- "+"\n- ".join(today_hbs),
            hokku=hokku
         )

      for id in GetToWhomSend(sh):
         if has_photo:
            Bot.send_photo(id, photo=photo, caption=caption)
         else:
            Bot.send_message(id, caption)

print("\n{}: Start sending hokku hb".format(datetime.now()))
send_hb()
print("\n{}: Done sending hokku hb".format(datetime.now()))