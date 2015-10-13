# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import sys
import datetime
import simplejson

def getByUrl(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        raise RuntimeError(u'Ошибка')
    return resp.content


def getSoupByHtml(html):
    return BeautifulSoup(html, 'html.parser')


def getSoupHtmlByUrl(url):
    return getSoupByHtml(getByUrl(url))

# из строки вида <tr><td><img src='\/shared\/site\/images\/check_icon_1.png' width='49' height='47'> <span>\u041a\u0438\u0435\u0432\u0441\u043a\u043e\u0435 \u043e\u0442\u0434\u0435\u043b\u0435\u043d\u0438\u0435 \u21163<\/span><\/td><td>\u0443\u043b. \u0421\u0442\u0430\u0440\u043e\u0432\u043e\u043a\u0437\u0430\u043b\u044c\u043d\u0430\u044f, 13<\/td><td><\/td><td><\/td><td>\u043a\u0440\u0443\u0433\u043b\u043e\u0441\u0443\u0442\u043e\u0447\u043d\u043e<\/td>
# получаем нормальную html-строку
def decodeUniCharsAndSlashed(s):
    s2 = re.sub(r'\\u([a-fA-F0-9]{4})', lambda m: unichr(int(m.group(1), 16)), s)
    s2 = s2.replace('\\/', '/')
    import cgi_unescape
    return cgi_unescape.unescape(s2)


# получая на вход строку вида
# curl 'http://www.mbank.kiev.ua/jscripts/ajax/list_serialize.php?city=1000%3F%3E&q=&type%5B%5D=1&type%5B%5D=2&type%5B%5D=3&type%5B%5D=4&type%5B%5D=5&lang=ru' -H 'X-Requested-With: XMLHttpRequest' --compressed
# шлет аналогичный запрос с использованием requests и ответ (response объект из requests) возвращает
def getRequestsResponseByCurlBashCommand(curl_bash_command):

    # Преобразовываем в список аргументов, в кавычках строка идет как один аргумент, даже если внутри нее пробел
    arg_index = 0
    curl_parts = curl_bash_command.split(' ')
    cur_parts_quoted = []
    while(arg_index!= len(curl_parts)):

        # если пробел внутри строки
        if curl_parts[arg_index].startswith("'"):
            cmd = curl_parts[arg_index]
            while not curl_parts[arg_index].endswith("'"):
                arg_index += 1
                cmd += " " + curl_parts[arg_index]
            cur_parts_quoted.append(cmd[1:-1])
            arg_index += 1

        else:
            cur_parts_quoted.append(curl_parts[arg_index])
            arg_index += 1

    # Извлпекаем параметры
    url = cur_parts_quoted[1]
    headers = []
    arg_index = 2
    while(arg_index!= len(cur_parts_quoted)):

        # если заголовок
        if cur_parts_quoted[arg_index] == '-H':
            headers.append(cur_parts_quoted[arg_index + 1])
            arg_index += 2

        elif cur_parts_quoted[arg_index] == '--compressed':
            headers.append('Accept-Encoding: gzip, deflate')
            arg_index += 1

        else:
            raise RuntimeError(u'Unknown argument: ' + cur_parts_quoted[arg_index])

    headers_dict = dict((h.split(':', 1)[0], h.split(':', 1)[1].strip()) for h in headers)

    from requests import Request, Session
    s = Session()
    req = Request('get', url, headers=headers_dict)
    prepped = req.prepare()
    return s.send(prepped)



#Функция для получения адреса в формате: Киев, ул. Артема, 53
def getAddress(name, address, map_list):
    # Заменяем в адресе символы /
    def parseAddress(addr):
        addr = addr.replace('/', ', ')
        return addr

    full_addr = address
    for item in map_list:
        if item['name'] == name and item['address'] == address:
            full_addr = u'{0}, {1}'.format(item['cityApi'], parseAddress(address))

    return unicode(full_addr)


# Удаление двойных пробелов
def remDblSpace(num_str):
    while '  ' in num_str:
        num_str = num_str.replace('  ', ' ')
    return num_str


# Фунцкция формирует строку вывода телефонов по шаблону.
def phoneToTemplate(phones, is_str=False):
    phone_tmpl = u'''
        <phone>
            <ext/><type>phone</type>
            <number>{phone}</number>
            <info/>
        </phone>'''
    res = u''
    # Если телефон - строка
    if is_str is True:
        res = phone_tmpl.format(phone=unicode(phones).replace("\\",""))
        return res
    if len(phones) == 0:
        return phone_tmpl.format(phone=u'')
    for phone in phones:
        res += phone_tmpl.format(phone=unicode(phone))
    return res


# Из телефонов разделенных запятой, получаем список телефонов
def getPhones(phones_str):
    #Если телефон строка то записываем строку без изменений
    if len(re.findall(r'\d', phones_str)) < 7:
        return phoneToTemplate(phones_str, is_str=True)
    res = ''
    phones_str = unicode(phones_str)
    phones_list = phones_str.replace('-', ' ').split(',')
    for phone in phones_list:
        phone = phone.strip()
        # Проверяем если телефон начинается на (, есть телефоны у которых код города не выделен в номере
        if phone.startswith(u'('):
            res += getPhone(unicode(phone))
        else:
            # Приводим строку к виду телефона на сайте
            phone = phone.replace('(', '').replace(')', '').replace(' ', '')
            n_p = u'({0}) {1}-{2}-{3}'.format(phone[:2], phone[2:5], phone[5:7], phone[7:])
            res += getPhone(n_p)
    return res


#Функция для приветедения номера телефона к виду: +380 (44) 389 40 43
def getPhone(phone_str):
    # Пустая строка
    if len(phone_str) == 0:
        return phoneToTemplate([phone_str])

    # Текст, а не номер телефона
    if len(re.findall(r'\d', phone_str)) < 7:
        return phoneToTemplate(phone_str, is_str=True)

    # Телефоны назделены ,
    if u',' in phone_str:
        phones = getPhones(unicode(phone_str))
        return phoneToTemplate(phones)



    # Удаляем дефисы, и двойные пробелы. Выдеяем код города и номер телефона
    phone_str = phone_str.replace('-', ' ').replace('  ', ' ')
    result = re.split(r'\)', phone_str, maxsplit=1)

    # У кода города удаем открывающую скобку и 0 вначале, если есть
    phone_code = result[0].replace('(0', '') if result[0].startswith('(0') else result[0].replace('(', '')

    # Получаем дополнительные номера, если есть. И удаляем записи о них из номера
    number = unicode(result[1])
    any_num = re.findall(r'\((\d{2})\)', result[1])

    for i in any_num:
        rm_str = '('+i+')'
        number = number.replace(rm_str, '')

    number = number.strip()
    number = remDblSpace(number)
    phone = u'+380 ({0}) {1}'.format(phone_code, number)

    any_nums = []
    # Формиреут номера полного формата из дополнительных номеров
    for i in any_num:
        any_nums.append(u'+380 ({0}) {1}'.format(phone_code, number[:-len(i)]+i))

    return phoneToTemplate([phone]+any_nums)



resp = getRequestsResponseByCurlBashCommand("curl 'http://www.mbank.kiev.ua/jscripts/ajax/list_serialize.php?city=1000%3F%3E&q=&type%5B%5D=1&type%5B%5D=2&type%5B%5D=3&type%5B%5D=4&type%5B%5D=5&lang=ru' -H 'X-Requested-With: XMLHttpRequest'")
soup = getSoupByHtml(decodeUniCharsAndSlashed(resp.content))

# Получаем список банкоматов на укр. языке
resp_ua = getRequestsResponseByCurlBashCommand("curl 'http://www.mbank.kiev.ua/jscripts/ajax/list_serialize.php?city=1000%3F%3E&q=&type%5B%5D=1&type%5B%5D=2&type%5B%5D=3&type%5B%5D=4&type%5B%5D=5&lang=ua' -H 'X-Requested-With: XMLHttpRequest'")
soup_ua = getSoupByHtml(decodeUniCharsAndSlashed(resp_ua.content))

# Получаем список банкоматов с кооринатами из карты. Нужно для определения города, для формирования полного адреса
resp_map = getRequestsResponseByCurlBashCommand("curl 'http://www.mbank.kiev.ua/jscripts/ajax/map_serialize.php?city=1000%3F%3E&q=&type%5B%5D=3&type%5B%5D=4&lang=ru' -H 'Pragma: no-cache' -H 'Accept-Encoding: gzip, deflate, sdch' -H 'Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4' -H 'User-Agent: Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Referer: http://www.mbank.kiev.ua/ru/kontakty/otdelenija-i-ofisy_kontakty.htm?csrf_token=e3b80d30a727c738f3cff0941f6bc55a&city=1000%3F%3E&q=&type%5B%5D=2' -H 'X-Requested-With: XMLHttpRequest' -H 'Cookie: PHPSESSID=f4ed9f095dd90ef6bfc1188701f84a17; __gfp_64b=b513EPIZ16THR11b0scw3_mstSGMrhvlXRsBNa7ACDL.g7; mbank_fb_like_box=on; _gat=1; _ga=GA1.3.1378111883.1444661498; _ym_visorc_23286403=w' -H 'Connection: keep-alive' -H 'Cache-Control: no-cache' --compressed")
json_map = simplejson.loads(resp_map.content)
resp_map_ua = getRequestsResponseByCurlBashCommand("curl 'http://www.mbank.kiev.ua/jscripts/ajax/map_serialize.php?city=1000%3F%3E&q=&type%5B%5D=3&type%5B%5D=4&lang=ua' -H 'Pragma: no-cache' -H 'Accept-Encoding: gzip, deflate, sdch' -H 'Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4' -H 'User-Agent: Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Referer: http://www.mbank.kiev.ua/ru/kontakty/otdelenija-i-ofisy_kontakty.htm?csrf_token=e3b80d30a727c738f3cff0941f6bc55a&city=1000%3F%3E&q=&type%5B%5D=2' -H 'X-Requested-With: XMLHttpRequest' -H 'Cookie: PHPSESSID=f4ed9f095dd90ef6bfc1188701f84a17; __gfp_64b=b513EPIZ16THR11b0scw3_mstSGMrhvlXRsBNa7ACDL.g7; mbank_fb_like_box=on; _gat=1; _ga=GA1.3.1378111883.1444661498; _ym_visorc_23286403=w' -H 'Connection: keep-alive' -H 'Cache-Control: no-cache' --compressed")
json_map_ua = simplejson.loads(resp_map_ua.content)

# Банкомат              1 184105402
# платежный терминал    2 184106974
# Рубринка банк         3,4,5 184105398

requestet_type_mbank_num = sys.argv[1].split(',')
requested_type_category = sys.argv[2]
requested_company_id = sys.argv[3]

print """<?xml version="1.0" encoding="UTF-8"?>"""
print """<companies xmlns:xi="http://www.w3.org/2001/XInclude" version="2.1">"""

for row, row_ua in zip(soup.find_all(name='tr'), soup_ua.find_all(name='tr')):

    tds = row.find_all(name='td')
    tds_ua = row_ua.find_all(name='td')

    type_png = row.find(name='img').get('src')
    type_png_ua = row_ua.find(name='img').get('src')

    if any([type_png.endswith('{0}.png'.format(n)) for n in requestet_type_mbank_num]) \
            and any([type_png_ua.endswith('{0}.png'.format(n)) for n in requestet_type_mbank_num]):

        company = u"""    <company>
        <name lang="ru">{name}</name>
        <name lang="ua">{name_ua}</name>
        <address-add lang="ru">{address_add}</address-add>
        <address-add lang="ua">{address_add_ua}</address-add>
        <address lang="ru">{address}</address>
        <address lang="ua">{address_ua}</address>{phone}
        <working-time lang="ru">{wtime}</working-time>
        <working-time lang="ua">{wtime_ua}</working-time>
        <rubric-id>{rubric}</rubric-id>
        <company-id>{company_id}</company-id>
        <actualization-date>{actualization_date}</actualization-date>
        <url>{url}</url>
    </company>
"""

        address = getAddress(unicode(tds[0].find(name=u'span').get_text()), unicode(tds[1].get_text()), json_map)
        address_ua = getAddress(unicode(tds_ua[0].find(name=u'span').get_text()), unicode(tds_ua[1].get_text()), json_map_ua)

        name = unicode(u'Банк Михайловский, {0}'.format(unicode(tds[0].find(name=u'span').get_text()))) \
            if type_png.endswith(u'3.png') else unicode(u'Банк Михайловский, {0}'.format(u'мини-офис'))
        name_ua = unicode(u'Банк Михайлівський, {0}'.format(unicode(tds_ua[0].find(name=u'span').get_text()))) \
            if type_png_ua.endswith(u'3.png') else unicode(u'Банк Михайлівський, {0}'.format(u'міні-офіс'))

        print company.format(
            name=name,
            name_ua=name_ua,
            address=address,
            address_ua=address_ua,
            address_add=unicode(tds[0].find(name=u'span').get_text()),
            address_add_ua=unicode(tds_ua[0].find(name=u'span').get_text()),
            phone=getPhones(unicode(tds[3].get_text())) if u',' in unicode(tds[3].get_text()) else getPhone(unicode(tds[3].get_text())),
            wtime=unicode(tds[4].get_text()),
            wtime_ua=unicode(tds_ua[4].get_text()),
            rubric=unicode(requested_type_category),
            company_id=unicode(requested_company_id),
            actualization_date=unicode(datetime.datetime.utcnow().strftime('%d.%m.%Y')),
            url=unicode(u'http://www.mbank.kiev.ua')
        )

print """</companies>"""
