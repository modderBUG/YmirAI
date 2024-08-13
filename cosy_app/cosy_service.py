import json
import requests
import logging
import traceback
from configs.config_prompts import prompts_kesya
from configs.project_config import *

logger = logging.getLogger("cosy_server")


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


api_url = API_URL
api_header = API_HEADERS
model_type = MODEL_TYPE


def response_stream(code=200, message="ok", data=None):
    """
    定义服务返回结构
    """
    response = {
        'code': code,
        'message': message,
        'data': data
    }
    return json.dumps(response, ensure_ascii=False, indent=None)


def stream_chat(messages):
    data = {
        "model": model_type,
        "messages": messages,
        "stream": True,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": TOP_K,
        "max_tokens": MAX_TOKENS,
    }
    response = None
    try:
        with requests.post(api_url, headers=api_header, json=data, stream=True) as res:
            for line in res.iter_lines():
                try:
                    # 解析 JSON
                    json_data = json.loads(line.decode('utf-8')[6:])
                    # 提取 content 字段
                    content = json_data['choices'][0]['delta'].get("content", "")

                    yield content

                except json.JSONDecodeError:
                    # 忽略解析错误
                    continue
            yield "data: [DONE]\n"
    except Exception as e:
        logger.error(f"input:{data}\noutput:{response}\n{str(e)}\ntraceback:{traceback.format_exc()}")


def with_char_stream_chat(history, query):
    """
    根据query生成新的clause
    :return:
    """

    message = [
        {"role": "system", "content": f"{prompts_kesya}"},
        {"role": "assistant", "content": f"想我了么？"},
    ]

    for user_text, assistant_text in history:
        message.append({"role": "user", "content": user_text})
        message.append({"role": "assistant", "content": assistant_text})

    message.append({"role": "user", "content": query})

    new_his = [query, ""]
    history.append(new_his)

    for i in stream_chat(message):

        if i == "data: [DONE]\n":
            break

        history[-1] = [query, i]

        res = {
            "output": i,
            "history": history
        }

        new_data_str = f"data: {response_stream(data=res)}\n"
        # 逐个返回新的 JSON 数据
        yield new_data_str
    yield "data: [DONE]\n"


if __name__ == '__main__':
    pass
