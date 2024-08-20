import os

from cosyvoice.cli.cosyvoice import CosyVoice
from cosyvoice.utils.file_utils import load_wav
import torchaudio
import time
import traceback
from flask import Flask, request, send_file, Response
from flask_caching import Cache
import json
import numpy as np
import io
import logging
from cosy_service import _read_json, with_char_stream_chat
from databases.sqllite_connection import UserService,ConvService
from qiniu_upload import upload_file_to_qiniu

app = Flask(__name__)

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

file_handler = logging.FileHandler('cosy_server.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)
logger = app.logger

np.random.seed(42)
cosyvoice = None
character_base_dir = "character"
character = {}


def _init_project():
    names = os.listdir(character_base_dir)
    global character
    for char_name in names:
        character[char_name] = _read_json(os.path.join(character_base_dir, char_name, "config.json"))
        sound_path = os.path.join(character_base_dir, char_name, character[char_name]["wav"])
        character[char_name]["prompt_speech_16k"] = load_wav(sound_path, 16000)
        print(f"init {char_name} done ...")


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



@app.before_first_request
def first_request():
    global cosyvoice
    cosyvoice = CosyVoice('pretrained_models/CosyVoice-300M-Instruct')


def response_entity(code=200, msg="ok", data=None):
    res = {
        "code": code,
        "message": msg,
        "data": data
    }
    return json.dumps(res, ensure_ascii=False, indent=4)


def _generate_voice(user_text,char_name):
    if user_text is None or char_name is None:
        raise Exception(f'没有传入TTS文本、或者角色为空。\n可选角色{character.keys()}')

    prompts_text = character[char_name]["text"]
    prompt_speech_16k = character[char_name]["prompt_speech_16k"]

    output = cosyvoice.inference_zero_shot(user_text, prompts_text, prompt_speech_16k)
    # torchaudio.save('zero_shot.wav', output['tts_speech'], 22050)
    audio_bytes = io.BytesIO()

    # 将生成的语音数据保存到 BytesIO 对象中
    torchaudio.save(audio_bytes, output['tts_speech'], 22050, format='wav')

    # 重置 BytesIO 对象的指针到开始位置
    audio_bytes.seek(0)
    return audio_bytes

def _get_voice(text,charactor):
    # res = requests.post("http://49.232.24.59/api/v1/voice_generate",json={
    #     "text":text,
    #     "character":charactor
    # })
    res = _generate_voice(text,charactor)
    filename = str(hash(text))+".wav"
    res = upload_file_to_qiniu(res,filename)
    path = res["key"]
    return "http://si5c7yq6z.hn-bkt.clouddn.com/"+path


@app.route('/api/v1/voice_generate', methods=['POST'])
def predict():
    try:
        body = request.get_json()
        user_text = body.get("text", None)
        char_name = body.get("character", None)
        if user_text is None or char_name is None:
            raise Exception(f'没有传入TTS文本、或者角色为空。\n可选角色{character.keys()}')

        prompts_text = character[char_name]["text"]
        prompt_speech_16k = character[char_name]["prompt_speech_16k"]

        output = cosyvoice.inference_zero_shot(user_text, prompts_text, prompt_speech_16k)
        # torchaudio.save('zero_shot.wav', output['tts_speech'], 22050)
        audio_bytes = io.BytesIO()

        # 将生成的语音数据保存到 BytesIO 对象中
        torchaudio.save(audio_bytes, output['tts_speech'], 22050, format='wav')

        # 重置 BytesIO 对象的指针到开始位置
        audio_bytes.seek(0)


        # 返回音频数据而不保存到本地
        return send_file(audio_bytes, mimetype='audio/wav', as_attachment=True,
                         download_name=f'{str(time.time())[:10]}.wav')
    except Exception as e:
        print(str(e), traceback.format_exc())
        return response_entity(500, f"服务器压力达到极限，亲稍后再试。tips:{str(e)}")




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


        if user_text is None or self_voice is None:
            raise Exception(f'没有传入TTS文本、或者角色为空。\n可选角色{character.keys()}')


        prompt_speech_16k = load_wav(self_voice.stream.read(), 16000)

        output = cosyvoice.inference_zero_shot(user_text, prompts_text, prompt_speech_16k)

        audio_bytes = io.BytesIO()

        # 将生成的语音数据保存到 BytesIO 对象中
        torchaudio.save(audio_bytes, output['tts_speech'], 22050, format='wav')

        # 重置 BytesIO 对象的指针到开始位置
        audio_bytes.seek(0)

        # 返回音频数据而不保存到本地
        return send_file(audio_bytes, mimetype='audio/wav', as_attachment=True,
                         download_name=f'{str(time.time())[:10]}.wav')
    except Exception as e:
        print(str(e), traceback.format_exc())
        return response_entity(500, f"服务器压力达到极限，亲稍后再试。tips:{str(e)}")


@app.route('/api/v1/sound', methods=['POST'])
def get_sound():
    try:
        body = request.get_json()
        char_name = body.get("character", None)

        sound_path = os.path.join(character_base_dir, char_name, character[char_name]["wav"])

        # 返回音频数据而不保存到本地
        return send_file(sound_path, mimetype='audio/wav', as_attachment=True,
                         download_name=f'{str(time.time())[:10]}.wav')
    except Exception as e:
        print(str(e), traceback.format_exc())
        return response_entity(500, f"服务器压力达到极限，亲稍后再试。tips:{str(e)}")


@app.route('/api/v1/characters')
# @token_required
def root_path():
    names = os.listdir(character_base_dir)
    res = {i: _read_json(os.path.join(character_base_dir, i, "config.json")) for i in names}
    return response_entity(data=res)


def generate_text(text):
    for i in text:
        time.sleep(0.1)
        yield  f"data: {json.dumps({'data':i})}\n\n"

    yield "data: [DONE]\n\n"


@app.route('/api/v1/chat', methods=['post'])
def post_chat():
    """
    分类 + 大纲 -> 条款生成接口。
    当query有字段，则为条款重新生成接口。否则为第一次生成。
    重新生成：根据history和query生成新的条款。
    """
    try:

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None:return Response(generate_text("你没有登录哦，请登录后进行聊天"), mimetype='text/event-stream')

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





@app.route('/api/v1/get_voice', methods=['POST'])
def get_voice_and_save_conv():
    """

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

        url = _get_voice(bot_message,"kesya") if len(bot_message)<30 else "error"
        print("url:",url)

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


@app.route('/api/v2/get_voice', methods=['POST'])
def generate_voice_by_text():
    """
    TODO 更合理的请求
    """
    db = None
    try:

        # 拿到convid，拿到recordsId，拿到bot_idx，更新相应的字段。
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

        url = _get_voice(bot_message,"kesya")
        print("url:",url)

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
    _init_project()
    app.run(debug=True, host='0.0.0.0', port=8220)
