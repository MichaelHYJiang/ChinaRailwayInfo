#!usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import os

import numpy as np
import requests

#from station import stations_dict

TRAIN_LIST_FILE = 'train_list.txt'
TRAIN_LIST_URL = 'https://kyfw.12306.cn/otn/resources/js/query/train_list.js?scriptVersion=1.0'

class ClockTime:
    """
    ClockTime class stores two numbers indicating hours and minutes.
    Two instances of ClockTime can calculate together.
    e.g.:
        t1 = ClockTime(10, 20)
        t2 = ClockTime("11:19")
        past_time = t2.minus(t1) # which is 59
    """

    def __init__(self, h, m = None):
        """
        Constructor of the class, that can either take two parameters
        as hour and minuts; or take one parameter that is a string of 
        format "%d:%d"
        """
        if m == None:
            text = h
            h, m = self.str2ct(text)
        if h >= 24 or h < 0 or m >= 60 or m < 0:
            print 'error: illegal hour or minute'
            print 'h:', h
            print 'm:', m
            return
        self.hour = h
        self.min = m


    def str2ct(self, text):
        t = text.split(':')
        if len(t) != 2:
            return 0, 0
        try:
            h = int(t[0])
            m = int(t[1])
        except ValueError as err:
            print 'ValueError in clocktime class:', err
            return 0, 0
        return h, m

    def minus(self, lt):
        if self.min < lt.min:
            m = self.min + 60
            h = self.hour - 1
        else:
            m = self.min
            h = self.hour
        if h < 0:
            h += 24
        return (h - lt.hour) * 60 + (m - lt.min)

class TrainList:


    def __init__(self):
        if TRAIN_LIST_FILE not in os.listdir('.'):
            self.get_train_list()
        with open('train_list.txt', 'rb') as f:
            train_list = f.readlines()
        train_list = train_list[0][16::]
        train_list = json.loads(train_list)
        self.date = train_list.keys()[int(np.random.rand() * len(train_list))]
        self.train_list = train_list[self.date]
        
    def get_train_list(self):
        """Download train list data and save them in TRAIN_LIST_FILE
        """
        requests.packages.urllib3.disable_warnings()
        requests.adapters.DEFAULT_RETRIES = 5
        response = requests.get(TRAIN_LIST_URL, stream = True,verify = False)
        status = response.status_code
        if status == 200:
            with open(TRAIN_LIST_FILE, 'wb') as of:
                for chunk in response.iter_content(chunk_size = 102400):
                    if chunk:
                        of.write(chunk)
    # TODO

init_url = 'https://kyfw.12306.cn/otn/queryTrainInfo/init'
HEADERS = {'Accept': 'text/html, application/xhtml+xml, image/jxr, */*',
               'Accept - Encoding':'gzip, deflate',
               'Accept-Language':'zh-Hans-CN, zh-Hans; q=0.5',
               'Connection':'Keep-Alive',
               'Host':'zhannei.baidu.com',
               'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063'}


def getStationCode():
    #关闭https证书验证警告
    requests.packages.urllib3.disable_warnings()
    # 12306的城市名和城市代码js文件url
    url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9046'
    r = requests.get(url,verify=False)
    pattern = u'([\u4e00-\u9fa5]+)\|([A-Z]+)'
    result = re.findall(pattern,r.text)
    station = dict(result)
    print station

        
def get_query_url(text):
    '''
    返回调用api的url链接
    '''
    # 解析参数 aggs[0]里是固定字符串：车票查询 用于匹配公众号接口
    text = text.encode('utf8')
    args = str(text).split(' ')
    try:
        date = args[0] 
        from_station_name = args[1].decode('utf-8') 
        to_station_name = args[2].decode('utf-8')
        from_station = stations_dict[from_station_name]
        to_station = stations_dict[to_station_name]
    except:
        date,from_station,to_station='--','--','--' 
    #将城市名转换为城市代码
    
    # api url 构造
    url = (
        'https://kyfw.12306.cn/otn/leftTicket/queryZ?'
        'leftTicketDTO.train_date={}&'
        'leftTicketDTO.from_station={}&'
        'leftTicketDTO.to_station={}&'
        'purpose_codes=ADULT'
    ).format(date, from_station, to_station)
    #print url
    
    return url

def query_train_info(url):
    '''
    查询火车票信息：
    返回 信息查询列表
    '''

    info_list = []
    try:
        r = requests.get(url, verify=False)
        # 获取返回的json数据里的data字段的result结果
        print 'mark'
        if r.status_code != 200:
            return ['Error: status code is %d' % r.status_code]
        raw_trains = json.loads(r.content)['data']['result']
        
        for raw_train in raw_trains:
            # 循环遍历每辆列车的信息
            data_list = raw_train.split('|')

            # 车次号码
            train_no = data_list[3]
            # 出发站
            from_station_code = data_list[6]
            from_station_name = code_dict[from_station_code.decode('utf8')]
            # 终点站
            to_station_code = data_list[7]
            to_station_name = code_dict[to_station_code.decode('utf8')]
            # 出发时间
            start_time = data_list[8]
            # 到达时间
            arrive_time = data_list[9]
            # 总耗时
            time_fucked_up = data_list[10]
            # 一等座
            first_class_seat = data_list[31] or '--'
            # 二等座
            second_class_seat = data_list[30]or '--'
            # 软卧
            soft_sleep = data_list[23]or '--'
            # 硬卧
            hard_sleep = data_list[28]or '--'
            # 硬座
            hard_seat = data_list[29]or '--'
            # 无座
            no_seat = data_list[26]or '--'

            # 打印查询结果
            info = u'车次:%s\n出发站:%s\n目的地:%s\n出发时间:%s\n到达时间:%s\n消耗时间:%s\n座位情况：\n 一等座：「%s」 \n二等座：「%s」\n软卧：「%s」\n硬卧：「%s」\n硬座：「%s」\n无座：「%s」\n\n' % (
                train_no, from_station_name, to_station_name, start_time, arrive_time, time_fucked_up, first_class_seat,
                second_class_seat, soft_sleep, hard_sleep, hard_seat, no_seat)

            info_list.append(info)

        return info_list
    except:
        return u'输出信息有误，请重新输入'
        
        

def main():
    #getTrain_list()
    #trainListStartToEnd()
    #for x in station_start_end_set:
    #    print x
    #getStationCode()
    requests.packages.urllib3.disable_warnings()
    #print stations_dict
    code_dict = {v: k for k, v in stations_dict.items()}
    print code_dict[u'HKN']
    print code_dict[u'NKH']
    print code_dict[u'AOH']
    url = get_query_url(u'2018-02-02 武汉 南京')
    
    info = query_train_info(url)
    print 'len(info_list):', len(info)
    print '\n' * 2 + '=' * 20
    for i in info[0:10]:
        print i, '\n' + '=' * 20


if __name__ == '__main__':
    #getTrain_list()
    requests.packages.urllib3.disable_warnings()
    train_list = TrainList()
    
    ###
    print train_list.train_list.keys()
    print train_list.date
    a = '''
    for trainType in train_list.keys():
        trains = train_list[trainType]
        print len(trains)
        for train in trains:
            station_train_code = train[u'station_train_code']
            train_no = train[u'train_no']
            pattern = re.compile(r'\((.*)-(.*)\)')
            match = pattern.search(station_train_code)
            from_station_name = match.groups()[0]
            to_station_name = match.groups()[1]
            try:
                from_station = stations_dict[from_station_name]
                to_station = stations_dict[to_station_name]
            except KeyError as e:
                print e
                os.system('pause')
                break
            url = (
                'https://kyfw.12306.cn/otn/czxx/queryByTrainNo?''train_no={}&'
                'from_station_telecode={}&'
                'to_station_telecode={}&'
                'depart_date={}'
            ).format(train_no, from_station, to_station, date)
            #print url
            r = requests.get(url, verify=False)
            print r.status_code
            data = json.loads(r.content)[u'data'][u'data']
            print len(data)
            if len(data) == 0:
                print station_train_code
                continue
            print data[0][u'station_name'],
            last = clocktime(data[0][u'start_time'])
            for i in range(1, len(data)):
                now = clocktime(data[i][u'arrive_time'])
                delta = now.minus(last)
                last = clocktime(data[i][u'start_time'])
                print '--', delta, '--', data[i][u'station_name'],
            print ''
            os.system('pause')'''
