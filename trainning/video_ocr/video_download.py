# 导入数据请求模块 安装命令：pip install requests
import requests
# 正则表达式 不需要安装
import re
# 导入json 不需要安装
import json
# 导入进程模块
import subprocess
# os模块是Python中整理文件和目录最为常用的模块
import os

def demo():
    # 要请求的网址：B站视频网址
    # 这个变量需要替换成你要下载的视频网址
    url = "https://www.bilibili.com/video/BV1ynpdejELq"

    # 添加headers请求头，对Python解释器进行伪装
    # referer 和 User-Agent要改写成字典形式
    headers = {
        "referer": "https://www.bilibili.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }

    # 用 requests 的 get 方法访问网页
    response = requests.get(url=url, headers=headers)

    # 返回响应状态码：<Response [200]>
    print("返回200，则网页请求成功：", response.text)

    # .text获取网页源代码
    # print(response.text)

    # 提取视频标题
    # 调用 re 的 findall 方法，去response.text中匹配我们要的标题
    # 正则表达式提取的数据返回的是一个列表，用[0]从列表中取值
    title = re.findall('<h1 data-title="(.*?)"', response.text)[0]
    # 如果标题里有[\/:*?<>|]特殊字符，直接删除
    title = re.sub(r"[\/:*?<>|]", "", title)
    print("视频标题为：", title)

    # type函数查看title的数据类型
    # print(type(title))

    # 提取 playinfo 里的数据
    # 调用 re的 findall 方法，去 response.text 中匹配我们要的数据
    # 正则表达式提取的数据返回的是一个列表，用[0]从列表中取值
    html_data = re.findall('<script>window.__playinfo__=(.*?)</script>', response.text)[0]

    # html_data是字符串类型，将字符串转换成字典
    json_data = json.loads(html_data)

    # 让pycharm控制台以json格式化输出
    # 不影响程序，只改变pycharm或vscode编辑器的终端输出显示
    # indent=4 缩进4个空格
    json_dicts = json.dumps(json_data, indent=4)

    # print(json_dicts)

    # 提取视频画面网址
    video_url = json_data["data"]["dash"]["video"][0]["baseUrl"]
    print("视频画面地址为：", video_url)
    # 提取音频网址
    audio_url = json_data["data"]["dash"]["audio"][0]["baseUrl"]
    print("音频地址为：", audio_url)

    # response.content获取响应体的二进制数据
    video_content = requests.get(url=video_url, headers=headers).content
    # audio_content = requests.get(url=audio_url,headers=headers).content

    # 创建mp4文件，写入二进制数据
    with open(title + ".mp4", mode="wb") as f:
        f.write(video_content)
    # 创建mp3文件，写入二进制数据
    # with open (title+".mp3", mode = "wb") as f :
    #     f.write(audio_content)

    print("数据写入成功！")

    # 合成视频
    # ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -strict experimental output.mp4
    # cmd =f"ffmpeg -i {title}.mp4 -i {title}.mp3 -c:v copy -c:a aac -strict experimental {title}(最终版).mp4"
    # subprocess.run(cmd,shell=True)
    # print( '恭喜你，视频合成成功！')

    # 删除不需要的mp3和mp4文件
    # os.remove(f'{title}.mp3')
    # os.remove(f'{title}.mp4')

    print("程序结束！")

headers = {
        "referer": "https://www.bilibili.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
def video_download(url = "https://www.bilibili.com/video/BV1ynpdejELq",dir_name="download"):

    # 用 requests 的 get 方法访问网页
    response = requests.get(url=url, headers=headers)

    title = re.findall('<h1 data-title="(.*?)"', response.text)[0]

    title = re.sub(r"[\/:*?<>|]", "", title)
    print("视频标题为：", title)

    html_data = re.findall('<script>window.__playinfo__=(.*?)</script>', response.text)[0]

    json_data = json.loads(html_data)

    # 提取视频画面网址
    video_url = json_data["data"]["dash"]["video"][0]["baseUrl"]
    print("视频画面地址为：", video_url)
    # 提取音频网址
    audio_url = json_data["data"]["dash"]["audio"][0]["baseUrl"]
    print("音频地址为：", audio_url)

    # response.content获取响应体的二进制数据
    video_content = requests.get(url=video_url, headers=headers).content

    # 创建mp4文件，写入二进制数据
    with open(f"{dir_name}/{title}.mp4", mode="wb") as f:
        f.write(video_content)

    return f"{dir_name}/{title}.mp4"


if __name__ == '__main__':
    video_download()