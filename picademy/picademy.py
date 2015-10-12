# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time


def getSoupHtmlByUrl(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        raise RuntimeError(u'Ошибка')
    return BeautifulSoup(resp.content, 'html.parser')

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
          "url": a_href_from_main,
          "title": h1_from_post,
          "image": img_src_from_post,
          "category": a_category_text_from_post,
          "keywords": [k.strip() for k in meta_keywords_content.split(',')]
        }

        import simplejson
        if p != posts[0]:
            print ","
        print simplejson.dumps(json_obj),

    # Критерий выхода - в выдаче менее 12 постов (последняя страница содержит не 12 а менее постов,
    # а за ней идет несколько путых страниц, а потом код ошибки)
    posts_count = len(posts)
    if posts_count != 12:
        print
        break

print "]"

