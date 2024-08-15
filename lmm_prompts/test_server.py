import time

from flask import Flask, Response,request
from flask_cors import CORS
from cosy_service import with_char_stream_chat
import json
import traceback
from flask_caching import Cache
from databases.sqllite_connection import UserService
app = Flask(__name__)

CORS(app)  # 允许所有域名的跨域请求
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
def response_entity(code=200, msg="ok", data=None):
    res = {
        "code": code,
        "message": msg,
        "data": data
    }
    return json.dumps(res, ensure_ascii=False, indent=4)


@app.route('/api/v1/chat', methods=['post'])
# @token_required
def post_chat():
    """
    分类 + 大纲 -> 条款生成接口。
    当query有字段，则为条款重新生成接口。否则为第一次生成。
    重新生成：根据history和query生成新的条款。
    """
    try:
        req_data = request.get_json()
        query = req_data.get("query", "")
        history = req_data.get("history", [])
        return Response(with_char_stream_chat(history, query), mimetype='text/event-stream')
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return Response("data: 出现错误\n\n", mimetype='text/event-stream')



@app.route('/api/v1/login', methods=['POST'])
def login():
    """
    哈希算法得到token。查库匹配密码。设置token缓存时间。
    :return: 返回一个token
    """
    # 从nginx限制调用次数，因此不需要进行验证码登录。因为是明文传输密码，因此必须开启https。
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        print(data)

        token = hash(username + password)

        user_service = UserService()

        if user_service.login_user(username, password):
            cached_user_id = user_service.get_uid_by_uname(username)
        else:
            return response_entity(401, "用户或密码错误")

        cache.set(token, cached_user_id, timeout=60)
        return response_entity(data=token)
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')

if __name__ == '__main__':
    app.run(debug=True,port=8888)
