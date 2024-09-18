import re

import requests
import tqdm
from markdownify import markdownify as md
headers = {
    "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"}
# res = requests.get("https://www.3dmgame.com/gl/3824473_10.html", headers=headers)
#
# with open("aaaa.html",'wb') as f:
#     f.write(res.content)
#
# print(res.content.decode("utf-8"))

import requests
from bs4 import BeautifulSoup


def parse_data(url):
    # 目标URL
    # url = 'https://www.3dmgame.com/gl/3824473_15.html'  # 替换为你要获取的URL

    # 发送GET请求
    response = requests.get(url,headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        # 解析HTML内容
        soup = BeautifulSoup(response.content.decode("utf-8"), 'html.parser')

        # 获取指定的div内容
        news_div = soup.find('div', class_='news_warp_center')

        if news_div:
            # 保存内容到文件
            # with open('news_content.html', 'w', encoding='utf-8') as file:
            #     file.write(str(news_div))

            markdown_content = md(str(news_div))
            markdown_content = "# "+markdown_content
            return markdown_content

            # 保存内容到Markdown文件
            # with open('news_content.md', 'w', encoding='utf-8') as file:
            #     file.write(markdown_content)
            print("内容已成功保存到 news_content.html")
        else:
            print("未找到指定的div标签")
    else:
        print(f"请求失败，状态码: {response.status_code}")


from concurrent.futures import ThreadPoolExecutor


def main():
    # task_url = ["https://www.3dmgame.com/gl/3824473.html"]
    # task_url = ["https://www.3dmgame.com/gl/3878423.html"]
    task_url = ["https://www.3dmgame.com/gl/3791916.html"]
    for i in range(2,26):
        # task_url.append(f"https://www.3dmgame.com/gl/3824473_{i}.html")
        # task_url.append(f"https://www.3dmgame.com/gl/3878423_{i}.html")
        task_url.append(f"https://www.3dmgame.com/gl/3791916_{i}.html")

    with ThreadPoolExecutor(3) as pool:
        res = list(tqdm.tqdm(pool.map(parse_data,task_url),desc="进度：",total=len(task_url)))

    markdown_content = "\n\n".join(res)
    with open('L1攻略.md', 'w', encoding='utf-8') as file:
        file.write(markdown_content)

if __name__ == '__main__':

    # main()
    url = "https://www.ciweimao.com/chapter/111715642"
    res = requests.get(url, headers=headers)
    print(res.text)

