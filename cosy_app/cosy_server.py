import os

from cosyvoice.cli.cosyvoice import CosyVoice
from cosyvoice.utils.file_utils import load_wav
import torchaudio
import time
import traceback
from flask import Flask, request,send_file
import json
import numpy as np
import io
from cosy_service import _read_json


app = Flask(__name__)



np.random.seed(42)
cosyvoice = None
character_base_dir = "character"
character = {}


def _init_project():
    names = os.listdir(character_base_dir)
    global  character
    for char_name in names:
        character[char_name] = _read_json(os.path.join(character_base_dir,char_name,"config.json"))
        sound_path  = os.path.join(character_base_dir,char_name,character[char_name]["wav"])
        character[char_name]["prompt_speech_16k"] = load_wav(sound_path, 16000)
        print(f"init {char_name} done ...")


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
def predict():
    try:
        body = request.get_json()
        user_text = body.get("text",None)
        char_name = body.get("character",None)
        if user_text is None or char_name is None:
            raise Exception(f'没有传入TTS文本、或者角色为空。\n可选角色{character.keys()}')

        prompts_text = character[char_name]["text"]
        prompt_speech_16k = character[char_name]["prompt_speech_16k"]

        output = cosyvoice.inference_zero_shot(user_text,prompts_text ,prompt_speech_16k)
        # torchaudio.save('zero_shot.wav', output['tts_speech'], 22050)
        audio_bytes = io.BytesIO()

        # 将生成的语音数据保存到 BytesIO 对象中
        torchaudio.save(audio_bytes, output['tts_speech'], 22050, format='wav')

        # 重置 BytesIO 对象的指针到开始位置
        audio_bytes.seek(0)


        # 返回音频数据而不保存到本地
        return send_file(audio_bytes, mimetype='audio/wav', as_attachment=True, download_name=f'{str(time.time())[:10]}.wav')
    except Exception as e:
        print(str(e),traceback.format_exc())
        return response_entity(500,f"服务器压力达到极限，亲稍后再试。tips:{str(e)}")


@app.route('/api/v1/sound', methods=['POST'])
def get_sound():
    try:
        body = request.get_json()
        char_name = body.get("character",None)

        sound_path = os.path.join(character_base_dir, char_name, character[char_name]["wav"])

        # 返回音频数据而不保存到本地
        return send_file(sound_path, mimetype='audio/wav', as_attachment=True, download_name=f'{str(time.time())[:10]}.wav')
    except Exception as e:
        print(str(e),traceback.format_exc())
        return response_entity(500,f"服务器压力达到极限，亲稍后再试。tips:{str(e)}")



@app.route('/')
def root_path():
    names = os.listdir(character_base_dir)
    res = {i:_read_json(os.path.join(character_base_dir,i,"config.json"))  for i in names}
    return response_entity(data = res)



if __name__ == '__main__':
    _init_project()
    app.run(debug=True,host='0.0.0.0', port=8220)