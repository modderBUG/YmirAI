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
from cosy_service import _read_json, with_char_stream_chat, stream_chat
from configs.project_config import TOKEN_EXPIRATION_TIME
from databases.sqllite_connection import UserService

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


def token_required(f):
    def decorator(*args, **kwargs):
        token = None

        # 从请求头中获取 Token
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # 假设格式为 "Bearer <token>"

        if not token:
            return response_entity(401, 'Token is missing!')  # jsonify({'message': 'Token is missing!'}), 401

        cached_user_id = cache.get(token)
        if cached_user_id:
            cache.set(token, cached_user_id, timeout=TOKEN_EXPIRATION_TIME)

        return f(*args, **kwargs)

    return decorator


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


@app.route('/api/v1/voice_generate', methods=['POST'])
# @token_required
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


@app.route('/api/v1/sound', methods=['POST'])
# @token_required
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

        token = request.headers['Authorization'].split(" ")[1]
        uid = cache.get(token)

        return Response(with_char_stream_chat(history, query,uid), mimetype='text/event-stream')
    except Exception as e:
        logger.error(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        logger.error(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')


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

        token = hash(username + password)

        user_service = UserService()

        if user_service.login_user(username, password):
            cached_user_id = user_service.get_uid_by_uname(username)
        else:
            return response_entity(401, "用户或密码错误")

        cache.set(token, cached_user_id, timeout=TOKEN_EXPIRATION_TIME)
        return response_entity(data=token)
    except Exception as e:
        logger.error(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        logger.error(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！')


if __name__ == '__main__':
    _init_project()
    app.run(debug=True, host='0.0.0.0', port=8220)
