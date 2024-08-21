import time

import requests
from flask import Flask, Response, request, send_file
from flask_cors import CORS
from cosy_service import with_char_stream_chat
import json
import traceback
from flask_caching import Cache
from databases.sqllite_connection import UserService, ConvService, AudioService,CharacterService

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


def get_uid_by_token(request):
    try:
        token = None
        # 从请求头中获取 Token
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # 假设格式为 "Bearer <token>"
        # print(request.headers)

        if not token:
            return None

        cached_user_id = cache.get(token)
        print(f"get {token} {cached_user_id}")
        if cached_user_id:
            print(f"set {token}:{cached_user_id}")
            cache.set(token, cached_user_id, timeout=3600)

        return cached_user_id
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return None


@app.route('/api/v1/chat', methods=['post'])
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


@app.route('/api/generate/convid', methods=['GET'])
def post_generate_convid():
    # print(request.headers)
    try:

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None: return response_entity(401, f'未授权')
        db = ConvService()
        conv_id = db.generate_convid(uid, "")

        return response_entity(data=conv_id)
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')


@app.route('/api/conv/<cid>', methods=['GET'])
def get_conv(cid):
    try:

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None: return response_entity(401, f'未授权')

        db = ConvService()

        res = db.get_conv_by_convid(cid, uid)
        if len(res) == 0: return response_entity(400, f'不存在')

        return response_entity(data=json.loads(res[0][1]))
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')


@app.route('/api/v1/summary', methods=['POST'])
def post_summary():
    """
    分类 + 大纲 -> 条款生成接口。
    当query有字段，则为条款重新生成接口。否则为第一次生成。
    重新生成：根据history和query生成新的条款。
    """
    db = None
    try:
        data = request.get_json()

        bot_message = data.get("bot_message", None)
        user_message = data.get("user_message", None)
        conv_id = data.get("conv_id", None)
        user_summary = data.get("user_summary", None)

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")

        if uid is None: return response_entity(401, f'未授权')

        db = ConvService()

        res = {
            "conv_id": conv_id,
            "summary": user_summary
        }

        if user_summary is not None:
            db.update_summary_by_convid(user_summary, conv_id, uid)
            return response_entity(data=res)

        summary = (bot_message, user_message)
        db.update_summary_by_convid(summary, conv_id, uid)
        res["summary"] = summary
        return response_entity(data=res)
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')

    finally:
        if db is not None:
            db.close()


from llm_prompts.qiniu_upload import upload_file_to_qiniu


def _get_voice(text, charactor):
    res = requests.post("http://49.232.24.59/api/v1/voice_generate", json={
        "text": text,
        "character": charactor
    })
    filename = str(hash(text)) + ".wav"
    res = upload_file_to_qiniu(res.content, filename)
    path = res["key"]
    return "http://si5c7yq6z.hn-bkt.clouddn.com/" + path


@app.route('/api/v1/get_voice', methods=['POST'])
def get_voice_and_save_conv():
    """
    分类 + 大纲 -> 条款生成接口。
    当query有字段，则为条款重新生成接口。否则为第一次生成。
    重新生成：根据history和query生成新的条款。
    """
    db = None
    try:
        data = request.get_json()

        conv = data.get("conversation", None)
        speeches_id = data.get("speechesId", None)
        conv_id = data.get("convid", None)

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")

        if uid is None: return response_entity(401, f'未授权')

        db = ConvService()
        db.update_conv_by_convid(json.dumps(conv), conv_id, uid)

        bot_message = conv[len(conv) - 1]["speeches"][speeches_id]

        url = _get_voice(bot_message, "yixian")
        print("url:", url)

        if "voice" in conv[len(conv) - 1]:
            conv[len(conv) - 1]["voice"].append(url)
        else:
            conv[len(conv) - 1]["voice"] = [url]
        db.update_conv_by_convid(json.dumps(conv), conv_id, uid)

        return response_entity(data=conv)
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')

    finally:
        if db is not None:
            db.close()


@app.route('/api/v1/voice2', methods=['POST'])
def get_saved_voice2():
    """
    分类 + 大纲 -> 条款生成接口。
    当query有字段，则为条款重新生成接口。否则为第一次生成。
    重新生成：根据history和query生成新的条款。
    """
    db = None
    try:
        data = request.get_json()

        conv = data.get("conversation", None)
        speeches_id = data.get("speechesId", None)
        conv_id = data.get("convid", None)

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")

        if uid is None: return response_entity(401, f'未授权')

        db = ConvService()
        db.update_conv_by_convid(json.dumps(conv), conv_id, uid)

        bot_message = conv[len(conv) - 1]["speeches"][speeches_id]

        url = _get_voice(bot_message, "yixian")
        print("url:", url)

        if "voice" in conv[len(conv) - 1]:
            conv[len(conv) - 1]["voice"].append(url)
        else:
            conv[len(conv) - 1]["voice"] = [url]
        db.update_conv_by_convid(json.dumps(conv), conv_id, uid)

        return response_entity(data=conv)
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')

    finally:
        if db is not None:
            db.close()


@app.route('/api/v1/make_voice', methods=['POST'])
def self_making_voice():
    """
    自定义语音合成接口。
    :return:
    """
    try:

        user_text = request.form.get("text")
        prompts_text = request.form.get("prompts_text")
        self_voice = request.files.get("file")
        print(user_text)
        print(prompts_text)
        print(self_voice)
        f = open(r'..\cosy_app\character\huajia2\b6cxl0z7w0j878nwkf2b57vaa2rbv5z.mp3', "rb")
        return send_file(f, mimetype='audio/wav', as_attachment=True,
                         download_name=f'{str(time.time())[:10]}.wav')
    except Exception as e:
        print(e)


@app.route('/api/v1/voices', methods=['GET'])
def get_saved_voice():
    try:

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None: return response_entity(401, f'未授权')

        db = AudioService()

        res = db.get_all_by_uid(uid)
        if len(res) == 0: return response_entity(400, f'不存在')

        return response_entity(data=res)
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')


@app.route('/api/v1/voice/<id>', methods=['GET'])
def get_voice_data(id):
    db = None
    try:

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None: return response_entity(401, f'未授权')

        db = AudioService()

        del_flag = request.args.get("delete", None)
        if del_flag:
            db.delete_audio(id)
            return response_entity(data=id)

        res = db.get_b64data_by_id(id)
        if len(res) == 0: return response_entity(400, f'不存在')

        return response_entity(data=res)
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')
    finally:
        db.close()


@app.route('/api/v1/voice', methods=['POST'])
def save_voice_data():
    db = None
    try:
        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None: return response_entity(401, f'未授权')

        user_text = request.form.get("text")
        prompts_text = request.form.get("prompts_text")
        self_voice = request.files.get("file")

        db = AudioService()
        db.insert_audio(uid=uid, filename=self_voice.filename, mime_type="audio/wav", prompts_text=prompts_text,
                        text=user_text, audio_data=self_voice.stream.read())
        return response_entity(data="ok")
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')
    finally:
        db.close()

@app.route('/api/v1/characters', methods=['GET'])
def get_saved_characters():
    try:

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None: return response_entity(401, f'未授权')

        db = CharacterService()

        res = db.get_all_characters_info_by_uid(uid)
        if len(res) == 0: return response_entity(400, f'不存在')

        return response_entity(data=res)
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')

@app.route('/api/v1/character/<id>', methods=['GET'])
def get_character_b64data(id):
    db = None
    try:

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None: return response_entity(401, f'未授权')

        db = CharacterService()

        del_flag = request.args.get("delete", None)
        if del_flag:
            db.delete_character(id,uid)
            return response_entity(data=id)

        avatar = request.args.get("avatar", None)
        if avatar:
            data = db.get_character_avatar_by_id(id)
            return response_entity(data=data)

        audio = request.args.get("audio", None)
        if audio:
            data = db.get_character_b64data_by_id(id)
            return response_entity(data=data)

        return response_entity(data="")
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')
    finally:
        db.close()


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

        # print(data)

        token = str(hash(username + password))

        user_service = UserService()

        if user_service.login_user(username, password):
            cached_user_id = user_service.get_uid_by_uname(username)
        else:
            return response_entity(401, "用户或密码错误")

        print(f"set {token}:{cached_user_id}")
        cache.set(token, cached_user_id, timeout=3600)
        return response_entity(data=token)
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')


if __name__ == '__main__':
    app.run(debug=True, port=8888)
