import re
import urllib3
import time
import json
import random
import pandas as pd
from urllib import parse
from datetime import datetime,timedelta
from requests_html import HTMLSession

urllib3.disable_warnings()


def get_spider_config():
    # 获取爬虫配置信息
    with open('spider_config.json', encoding='utf-8') as fp:
        spider_config = json.load(fp)
        basic_setting = spider_config['basic_setting']
        try:
            crawl_by_user_setting = spider_config['crawl_by_user_setting']
        except:
            crawl_by_user_setting = None
        try:
            crawl_by_keyword_setting = spider_config['crawl_by_keyword_setting']
        except:
            crawl_by_keyword_setting = None
    return basic_setting, crawl_by_user_setting, crawl_by_keyword_setting


def get_session_list(SLUser_list):
    # 模拟登录手机微博客户端，获取可爬取数据的session列表
    session_list = []
    for user_name,password in SLUser_list:
        session = HTMLSession(verify=False)
        login_url = 'https://passport.weibo.cn/sso/login'
        index_url = 'https://weibo.cn/'
        session.headers['Referer'] = 'https://passport.weibo.cn/signin/login?entry=mweibo&r=https%3A%2F%2Fweibo.cn&u=katandsid&_T_WM=4befa55f33b8759eee01d119fdcd678e'
        data = {'username': user_name,'password': password,'savestate': '1','r': 'https://weibo.cn','ec': '0','pagerefer': '','entry': 'mweibo','wentry': '','loginfrom': '','client_id': '','code': '','qq': '','mainpageflag': '1','hff': '','hfp': ''}
        session.post(login_url, data=data)
        resp = session.get(index_url)
        try:
            nick_name = re.findall('class="ut">(.*?)<a', resp.text)[0]
            if nick_name:
                print('{}登陆成功,将session加入列表'.format(nick_name))
                session_list.append(session)
            else:
                print('{}账号登录异常!'.format(user_name))
        except:
            print('连接失败！')
    return session_list


class WeiboCrawler():

    def __init__(self, session_list):

        self.session_list = session_list
        self.personal_information_dict = {'用户ID':[],'用户名':[],'更新时间':[],'昵称':[],'性别':[],'地址':[],'微博数量':[],'关注数量':[],'粉丝数量':[]}
        self.keyword_information_dict = {'数据截止时间':[],'关键词': [], '同名关键词微博数量': [], '同名关键词原创微博数量': [],  '包含关键词微博数量': [], '包含关键词原创微博数量': []}
        self.weibo_text_byUser_dict = {'微博ID':[],'用户ID':[],'用户名':[],'创建时间':[],'来源':[],'是否原创':[],'微博内容':[],'点赞数量':[],'转发数量':[],'评论数量':[],'评论链接':[]}
        self.weibo_text_byKeyword_dict = {'数据截止时间':[],'关键词':[],'微博ID':[],'创建时间':[],'来源':[],'是否原创':[],'微博内容':[],'点赞数量':[],'转发数量':[],'评论数量':[],'评论链接':[]}

    def _get_normal_datetime(self, datetime_str):
        # 提取微博标准的日期时间
        if '分钟前' in datetime_str:
            minute_number = int(re.findall(r'(.*)分钟前', datetime_str)[0])
            normal_datetime = (datetime.now() - timedelta(minutes=minute_number)).strftime('%Y-%m-%d %H:%M:%S')
        elif '今天' in datetime_str:
            time_str = re.findall(r'(\d{2}:\d{2})', datetime_str)[0]
            normal_datetime = '{} {}:00'.format(datetime.now().strftime('%Y-%m-%d'),time_str)
        elif '月' in datetime_str:
            datetime_tuple = re.findall(r'(\d{2})月(\d{2})日 (\d{2}:\d{2})', datetime_str)[0]
            normal_datetime = '{}-{}-{} {}:00'.format(datetime.now().year, datetime_tuple[0], datetime_tuple[1],datetime_tuple[2])
        else:
            normal_datetime = datetime_str.strip()
        return normal_datetime

    def _request_data(self, url):
        #请求数据
        session = random.choice(self.session_list)
        try:
            resp = session.get(url,timeout = 8)
        except Exception as e:
            print('{}请求数据失败,原因是\n{}'.format(url,e))
            return None
        else:
            if resp.status_code == 200:
                return resp.text
            else:
                print('{}数据请求错误，状态码是{}'.format(url,resp.status_code))
                return None

    def _save_data(self, data_type, keyword_type=None):
        # 保存微博抓取数据值xlsx文件
        if data_type == 'personal_information':
            print('保存微博个人信息数据！')
            df_personal_information = pd.DataFrame(self.personal_information_dict)
            df_personal_information['更新时间'] = pd.to_datetime(df_personal_information['更新时间'])     # 将日期时间字符串转化为日期时间
            df_personal_information.to_excel(excel_writer=writer, sheet_name='个人信息')
        elif data_type == 'keyword_information':
            print('保存微博关键词统计信息！')
            df_keyword_information = pd.DataFrame(self.keyword_information_dict)
            df_keyword_information['数据截止时间'] = pd.to_datetime(df_keyword_information['数据截止时间'])  # 将日期时间字符串转化为日期时间
            df_keyword_information.to_excel(excel_writer=writer, sheet_name='关键词统计信息')
        elif data_type == 'weibo_text_byUser':
            print('保存微博数据_用户ID！')
            df_weibo_text_byUser = pd.DataFrame(self.weibo_text_byUser_dict)
            df_weibo_text_byUser['创建时间'] = pd.to_datetime(df_weibo_text_byUser['创建时间'])
            df_weibo_text_byUser.to_excel(excel_writer=writer, sheet_name='微博正文数据_用户ID')
        elif data_type == 'weibo_text_byKeyword':
            print('保存微博数据_关键词！')
            df_weibo_text_byKeyword = pd.DataFrame(self.weibo_text_byKeyword_dict )
            df_weibo_text_byKeyword['创建时间'] = pd.to_datetime(df_weibo_text_byKeyword['创建时间'])
            df_weibo_text_byKeyword['数据截止时间'] = pd.to_datetime(df_weibo_text_byKeyword['数据截止时间'])  # 将日期时间字符串转化为日期时间
            if keyword_type == 0:
                df_weibo_text_byKeyword.to_excel(excel_writer=writer, sheet_name='微博正文数据_包含关键词')
            if keyword_type == 1:
                df_weibo_text_byKeyword.to_excel(excel_writer=writer, sheet_name='微博正文数据_包含关键词原创')
            if keyword_type == 2:
                df_weibo_text_byKeyword.to_excel(excel_writer=writer, sheet_name='微博正文数据_同名关键词')
            if keyword_type == 3:
                df_weibo_text_byKeyword.to_excel(excel_writer=writer, sheet_name='微博正文数据_同名关键词原创')
        else:
            print('暂不支持保存的数据类型！')

    def _parse_weibo_text(self, weibo_text):
        # 解析微博正文
        try:
            text_id = weibo_text[0]
            is_original = '否' if '转发' in weibo_text[1].strip() else '是'
            text = weibo_text[1].strip()
            create_time = self._get_normal_datetime(weibo_text[6])
            source = weibo_text[6].split('&nbsp;')[1] if '&nbsp;' in weibo_text[6] else None
            like_quantity = int(weibo_text[2])
            forward_quantity = int(weibo_text[3])
            comment_quantity = int(weibo_text[5])
            comment_url = weibo_text[4].strip()
            return text_id, is_original, text, create_time, source, like_quantity, forward_quantity, comment_quantity, comment_url
        except:
            return None

    def get_personal_information(self, user_list):
        # 获取微博个人信息
        weibo_text_start_list = []
        for abbr_name,user_id in user_list:
            abbr_name = abbr_name.capitalize()
            index_url = 'https://weibo.cn/{}/profile'.format(user_id)
            content = self._request_data(index_url)
            if not content: continue     #请求失败，循环中断
            max_page = int(re.findall(r'"跳页".*?/(\d{1,10})页', content)[0]) - 1  # 微博正文最大页码
            weibo_text_start_list.append((abbr_name, user_id, max_page))  # 加入微博正文启动列表
            try:
                personal_information_list = re.findall(r'class="ut"><span class="ctt">(.*?)<.*?&nbsp;(.*?)/(.*?)&nbsp.*?微博\[(.*?)\].*?关注\[(.*?)\].*?粉丝\[(.*?)\]',content, re.S)[0]
            except Exception as e:
                print('微博个人信息解析错误，原因是：{}'.format(e))
            else:
                update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                nick_name = personal_information_list[0].strip()
                if personal_information_list[1].strip() == '男':
                    sex = '男'
                elif personal_information_list[1].strip() == '女':
                    sex = '女'
                else:
                    sex = '未知'
                place = personal_information_list[2].strip()
                weibo_text_quantity = int(personal_information_list[3].strip())
                attention_quantity = int(personal_information_list[4].strip())
                fan_quantity = int(personal_information_list[5].strip())
                self.personal_information_dict['用户ID'].append(user_id)
                self.personal_information_dict['用户名'].append(abbr_name)
                self.personal_information_dict['更新时间'].append(update_time)
                self.personal_information_dict['昵称'].append(nick_name)
                self.personal_information_dict['性别'].append(sex)
                self.personal_information_dict['地址'].append(place)
                self.personal_information_dict['微博数量'].append(weibo_text_quantity)
                self.personal_information_dict['关注数量'].append(attention_quantity)
                self.personal_information_dict['粉丝数量'].append(fan_quantity)
                print('-------------------------已获取<{}>微博个人信息-------------------------'.format(abbr_name))
                print(user_id,abbr_name,update_time,nick_name,sex,place,weibo_text_quantity,attention_quantity,fan_quantity,sep='\t')
                time.sleep(random.randint(min_delay,max_delay))
        return weibo_text_start_list

    def crawl_weibo_by_user(self, user_list, crawl_pages, filter="1"):
        # 抓取微博正文数据通过用户ID
        if user_list: weibo_text_start_list = self.get_personal_information(user_list)
        if weibo_text_start_list:
            for abbr_name, user_id, max_page in weibo_text_start_list:
                pages = crawl_pages + 1 if crawl_pages <= max_page else max_page + 1
                for page in range(1, pages):
                    url = 'https://weibo.cn/{}/profile?filter={}&page={}'.format(user_id,filter,str(page))
                    content = self._request_data(url)
                    if not content: break     #请求失败，循环中断
                    pattern = r'id="([A-Z]_\w{6,15})".*?class="ctt">(.*?)</span>.*?赞\[(.*?)\].*?转发\[(.*?)\].*?href="(.*?)".*?评论\[(.*?)\].*?class="ct">(.*?)</span>'
                    weibo_text_list = re.findall(pattern, content,re.S)
                    if not weibo_text_list:continue     #未提取到数据，跳出本次循环
                    for index, weibo_text in enumerate(weibo_text_list):
                        if self._parse_weibo_text(weibo_text):
                            text_id, is_original, text, create_time, source, like_quantity, forward_quantity, comment_quantity, comment_url = self._parse_weibo_text(weibo_text)
                            self.weibo_text_byUser_dict['微博ID'].append(text_id)
                            self.weibo_text_byUser_dict['用户ID'].append(user_id)
                            self.weibo_text_byUser_dict['用户名'].append(abbr_name)
                            self.weibo_text_byUser_dict['创建时间'].append(create_time)
                            self.weibo_text_byUser_dict['来源'].append(source)
                            self.weibo_text_byUser_dict['是否原创'].append(is_original)
                            self.weibo_text_byUser_dict['微博内容'].append(text)
                            self.weibo_text_byUser_dict['点赞数量'].append(like_quantity)
                            self.weibo_text_byUser_dict['转发数量'].append(forward_quantity)
                            self.weibo_text_byUser_dict['评论数量'].append(comment_quantity)
                            self.weibo_text_byUser_dict['评论链接'].append(comment_url)
                            print('-------------------------已获取<{}>的第{}页第{}条微博正文信息-------------------------'.format(abbr_name, page, index+1))
                    time.sleep(random.randint(min_delay, max_delay))  #延时请求
            self._save_data('personal_information')
            self._save_data('weibo_text_byUser')

    def get_keyword_information(self, keyword, keyword_type):
        # 获取关键词统计信息
        keword_url_list = [
            'https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}'.format(parse.quote(keyword)),
            'https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}&filter=hasori'.format(parse.quote(keyword)),
            'https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}'.format(parse.quote('#{}#'.format(keyword))),
            'https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}&filter=hasori'.format(parse.quote('#{}#'.format(keyword)))
        ]
        for index, url in enumerate(keword_url_list):
            content = self._request_data(url)
            if not content: break  # 请求失败，循环中断
            try:
                number = int(re.findall(r'共(.*?)条', content, re.S)[0])
            except:
                print('未找到微博关键词相关数据！')
                number = 0
            finally:
                if index == 0:
                    self.keyword_information_dict['包含关键词微博数量'].append(number)
                    print('-----已获取到关键词{}的包含关键词微博数量{}-----'.format(keyword, number))
                elif index == 1:
                    self.keyword_information_dict['包含关键词原创微博数量'].append(number)
                    print('-----已获取到关键词{}的包含关键词原创微博数量{}-----'.format(keyword, number))
                elif index == 2:
                    self.keyword_information_dict['同名关键词微博数量'].append(number)
                    print('-----已获取到关键词{}的同名关键词微博数量{}-----'.format(keyword, number))
                elif index == 3:
                    self.keyword_information_dict['同名关键词原创微博数量'].append(number)
                    print('-----已获取到关键词{}的同名关键词原创微博数量{}-----'.format(keyword, number))
            time.sleep(random.randint(min_delay, max_delay))  # 延时请求
        if keyword_type == 0:
            return keword_url_list[keyword_type],self.keyword_information_dict['包含关键词微博数量'][-1]
        elif keyword_type == 1:
            return keword_url_list[keyword_type],self.keyword_information_dict['包含关键词原创微博数量'][-1]
        elif keyword_type == 2:
            return keword_url_list[keyword_type],self.keyword_information_dict['同名关键词微博数量'][-1]
        elif keyword_type == 3:
            return keword_url_list[keyword_type],self.keyword_information_dict['同名关键词原创微博数量'][-1]

    def crawl_weibo_by_keyword(self, keyword_list, crawl_pages, keyword_type=1):
        # 抓取微博正文数据通过关键词
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for keyword in keyword_list:
            self.keyword_information_dict['数据截止时间'].append(current_datetime)
            self.keyword_information_dict['关键词'].append(keyword)
            keword_url,max_page = self.get_keyword_information(keyword, keyword_type)
            pages = crawl_pages + 1 if crawl_pages <= max_page else max_page + 1
            for page in range(1, pages):
                url = '{}&page={}'.format(keword_url, str(page))
                content = self._request_data(url)
                if not content: break  # 请求失败，循环中断
                pattern = r'id="([A-Z]_\w{6,15})".*?class="ctt">(.*?)</span>.*?赞\[(.*?)\].*?转发\[(.*?)\].*?href="(.*?)".*?评论\[(.*?)\].*?class="ct">(.*?)</span>'
                weibo_text_list = re.findall(pattern, content, re.S)
                if not weibo_text_list: continue  # 未提取到数据，跳出本次循环
                for index, weibo_text in enumerate(weibo_text_list):
                    if self._parse_weibo_text(weibo_text):
                        text_id, is_original, text, create_time, source, like_quantity, forward_quantity, comment_quantity, comment_url = self._parse_weibo_text(weibo_text)
                        self.weibo_text_byKeyword_dict['数据截止时间'].append(current_datetime)
                        self.weibo_text_byKeyword_dict['关键词'].append(keyword)
                        self.weibo_text_byKeyword_dict['微博ID'].append(text_id)
                        self.weibo_text_byKeyword_dict['创建时间'].append(create_time)
                        self.weibo_text_byKeyword_dict['来源'].append(source)
                        self.weibo_text_byKeyword_dict['是否原创'].append(is_original)
                        self.weibo_text_byKeyword_dict['微博内容'].append(text)
                        self.weibo_text_byKeyword_dict['点赞数量'].append(like_quantity)
                        self.weibo_text_byKeyword_dict['转发数量'].append(forward_quantity)
                        self.weibo_text_byKeyword_dict['评论数量'].append(comment_quantity)
                        self.weibo_text_byKeyword_dict['评论链接'].append(comment_url)
                        print('-------------------------已获取<{}>的第{}页第{}条微博正文信息-------------------------'.format(keyword, page, index + 1))
                time.sleep(random.randint(min_delay, max_delay))  # 延时请求
        self._save_data('keyword_information')
        self._save_data('weibo_text_byKeyword',keyword_type)


def crawl_weibo_by_config():
    # 通过配置文件信息抓取微博数据
    global min_delay, max_delay
    basic_setting, crawl_by_user_setting, crawl_by_keyword_setting = get_spider_config()
    if basic_setting: SLUser_list, min_delay, max_delay = basic_setting['SLUser_list'], basic_setting['min_delay'], basic_setting['max_delay']
    session_list = get_session_list(SLUser_list)
    if session_list:
        weibo = WeiboCrawler(session_list)
        if crawl_by_user_setting: weibo.crawl_weibo_by_user(crawl_by_user_setting['user_list'],
                                                            crawl_by_user_setting['crawl_pages'],
                                                            crawl_by_user_setting['filter'])
        if crawl_by_keyword_setting: weibo.crawl_weibo_by_keyword(crawl_by_keyword_setting['keyword_list'],
                                                                  crawl_by_keyword_setting['crawl_pages'],
                                                                  crawl_by_keyword_setting['keyword_type'])


if __name__ == '__main__':

    writer = pd.ExcelWriter('weibo.xlsx')
    try:
        crawl_weibo_by_config()
    except:
        pass
    finally:
        writer.save()
        writer.close()


