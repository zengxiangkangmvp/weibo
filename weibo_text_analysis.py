import jieba
import re
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
from snownlp import sentiment,SnowNLP
from wordcloud import WordCloud

'''
情感分析
情绪判断：模型训练-train_model；情感评估-snow_analysis
词云：generate_wordcloud_image
'''
def train_model(text_set,train_frequency):
    '''
    :param text_set: 文本集合
    :param train_frequency: 训练次数
    :return:
    '''
    # 情感模型训练，分值大于0.8判断为积极，分值小于0.3判断为消极
    for i in range(1,train_frequency + 1):
        print('开始第{}次训练'.format(i))
        for text in text_set:
            sub_text = ','.join(re.findall("([\u4E00-\u9FA5]+)", text))
            socre = SnowNLP(sub_text)
            if socre.sentiments > 0.8:
                with open('pos.txt', mode='a', encoding='utf-8') as g:
                    g.writelines(sub_text + "\n")
            elif socre.sentiments < 0.3:
                with open('neg.txt', mode='a', encoding='utf-8') as f:
                    f.writelines(sub_text + "\n")
            else:
                pass
        sentiment.train('neg.txt', 'pos.txt')
        sentiment.save('sentiment.marshal')

def snow_analysis(text_set):
    # 使用训练模型进行情感评估
    sentimentslist = []
    for text in text_set:
        s = SnowNLP(text)
        print('{}\n{}'.format(text, s.sentiments))
        sentimentslist.append(s.sentiments)
    plt.hist(sentimentslist, bins=np.arange(0, 1, 0.01))
    plt.show()

def generate_wordcloud_image(texts, image, font_path='FZLTXIHK.TTF'):
    '''
    生成词云图片
    texts:文本内容，str数据类型
    font_path:词云字体路径，默认同目录下的FZLTXIHK.TTF
    '''
    cut_text = ' '.join(jieba.cut(texts))
    wordcloud = WordCloud(background_color='white', font_path=font_path)
    wordcloud.generate(cut_text)
    wordcloud.to_file(image)
    img = Image.open(image)
    img.show()

def weibo_analysis(sheet_name):
    '''
    微博数据分析主程序
    '''
    #读取数据集
    weibo_df = pd.read_excel('weibo.xlsx', sheet_name=sheet_name)
    analyze_type = '关键词' if '关键词' in sheet_name else '用户名'
    #模型训练
    train_model(set(weibo_df['微博内容'].tolist()),5)
    #情感评估以及词云分布情况
    keyword_set = set(weibo_df[analyze_type].tolist())
    for keyword in keyword_set:
        text_set = set(weibo_df.loc[weibo_df[analyze_type] == keyword]['微博内容'].tolist())
        print('{}文本情感分析'.format(keyword))
        snow_analysis(text_set)
        print('{}文本词云分布'.format(keyword))
        generate_wordcloud_image(''.join(text_set),'{}.png'.format(keyword))

if __name__ == '__main__':

    weibo_analysis('微博正文数据_用户ID')

