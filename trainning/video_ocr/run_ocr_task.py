import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import base64
import tqdm

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

QWEN_CHAT_URL = "http://74.120.172.183:8216/v1/chat/completions"
def qwen_chat(prompts):
    data = {
        "model": "Qwen2-7B-Instruct-GPTQ-Int4",  # "chatglm3-6b",
        "messages": prompts,
        "temperature": 0.2,  # 调整温度，通常介于0.2和1.0之间
        # "top_k": 10,
        # "top_P": 1,
        "max_tokens": 2048,
        "stream": False
    }
    res = requests.post(QWEN_CHAT_URL, json=data)

    try:
        print(f"INFO:{res.json()['choices'][0]['message']['content']}")
    except:
        print(f"input ERROR:{json.dumps(data, ensure_ascii=False, indent=2)}")
        print(res.text)
        return None
    return res.json()['choices'][0]['message']['content']


def chat_with_img(image_path):
    base64_image = encode_image(image_path)
    messages = [
        {
            "role": "system",
            "content": "你是一个图片文本提取模型，善于从文本中提取文字。"
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请从以下对话记录中，提取对话文本，注意右边侧，对话为`我`。例如:\n- 凯茜娅: 你好~分析员\n- 我:你好凯茜娅。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                },
            ]
        }
    ]

    res = qwen_chat(messages)
    print(res)


def send_ocr_request(image_path):
    url = "http://74.120.172.183:8218/ocr"

    # 构建 multipart/form-data 的 payload
    with open(image_path, 'rb') as f:
        image_data = f.read()
    files = {
        "image": ("1.jpg", image_data)
    }

    response = requests.post(url, files=files)
    # print(response.text)
    return response.json()


def main():
    main_dir = 'ocr_dir'

    ocr_dirs = os.listdir(main_dir)

    for dir_name in ocr_dirs:
        files = os.listdir(f"{main_dir}/{dir_name}")
        task_img = [f"{main_dir}/{dir_name}/{i}" for i in files]

        with ThreadPoolExecutor(5) as pool:
            res = list(tqdm.tqdm(pool.map(send_ocr_request, task_img), desc="img", total=len(task_img)))

        pages = [page['result'] for page in res]
        pages = ["\n".join(page) for page in pages]
        all_text = "\n\n".join(pages)

        with open(f"{dir_name}.txt", "w", encoding="utf-8") as f:
            f.write(all_text)


if __name__ == '__main__':
    # send_ocr_request(r"D:\projects\pythonproject\YmirAI\trainning\video_ocr\ocr_dir\吃醋后醉酒的芬妮_saved\frame_0.jpg")

    chat_with_img(r"D:\projects\pythonproject\YmirAI\trainning\video_ocr\ocr_dir\吃醋后醉酒的芬妮_saved\frame_0.jpg")