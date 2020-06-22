## 微博数据挖掘
### 微博数据抓取
- 数据接口\
    https://weibo.cn/
- 抓取方式 
    1. 通过用户抓取用户个人信息和微博文本数据(配置crawl_by_user_setting)
    2. 通过关键词抓取关键词统计信息和微博文本数据(配置crawl_by_user_setting)
-  抓取JSON文件配置(其中i为必填项，ii和iii根据需求选填)
    1. basic_setting(模拟登陆账号数量越多，能够抓取的数据量越大)\
    SLUser_list：模拟登陆账号列表\
    min_delay：每次请求最小延时时间(单位:秒)\
    max_delay：每次请求最大延时时间(单位:秒)\
    2. crawl_by_user_setting\
    user_list：需要抓取的用户列表，需提供用户ID，通过浏览器调试查询\
    crawl_pages：抓取页数\
    filter：微博类型("0"=全部，"1"=原创，通常抓取原创微博数据)
    3. crawl_by_keyword_setting\
    keyword_list：需要抓取的关键词列表\
    crawl_pages：抓取页数\
    keyword_type：关键词类型(0=包含关键词，1=包含关键词原创，2=同名关键词，3=同名关键词原创，通常抓取包含关键词原创微博数据)
- 抓取策略\
通过模拟登陆账号列表进行模拟登陆获取相应的session列表，后续随机从session列表中生成session进行数据请求;\
每次请求的延时通过设置最小和最大延时区间随机生成。
### 微博文本分析
- 数据源\
通过微博数据抓取得到的微博正文数据
- 分析内容
   1. 词云分布
   2. 情感分布