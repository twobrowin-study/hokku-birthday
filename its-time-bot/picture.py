import requests, re
from PIL import ImageFile
from random import randint

def RequestPhoto(search):
    req = requests.get("https://yandex.ru/images/search?text="+search)
    ph_links = list(filter(lambda x: '.jpg' in x, re.findall('''(?<=["'])[^"']+''', req.text)))
    ph_list = []
    for i in range(1, 10):
        if len(ph_links[i]) > 5:
            if ph_links[i][0:4] == "http":
                size = ph_size(ph_links[i])[0]
                print(size)
                if size > 500:
                    ph_list.append(ph_links[i])
                    print(ph_list)

    return ph_list[randint(0, len(ph_list) - 1)]

def ph_size(url):
    resume_header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
    "Accept-Encoding": "*",
    "Connection": "keep-alive", 
    'Range': 'bytes=0-2000000'}  
    data = requests.get(url, stream = True, headers = resume_header).content
    p = ImageFile.Parser()
    p.feed(data)   
    if p.image:
        return p.image.size 
    else: 
        return (0, 0)