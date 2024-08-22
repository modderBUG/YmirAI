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
from cosy_service import _read_json, with_char_stream_chat,with_charid_stream_chat
from databases.sqllite_connection import UserService, ConvService,CharacterService,AudioService
from qiniu_upload import upload_file_to_qiniu

app = Flask(__name__)

# 创建token缓存
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

file_handler = logging.FileHandler('cosy_server.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)
logger = app.logger

np.random.seed(42)
cosy_voice_model = None
character_base_dir = "character"
character = {}
user_character = {}

def _init_project():
    names = os.listdir(character_base_dir)
    global character,user_character
    for char_name in names:
        character[char_name] = _read_json(os.path.join(character_base_dir, char_name, "config.json"))
        sound_path = os.path.join(character_base_dir, char_name, character[char_name]["wav"])
        character[char_name]["prompt_speech_16k"] = load_wav(sound_path, 16000)
        print(f"init {char_name} done ...")

    db = CharacterService()
    items = db.get_published_characters_info(20,0)


    for item in items:
        try:
            file_bytes =  db.get_character_audio_by_id(item["id"])
            user_character[item["id"]] = {
                "text":item["id"]["text"],
                "prompt_speech_16k":load_wav(file_bytes, 16000)
            }
        except Exception as e:
            print(str(e))

    db.close()

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
    global cosy_voice_model
    cosy_voice_model = CosyVoice('pretrained_models/CosyVoice-300M-Instruct')


def response_entity(code=200, msg="ok", data=None):
    res = {
        "code": code,
        "message": msg,
        "data": data
    }
    return json.dumps(res, ensure_ascii=False, indent=4)


def _generate_voice(user_text, char_name):
    assert isinstance(cosy_voice_model,CosyVoice)
    if user_text is None or char_name is None:
        raise Exception(f'没有传入TTS文本、或者角色为空。\n可选角色{character.keys()}')

    prompts_text = character[char_name]["text"]
    prompt_speech_16k = character[char_name]["prompt_speech_16k"]

    output = cosy_voice_model.inference_zero_shot(user_text, prompts_text, prompt_speech_16k)
    # torchaudio.save('zero_shot.wav', output['tts_speech'], 22050)
    audio_bytes = io.BytesIO()

    # 将生成的语音数据保存到 BytesIO 对象中
    torchaudio.save(audio_bytes, output['tts_speech'], 22050, format='wav')

    # 重置 BytesIO 对象的指针到开始位置
    audio_bytes.seek(0)
    return audio_bytes


def _generate_voice_by_cid(user_text, cid):
    assert isinstance(cosy_voice_model,CosyVoice)
    if user_text is None or cid is None:
        raise Exception(f'没有传入TTS文本、或者角色为空。\n可选角色{character.keys()}')

    cc = user_character.get(cid,None)
    if cc is None:
        db = CharacterService()
        text = db.get_text_by_id(cid)
        file_bytes = db.get_character_audio_by_id(cid)

        prompts_text = text
        prompt_speech_16k = load_wav(file_bytes,16000)

        cc[cid] = {
            "text":prompts_text,
            "prompt_speech_16k":prompt_speech_16k,
        }

    else:
        prompts_text = cc[cid]["text"]
        prompt_speech_16k = cc[cid]["prompt_speech_16k"]

    output = cosy_voice_model.inference_zero_shot(user_text, prompts_text, prompt_speech_16k)
    # torchaudio.save('zero_shot.wav', output['tts_speech'], 22050)
    audio_bytes = io.BytesIO()

    # 将生成的语音数据保存到 BytesIO 对象中
    torchaudio.save(audio_bytes, output['tts_speech'], 22050, format='wav')

    # 重置 BytesIO 对象的指针到开始位置
    audio_bytes.seek(0)
    return audio_bytes

def _get_voice(text, charactor):
    # res = requests.post("http://49.232.24.59/api/v1/voice_generate",json={
    #     "text":text,
    #     "character":charactor
    # })
    res = _generate_voice(text, charactor)
    filename = str(hash(text)) + ".wav"
    res = upload_file_to_qiniu(res, filename)
    path = res["key"]
    return "http://si5c7yq6z.hn-bkt.clouddn.com/" + path


def _get_voice_by_cid(text, charactor_id):
    res = _generate_voice_by_cid(text, charactor_id)
    filename = str(hash(text)) + f"{time.time()}.wav"
    res = upload_file_to_qiniu(res, filename)
    path = res["key"]
    return "http://si5c7yq6z.hn-bkt.clouddn.com/" + path

@app.route('/api/v1/voice_generate', methods=['POST'])
def predict():
    try:
        assert isinstance(cosy_voice_model,CosyVoice)
        body = request.get_json()
        user_text = body.get("text", None)
        char_name = body.get("character", None)
        if user_text is None or char_name is None:
            raise Exception(f'没有传入TTS文本、或者角色为空。\n可选角色{character.keys()}')

        prompts_text = character[char_name]["text"]
        prompt_speech_16k = character[char_name]["prompt_speech_16k"]

        output = cosy_voice_model.inference_zero_shot(user_text, prompts_text, prompt_speech_16k)
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
        assert isinstance(cosy_voice_model,CosyVoice)

        user_text = request.form.get("text")
        prompts_text = request.form.get("prompts_text")
        self_voice = request.files.get("file")

        if user_text is None or self_voice is None:
            raise Exception(f'没有传入TTS文本、或者角色为空。\n可选角色{character.keys()}')

        prompt_speech_16k = load_wav(self_voice.stream.read(), 16000)

        output = cosy_voice_model.inference_zero_shot(user_text, prompts_text, prompt_speech_16k)

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
    """获取指定角色的语音"""
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
    """获取所有支持的角色和对应语音"""
    names = os.listdir(character_base_dir)
    res = {i: _read_json(os.path.join(character_base_dir, i, "config.json")) for i in names}
    return response_entity(data=res)


def generate_text(text):
    for i in text:
        time.sleep(0.1)
        yield f"data: {json.dumps({'data': i})}\n\n"

    yield "data: [DONE]\n\n"


@app.route('/api/v1/chat', methods=['post'])
def post_chat():
    """
    聊天接口
    """
    try:

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None: return Response(generate_text("你没有登录哦，请登录后进行聊天"), mimetype='text/event-stream')

        req_data = request.get_json()
        query = req_data.get("query", "")
        history = req_data.get("history", [])
        character_id = req_data.get("character_id", 2)
        return Response(with_charid_stream_chat(history, query, character_id), mimetype='text/event-stream')
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return Response("data: 出现错误\n\n", mimetype='text/event-stream')


@app.route('/api/generate/convid', methods=['GET'])
def post_generate_convid():
    """获取一个会话id"""
    db = None
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
    finally:
        db.close()


@app.route('/api/conv/<cid>', methods=['GET'])
def get_conv(cid):
    """通过会话id获取聊天内容"""
    db = None
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
    finally:
        db.close()


@app.route('/api/v1/summary', methods=['POST'])
def post_summary():
    """总结会话摘要
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
        character_id = data.get("character_id", None)

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")

        if uid is None: return response_entity(401, f'未授权')

        db = ConvService()
        db.update_conv_by_convid(json.dumps(conv), conv_id, uid)

        bot_message = conv[len(conv) - 1]["speeches"][speeches_id]

        url = _generate_voice_by_cid(bot_message, character_id) if len(bot_message) < 30 else "error"
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

        url = _get_voice(bot_message, "kesya")
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


@app.route('/api/v1/voices', methods=['GET'])
def get_saved_voice():
    """
    获取所有指定uid的角色信息
    为声音克隆页面提供服务
    :return:
    """
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
    """保存音频，为克隆声音界面服务"""
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
    """获取所有公共角色的角色信息"""
    try:

        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None:
            return response_entity(401, f'未授权')


        db = CharacterService()
        publish = request.args.get("publish",None)
        page = request.args.get("page",1)
        size = request.args.get("pageSize",20)
        if publish:
            res = db.get_published_characters_info(size,(page - 1) * size)
            return response_entity(data=res)



        res = db.get_all_characters_info_by_uid(uid)
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


@app.route('/api/v1/character', methods=['POST'])
def save_character_data():
    db = None
    try:
        uid = get_uid_by_token(request)
        print(f"uid:{uid}")
        if uid is None:
            return response_entity(401, f'未授权')

        data = request.form
        character_name = data.get('character_name')
        summery = data.get('summery')
        prompts_texts = data.get('prompts_texts')
        text = data.get('text')
        publish = data.get('publish')

        # 处理文件
        avatar_file = request.files.get('avatar')
        audio_data_file = request.files.get('audio_data')

        # 保存数据
        db = CharacterService()
        db.insert_character(uid=uid,
                            character_name=character_name,
                            summery=summery,
                            prompts_texts=prompts_texts,
                            text=text,
                            audio_data=audio_data_file.stream.read(),
                            avatar=avatar_file.stream.read(),
                            publish=publish)
        return response_entity(data="ok")
    except Exception as e:
        print(f"input:{json.dumps(request.get_data())},err:{repr(e)}")
        print(traceback.format_exc())
        return response_entity(500, f'服务器内部错误！请重试！:{traceback.format_exc()}')
    finally:
        db.close()

@app.route('/api/v1/register', methods=['POST'])
def register():
    """
    哈希算法得到token。查库匹配密码。设置token缓存时间。
    :return: 返回一个token
    """
    # 从nginx限制调用次数，因此不需要进行验证码登录。因为是明文传输密码，因此必须开启https。
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        nickname = data.get('nickname')
        email = data.get('email')

        token = str(hash(username + password))

        user_service = UserService()

        res = user_service.get_uid_by_uname(username)
        if res is not None:
            return response_entity(400, "用户已存在")
        res = user_service.get_uid_by_email(email)
        if res is not None:
            return response_entity(400, "邮箱已存在")


        user_service.insert_user(username, password, email)


        cached_user_id = user_service.get_uid_by_uname(username)


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
