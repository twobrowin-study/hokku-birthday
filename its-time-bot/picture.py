import requests, re
from PIL import ImageFile
from random import randint
from datetime import datetime

def RequestPhoto(search):
    print("\n{}: Starting request photo".format(datetime.now()))
    req = requests.get("https://yandex.ru/images/search?text="+search)
    ph_links = list(filter(lambda x: '.jpg' in x, re.findall('''(?<=["'])[^"']+''', req.text)))
    ph_list = []
    for i in range(1, 10):
        if len(ph_links[i]) > 5:
            if ph_links[i][0:4] == "http":
                try:
                    size = ph_size(ph_links[i])[0]
                    if size > 500:
                        ph_list.append(ph_links[i])
                        print("\n{}: Got pretty picture".format(datetime.now()))
                except Exception as e:
                    print("\n{}: Error while trying to find picure size".format(datetime.now()))

    print("\n{}: Done request photo".format(datetime.now()))
    return ph_list[randint(0, len(ph_list) - 1)]

def ph_size(url):
    print("\n{}: Start ph size".format(datetime.now()))
    resume_header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
    "Accept-Encoding": "*",
    "Connection": "keep-alive", 
    'Range': 'bytes=0-2000000'}  
    data = requests.get(url, stream = True, headers = resume_header).content
    p = ImageFile.Parser()
    p.feed(data)   
    print("\n{}: Done ph size".format(datetime.now()))
    if p.image:
        return p.image.size 
    else: 
        return (0, 0)