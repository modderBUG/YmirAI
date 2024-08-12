import json
import traceback

import requests
# curl -X POST -F 'audio=@C:\Users\wwwwi\Documents\录音\test.m4a' http://10.8.13.92:38214/transcribe
from flask import Flask, request, jsonify
import whisper
from pydub import AudioSegment
import numpy as np
import io
from pydub.utils import mediainfo
from io import BytesIO
from flask import send_file
import torchaudio
import ChatTTS
import torch
from flask_cors import CORS
import hashlib
import os


from configs.config_prompts import prompts_kiana


torch._dynamo.config.cache_size_limit = 64
torch._dynamo.config.suppress_errors = True
torch.set_float32_matmul_precision('high')

import random

chat = ChatTTS.Chat()
chat.load_models(source='local',local_path="./model/ChatTTS/")  # Set to True for better performance

# 加载 Whisper 模型
model = whisper.load_model("base")

app = Flask(__name__)

CORS(app)




def qwen_chat(prompts):
    data = {
        "model": "Qwen",  # "chatglm3-6b",
        "messages": prompts,
        "temperature": 0.9,  # 调整温度，通常介于0.2和1.0之间
        "top_k": 50,
        "top_P": 1,
        "max_tokens":4096,
        "stream": False
    }
    headers = {
        "X-Server-Param": "eyJhcHBpZCI6ICJiZXJ0YmFzZSIsICJjc2lkIjogImJlcnRiYXNlYXBpMDAwMDAwMDAwMDAwMDAwMDAwMDAwM2JmY2VjYzMzZjc2NDU4NmI0NWUxODA4NGRiNzVkNDUifQ==",
        "X-CheckSum": "2b5379d4d06b23bb4a6ad8979c1ab4fb",
    }

    # url = "http://172.16.251.142:9050/chatglm3/v1/chat/completions"
    # url = "http://www.modderbug.cn:8212/v1/chat/completions"

    url_list = ["http://10.8.13.92:8808/v1/chat/completions","http://10.8.13.92:8808/v1/chat/completions"]

    url = random.choice(url_list)
    res = requests.post(url, json=data, headers=headers)

    try:
        print(f"INFO:{res.json()['choices'][0]['message']['content']}")
    except:
        print(f"input ERROR:{json.dumps(data, ensure_ascii=False, indent=2)}")
        print(res.text)
        return None
    return res.json()['choices'][0]['message']['content']

def get_audio_format(filename):
    if filename.endswith('.wav'):
        return 'wav'
    elif filename.endswith('.mp3'):
        return 'mp3'
    elif filename.endswith('.ogg'):
        return 'ogg'
    elif filename.endswith('.m4a'):
        return 'm4a'
    elif filename.endswith('.flac'):
        return 'flac'
    elif filename.endswith('.acc'):
        return 'acc'
    # 添加其他格式的判断条件...
    else:
        return None


@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    语音识别，输入，音频，输出文本
    :return:
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided.'}), 400

    audio_file = request.files['audio']
    if not audio_file:
        return jsonify({'error': 'Empty audio file.'}), 400

    # 保存文件
    file_hash = hashlib.md5(audio_file.read()).hexdigest()
    audio_file.seek(0)  # 重置文件指针
    file_path = f"./tmp/{file_hash[0:10]}"
    audio_file.save(file_path)

    # 执行识别
    result = model.transcribe(file_path, language='zh',initial_prompt = "以下是普通话：")

    # 删除文件
    os.remove(file_path)

    # 返回识别结果
    return json.dumps({'text': result['text']}, ensure_ascii=False, indent=4)


@app.route('/api/v1/chat', methods=['POST'])
def chatchat():
    """
    输入，音频，输出，音频
    :return:
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided.'}), 400

    audio_file = request.files['audio']
    if not audio_file:
        return jsonify({'error': 'Empty audio file.'}), 400

    # 保存文件
    file_hash = hashlib.md5(audio_file.read()).hexdigest()
    audio_file.seek(0)  # 重置文件指针
    file_path = f"./tmp/{file_hash[0:10]}"
    audio_file.save(file_path)

    # 执行识别
    result = model.transcribe(file_path, language='zh',initial_prompt = "以下是普通话：")

    # 删除文件
    os.remove(file_path)
    user_input = result['text']

    message = [
        {
            "role": "system",
            "content": f"{prompts_kiana}",
        }, {
            "role": "user",
            "content": f"{user_input}",
        }
    ]

    res = qwen_chat(message)
    print("user_input", user_input)
    print("robot_text",res)


    robot_text = res

    return tts_generate(29998,0.01,0.2,5,True,robot_text)






@app.route('/tts', methods=['POST'])
def tts():
    query = request.get_json()
    text = query.get('query','What is your favorite english food?[lbreak]')
    audio_seed_input = int(query.get('audio_seed_input',24))
    temperature = float(query.get('temperature',.3))
    top_P = float(query.get('top_P',0.7))
    top_K = int(query.get('top_K',20))
    refine_text_flag = bool(query.get('refine_text_flag',False))
    return tts_generate(audio_seed_input,temperature,top_P,top_K,refine_text_flag,text)


def tts_generate(audio_seed_input,temperature,top_P,top_K,refine_text_flag,text):
    torch.manual_seed(audio_seed_input)
    rand_spk = chat.sample_random_speaker()
    params_infer_code = {
        'spk_emb': rand_spk,  # add sampled speaker
        'temperature': temperature,  # using custom temperature
        'top_P': top_P,  # top P decode
        'top_K': top_K,  # top K decode
    }

    ###################################
    # For sentence level manual control.

    # use oral_(0-9), laugh_(0-2), break_(0-7)
    # to generate special token in text to synthesize.
    params_refine_text = {
        'prompt': '[oral_2][laugh_0][break_6]'
    }

    # wav = chat.infer(texts, params_refine_text=params_refine_text, params_infer_code=params_infer_code)

    ###################################
    # For word level manual control.

    # wavs = chat.infer([text], skip_refine_text=True, params_infer_code=params_infer_code, use_decoder=False)

    if refine_text_flag:
        text = chat.infer(text,
                          skip_refine_text=False,
                          refine_text_only=True,
                          params_refine_text=params_refine_text,
                          params_infer_code=params_infer_code
                          )

    wavs = chat.infer(text,
                     skip_refine_text=True,
                     params_refine_text=params_refine_text,
                     params_infer_code=params_infer_code
                     )

    tensor = torch.from_numpy(wavs[0])

    text_data = text[0] if isinstance(text, list) else text
    print(text_data)

    # 创建一个字节流缓冲区
    byte_io = io.BytesIO()

    # 将torch张量保存到字节流缓冲区
    torchaudio.save(byte_io, tensor, 24000, format='wav')

    # 重置字节流缓冲区的位置
    byte_io.seek(0)

    # 使用Flask的send_file函数发送数据
    return send_file(byte_io, download_name='output2.wav', as_attachment=True)


@app.route('/convert', methods=['POST'])
def convert_audio():
    audio_file = request.files['audio']
    m4a_data = audio_file.read()
    audio = AudioSegment.from_file(BytesIO(m4a_data), format="m4a")

    mp3_data = BytesIO()
    audio.export(mp3_data, format="mp3")
    mp3_data.seek(0)

    return send_file(mp3_data, as_attachment=True, download_name="converted.mp3", mimetype="audio/mpeg")




if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=8212)