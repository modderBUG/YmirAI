from bs4 import BeautifulSoup

from bs4 import BeautifulSoup

from bs4 import BeautifulSoup

def remove_html_tags_except_span(html_content):
    # 使用 BeautifulSoup 解析 HTML 内容
    soup = BeautifulSoup(html_content, 'lxml')

    # 找到所有的 <span> 标签并删除它们
    for span in soup.find_all('span'):
        span.decompose()  # 删除 <span> 标签及其内容

    # 获取剩余的文本内容
    text = soup.get_text()
    return text.strip()




with open('datasets/aaa.html','r',encoding='utf-8') as f:
    txt = f.read()
# 示例用法
html_string = txt
clean_text = remove_html_tags_except_span(html_string)
print(clean_text.replace("　",""))