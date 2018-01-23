#!usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re
import json

from station import stations_dict

station_start_end_set = set()
train_list_url = 'https://kyfw.12306.cn/otn/resources/js/query/train_list.js?scriptVersion=1.0'
init_url = 'https://kyfw.12306.cn/otn/queryTrainInfo/init'
HEADERS = {'Accept': 'text/html, application/xhtml+xml, image/jxr, */*',
               'Accept - Encoding':'gzip, deflate',
               'Accept-Language':'zh-Hans-CN, zh-Hans; q=0.5',
               'Connection':'Keep-Alive',
               'Host':'zhannei.baidu.com',
               'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063'}


#下载所有的车次数据  保存为 train_list.txt文件  
def getTrain_list():  
    requests.packages.urllib3.disable_warnings()
    requests.adapters.DEFAULT_RETRIES = 5  
    response = requests.get(train_list_url, stream=True,verify=False)  
    status = response.status_code  
    if status == 200:  
        with open('train_list.txt', 'wb') as of:  
            for chunk in response.iter_content(chunk_size=102400):  
                if chunk:  
                    of.write(chunk)  
  
  
#分析train_list.txt文件 得出火车 出发站到终点站的数据  
def trainListStartToEnd():  
    global station_start_end_set  
    with open('train_list.txt','rb') as of:  
        text=of.readline()  
        tt=text.decode("utf-8")  
        ss=tt.replace("},{","}\n{").replace("2018-","\n").replace("[","\n").split("\n")  
        m_list=list()  
        for s in ss:  
            pattern = re.compile(u'([\u2E80-\u9FFF]+-[\u2E80-\u9FFF]+)')
            match = pattern.search(s)  
            if match:  
                m_list.append(match.group(1))  
        station_start_end_set=set(m_list)
        
        
        #https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9046

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
#利用出发站到终点站 爬取期间的列车数据  
def getTrainNoList(back_date,train_date,from_station,from_station_name,to_station,to_station_name):  
    post_data= {'back_train_date':back_date,  
                '_json_att':"",'flag':'dc',  
                'leftTicketDTO.from_station':from_station,  
                'leftTicketDTO.to_station':to_station,  
                'leftTicketDTO.from_station_name':from_station_name,  
                'leftTicketDTO.to_station_name':to_station_name,  
                'leftTicketDTO.train_date':train_date,  
                'pre_step_flag':'index',  
                'purpose_code':'ADULT'}  
  
    #init_resp=requests.post(init_url,data=post_data,headers=HEADERS,allow_redirects=True,verify=False)  
    #cookies=init_resp.cookies  
    #cookies.set('_jc_save_fromStation', from_station_name+','+from_station, domain='kyfw.12306.cn', path='/')  
    #cookies.set('_jc_save_toStation', to_station_name+','+to_station, domain='kyfw.12306.cn', path='/')  
    #cookies.set('_jc_save_fromDate', train_date, domain='kyfw.12306.cn', path='/')  
    #cookies.set('_jc_save_toDate', back_date, domain='kyfw.12306.cn', path='/')  
    #cookies.set('_jc_save_wfdc_flag', 'dc', domain='kyfw.12306.cn', path='/')  
    query_url = 'https://kyfw.12306.cn/otn/leftTicket/queryZ?'
    url=query_url+"leftTicketDTO.train_date="+train_date+"&leftTicketDTO.from_station="+from_station+"&leftTicketDTO.to_station="+to_station+"&purpose_codes=ADULT"  
    print url
    try:  
        response = requests.get(url, headers=HEADERS, allow_redirects=True,verify=False,timeout=10)  
        data=""  
        if response.status_code==200:  
            data=response.content  
        data=data.decode("UTF-8")  
        return data
    except  Exception as err:  
        print 'getTrainNoList error 获取车次列表错误 日期'+train_date+'从'+from_station_name+'到'+to_station_name+' :%s' % err  
        return None
        
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
    print url
    
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
        print r.status_code
        raw_trains = json.loads(r.content)['data']['result']

        print r'len(raw_trains):', len(raw_trains)
        
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
        
        
if __name__ == '__main__':
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
    
    #info = query_train_info(url)
    #print 'len(info_list):', len(info)
    #for i in info:
    #    print i, '\n' + '=' * 20
    #data = getTrainNoList('2018-02-10', '2018-02-02', 'ASY','1', 'AEM', '2')
    #print data
    #永寿    ASY
#羊者窝  AEM
