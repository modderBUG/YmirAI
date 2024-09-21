import json


def _convert_niko():
    with open('datasets/cat.txt', "r", encoding="utf-8") as f:
        text = f.read()

    SYS = text.split("///")[0]
    history = text.split("///")[1:]

    import json

    # 创建一个空列表来存储结果
    json_list = [{
        "role": "system",
        "content": SYS
    }]

    # 遍历 history 列表并组装成字典格式
    for i in range(len(history)):
        role = "user" if i % 2 == 0 else "assistant"
        json_list.append({"role": role, "content": history[i].strip().strip("\n")})

    data = {
        "conversations": json_list
    }

    with open("datasets/niko_cat.jsonl", 'w', encoding="utf-8") as f:
        json.dump(obj=data, fp=f, ensure_ascii=False)

    print()
    # 转换为 JSON 格式
    json_output = json.dumps(json_list, ensure_ascii=False, indent=2)

    print(json_output)


from convert_dat import loadjson,list_to_jsonl

a = loadjson("datasets/niko_cat.jsonl")

sys = a['conversations'][0]
dialog = a['conversations'][1:]

conversations = []

start = 0
conversation = [sys]

for i in range(0, len(dialog), 2):
    user = dialog[i]
    assistant = dialog[i + 1]

    user_text = user['content']
    assistant_text = assistant['content']
    start += len(user_text)
    start += len(assistant_text)
    if start > 2048:
        start = 0
        conversations.append({"conversations":conversation})
        conversation = [sys]
    conversation.append(user)
    conversation.append(assistant)

# if len(conversation)>1:
#     conversations.append(conversation)

print(json.dumps(conversations,ensure_ascii=False,indent=3))
# list_to_jsonl(conversations,"datasets/niko_chat.jsonl")

if __name__ == '__main__':
    pass
