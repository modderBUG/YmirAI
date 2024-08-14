import random
import requests
import json
from cosy_app.configs.config_prompts import prompts_kesya

def qwen_chat(prompts):
    data = {
        "model": "Qwen2-7B-Instruct-GPTQ-Int4",  # "chatglm3-6b",
        "messages": prompts,
        # "temperature": 0.9,  # 调整温度，通常介于0.2和1.0之间
        # "top_k": 50,
        # "top_P": 1,
        "max_tokens":128,
        "stream": False
    }
    headers = {
        "X-Server-Param": "eyJhcHBpZCI6ICJiZXJ0YmFzZSIsICJjc2lkIjogImJlcnRiYXNlYXBpMDAwMDAwMDAwMDAwMDAwMDAwMDAwM2JmY2VjYzMzZjc2NDU4NmI0NWUxODA4NGRiNzVkNDUifQ==",
        "X-CheckSum": "2b5379d4d06b23bb4a6ad8979c1ab4fb",
    }

    # url = "http://172.16.251.142:9050/chatglm3/v1/chat/completions"
    # url = "http://www.modderbug.cn:8212/v1/chat/completions"

    # url_list = ["http://10.8.13.92:8808/v1/chat/completions","http://10.8.13.92:8808/v1/chat/completions"]
    # url_list = ["http://74.120.172.183:8216/v1/chat/completions","http://74.120.172.183:8216/v1/chat/completions"]
    url_list = ["http://49.232.24.59:80/v1/chat/completions"]

    url = random.choice(url_list)
    res = requests.post(url, json=data, headers=headers)

    print(res.text)

    try:
        print(f"INFO:{res.json()['choices'][0]['message']['content']}")
    except:
        print(f"input ERROR:{json.dumps(data, ensure_ascii=False, indent=2)}")
        print(res.text)
        return None
    return res.json()['choices'][0]['message']['content']


if __name__ == '__main__':

    user_input = "开门啊凯西娅，你在里面吗"
    print(len(prompts_kesya))

    message = [
        {
            "role": "system",
            "content": f"{prompts_kesya}",
        }, {
            "role": "user",
            "content": f"{user_input}",
        }
    ]
    bot_text = qwen_chat(message)

    # message.append({"role":"assistant","content":bot_text})
    #
    #
    # while True:
    #     user_input = input()
    #     message.append({"role":"user","content":user_input})
    #     bot_text = qwen_chat(message)
    #     message.append({"role": "assistant", "content": bot_text})
    #
