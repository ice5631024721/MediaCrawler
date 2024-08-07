
from bs4 import BeautifulSoup
from lxml import etree
import jsonpath
import json

# 创建BeautifulSoup对象

def get_toutiao_help(content:str):
    element = etree.HTML(content)
    content_list = element.xpath('//script[@type="application/json"]')
    tmpList = []

    for ele in content_list:

        content = json.loads(ele.text)
        cons = jsonpath.jsonpath(content, '$..open_url')
        if cons:
            tmpList += cons
    return tmpList



# print(set(tmpList))


# html = '''
#
# '''
#
# url = 'https://www.toutiao.com/article/6790312245843722764/?channel=&source=news'
# extractor = GeneralExtractor()
# data = extractor.extract(html, base_url=url, html_type="forum")
# markdown = html2text.html2text(data['html'])
# print(markdown)