# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time
import sys

# В скрипте устанавлиаем кодировку по умолчанию
reload(sys)
sys.setdefaultencoding('utf8')

def getSoupHtmlByUrl(url):
    attempt = 0
    # Для получения страницы используется 10 попыток с таймаутом 30 сек.
    while attempt <= 10:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return BeautifulSoup(resp.content, 'html.parser')
        if resp.status_code != 200:
            attempt += 1

    raise RuntimeError(u'Ошибка. Использовано более 10 попыток получить страницу с данными. Url - {0}'.format(url))


page = 0
print "["
while True:

    # Получение с заглавной страницы очереднойп орции постов
    page = page + 1
    soup = getSoupHtmlByUrl('http://picademy.net/' if page == 1 else 'http://picademy.net/page/{0}/'.format(page))

    # Перебор всех постов полученных с заглавной
    posts = soup.find_all(name='div', attrs={'class': 'home_post_box'})
    for p in posts:

        # Получаем поля с заглавной с постао
        a_href_from_main = p.find(name='a').get('href')
        img_src_from_main = p.find(name='img').get('src')
        h_from_main = p.find(name='h3').get_text()

        # Грузим страницу по УРЛ и получаем с нее прааметры
        soup_post = getSoupHtmlByUrl(a_href_from_main)

        # получаем поля с внутренней
        meta_keywords_content = soup_post.find(name='meta', attrs={'name': 'keywords'}).get('content')

        # До 27 станицы один шаблон, а с 27-й страницы - другой.
        # Пример где другой шаблон http://picademy.net/tyi-che-hleb-kurnul/
        img_src_from_post = soup_post.find(name='img', class_='aligncenter')
        if img_src_from_post is None:
            img_src_from_post = soup_post.find(name='img', class_='alignnone')
        img_src_from_post = img_src_from_post.get('src')

        h1_from_post = soup_post.find(name='h1').get_text()
        a_category_text_from_post = soup_post.find(name='a', attrs={'rel': "category tag"}).get_text()

        # Формируем JSON
        json_obj = {
          "url": a_href_from_main.encode('utf8'),
          "title": h1_from_post.encode('utf8'),
          "image": img_src_from_post.encode('utf8'),
          "category": a_category_text_from_post.encode('utf8'),
          "keywords": [k.strip().encode('utf8') for k in meta_keywords_content.split(',')]
        }

        if p != posts[0]:
            print ","

        meta_keywords_content_str = ""
        for k in meta_keywords_content.split(','):
            meta_keywords_content_str+='"'+k.strip().encode('utf8')+'", '
        if meta_keywords_content_str.endswith(', '):
            meta_keywords_content_str = meta_keywords_content_str[:-2]

        print "{",
        print '"url": "'+a_href_from_main.strip().encode('utf8')+'", ',
        print '"title": "'+h1_from_post.strip().encode('utf8')+'", ',
        print '"image": "'+img_src_from_post.strip().encode('utf8')+'", ',
        print '"category": "'+a_category_text_from_post.strip().encode('utf8')+'", ',
        print '"keywords": ['+meta_keywords_content_str+']'+'}',

    # Критерий выхода - в выдаче менее 12 постов (последняя страница содержит не 12 а менее постов,
    # а за ней идет несколько путых страниц, а потом код ошибки)
    posts_count = len(posts)
    if posts_count != 12:
        print
        break

print "]"

