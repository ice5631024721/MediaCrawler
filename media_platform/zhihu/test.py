import hashlib
import json
import random
# from db_config import engine_zhihu
# from utils import iooo
import time
import urllib.parse

import execjs
import requests

query = "/api/v4/search_v3?t=general&q={}&correction=1&offset=0&limit=20&filter_fields=&lc_idx=0&show_all_topics=0&search_source=Filter&sort=created_time&time_interval=a_day"
cookie_format = "\"_xsrf=VYBO3umvIxTThehvs5hnAdRcaMVsZa4r{}{}{}{}\""
version = "101_3_2.0"
with open("/Users/lingxiao.yz/PycharmProjects/MediaCrawler/media_platform/zhihu/encrpt.js", 'r', encoding='utf-8') as f:
    # ctx1 = execjs.compile(f.read())
    ctx1 = execjs.compile(f.read(), cwd="node_modules")

if __name__ == '__main__':
        try:
            sql_keyword = "select keyword from ety_zhihu_keyword where status=0"
            # for keyword in pd.read_sql(sql_keyword, engine_zhihu())['keyword']:
            keyword = urllib.parse.quote("你是谁")
            query_now = query.format(keyword)
            url = "https://www.zhihu.com" + query_now
            cookie_now = cookie_format.format(random.randint(1, 9), random.randint(1, 9), random.randint(1, 9),
                                              random.randint(1, 9))
            payload = {}
            str = version + "+" + query_now + "+" + cookie_now
            hl = hashlib.md5()
            hl.update(str.encode(encoding='utf-8'))
            fmd5 = hl.hexdigest()
            encrpt_str = ctx1.call('b', fmd5)
            headers = {
                'cookie': 'd_c0={}; '.format(cookie_now),
                'x-zse-93': version,
                'x-zse-96': '2.0_{}'.format(encrpt_str),
                'User-Agent': 'PostmanRuntime/7.28.4'
            }

            r = requests.request("GET", url, headers=headers, data=payload)
            r.encoding = 'utf-8'
            html = r.text
            resp = json.loads(html)
            list_data = []
            for dict_data in resp['data']:
                if dict_data['type'] == 'relevant_query':
                    continue
                data = {}
                try:
                    data['summary'] = dict_data['highlight']['description']
                except Exception:
                    data['summary'] = None
                data['title'] = dict_data['highlight']['title']
                try:
                    data['content'] = dict_data['object']['content']
                except Exception:
                    data['content'] = None
                try:
                    data['url'] = dict_data['object']['url']
                except Exception:
                    data['url'] = dict_data['object']['video_url']
                try:
                    timeArray = time.localtime(dict_data['object']['updated_time'])
                except Exception:
                    timeArray = time.localtime(dict_data['object']['created_at'])
                data['publish_time'] = time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                    , timeArray)
                try:
                    data['author_name'] = dict_data['object']['author']['name']
                except Exception:
                    data['author_name'] = None
                list_data.append(data)
            # insert_df = pd.DataFrame(list_data)
            # iooo.to_sql("ety_zhihu_article", engine_zhihu(), insert_df)
        # time.sleep(60 * 60 * 4 - 120)
        except Exception as e:
            print(e)
            # time.sleep(60 * 5)
