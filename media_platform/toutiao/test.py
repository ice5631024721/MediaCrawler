import html2text
from magic_html import GeneralExtractor

with open('test.html', 'r', encoding='utf-8') as f:
    content = f.read()

url = 'https://www.toutiao.com/article/7398691436012552756/?channel=&source=news'

extractor = GeneralExtractor()
data = extractor.extract(content, base_url=url, html_type="forum")
markdown = html2text.html2text(data['html'])
print(markdown)