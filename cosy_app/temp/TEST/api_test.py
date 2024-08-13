import time
import requests
import json

api = "http://127.0.0.1:8213"
def test_chat_with_char():

    # 有query

    req_body = {
        "stream":True,
        "query":"再生成4000字符的文本长度",
        "history":[],
    }

    start = time.time()
    print("input:", json.dumps(req_body, ensure_ascii=False, indent=4))
    with  requests.post(f"{api}/api/v1/chat/clause", json=req_body,stream=True) as res:
        print("time used",time.time()-start)
        for line in res.iter_lines():
            print(line.decode("utf-8"))


if __name__ == '__main__':
    test_chat_with_char()
