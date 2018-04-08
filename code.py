# -*- coding: utf-8 -*-
"""
Created on Tue Mar 20 09:11:39 2018

@author: peter
"""

from concurrent import futures
import time
import threading
import sqlite3
import requests
result = []
lock = threading.Lock()
total = 1
conn = None
cookie = {'domain': '/',
          'expires': 'false',
          'httpOnly': 'false',
          'name': 'buvid3',
          'path': 'Fri, 29 Jan 2021 08:50:10 GMT',
          'value': '7A29BBDE-VA94D-4F66-QC63-D9CB8568D84331045infoc,bilibili.com'}

uas = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 \
       like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 \
       Mobile/14E5239e Safari/602.1'


def create():
    # 创建数据库
    global conn
    conn = sqlite3.connect('data.db')
    conn.execute("""
  create table if not exists bilibili_user_info(
  id int prinmary key autocrement ,
  mid varchar DEFAULT NULL,
  name varchar DEFAULT NULL,
  sex varchar DEFAULT NULL,
  following int DEFAULT NULL,
  fans int DEFAULT NULL,
  level int DEFAULT NULL)""")


def run(url):
    # 启动爬虫
    global total, result, uas, cookie
    mid = url.replace('https://m.bilibili.com/space/', '')
    head = {'User-Agent': uas,
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'http://space.bilibili.com',
            'Host': 'm.bilibili.com',
            'AlexaToolbar-ALX_NS_PH': 'AlexaToolbar/alx-4.0',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': url}
    time.sleep(0.5)     # 延迟，避免太快 ip 被封
    try:
        r = requests.get(url, headers=head, cookies=cookie, timeout=10).text
        if r.find("name\":") == -1:
            return
        name = r[r.find("name\":")+7:r.find('\",\"approve\"')]
        sex = r[r.find('\"sex\":\"')+7:r.find('\",\"rank')]
        if r.find('lv0') != -1:
            level = 0
        elif r.find('lv1') != -1:
            level = 1
        elif r.find('lv2') != -1:
            level = 2
        elif r.find('lv3') != -1:
            level = 3
        elif r.find('lv4') != -1:
            level = 4
        elif r.find('lv5') != -1:
            level = 5
        elif r.find('lv6') != -1:
            level = 6
        else:
            level = -1
        head = {'User-Agent': uas,
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'http://space.bilibili.com',
                'Host': 'api.bilibili.com',
                'AlexaToolbar-ALX_NS_PH': 'AlexaToolbar/alx-4.0',
                'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Referer': url}
        res = requests.get('https://api.bilibili.com/x/relation/stat?jsonp=jsonp&vmid='+str(mid),
                           headers=head, cookies=cookie, timeout=10).text
        res_js = eval(res)
        following = res_js['data']['following']
        follower = res_js['data']['follower']
        users = (total, mid, name, sex, following, follower, level)
    except Exception as e:
        print('error')
        print(e)
        print(i)
        print(total)
        return
    with lock:
        result.append(users)
        print(i)
        print(total)
        total += 1


def save():
    # 将数据保存至本地
    global result, conn, flag, total
    command = "insert into bilibili_user_info \
             values(?,?,?,?,?,?,?);"
    for row in result:
        try:
            conn.execute(command, row)
        except Exception as e:
            print(e)
            conn.rollback()
    conn.commit()
    result = []


if __name__ == "__main__":
    create()
    total_num = 300000000
    num = 32*20
    for i in range(1, int(1*total_num/num)):
        begin = num * i
        urls = ["https://m.bilibili.com/space/{}".format(j)
                for j in range(begin, begin + num)]
#        while len(urls)>=1:
#            url=urls.pop()
#            run(url)
        with futures.ThreadPoolExecutor(10) as executor:
            executor.map(run, urls)
        save()
    conn.close()
