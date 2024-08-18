from qiniu import Auth, put_data
import qiniu.config
access_key = 'a7q_2WVFGwjO3TnSJHJxCQ-omZ53cWiFJXWUwGlb'
secret_key = 'Y2vDx1lbd7GdJI74CEKxPWZ7hNj_cY-1nE2g6eYa'
bucket_name = 'modderbug'

q = Auth(access_key, secret_key)

# 读取要上传的文件


def upload_file_to_qiniu(data,filename):

    key = 'user/'+filename
    token = q.upload_token(bucket_name, key)
    # 上传文件
    ret, info = put_data(token, key, data)

    return ret

import requests

def test_get_voice(text,charactor):
    res = requests.post("http://49.232.24.59/api/v1/voice_generate",json={
        "text":text,
        "character":charactor
    })
    print(res.text)

    filename = str(hash(text))+".wav"
    res = upload_file_to_qiniu(res.content,filename)
    print(res)
    path = res["key"]
    return "http://si5c7yq6z.hn-bkt.clouddn.com/"+path

# 使用示例
if __name__ == "__main__":


    # result = upload_file_to_qiniu(file_data,"aaa")
    # print(result)
    print(test_get_voice("你好，指挥官！","yixian"))
