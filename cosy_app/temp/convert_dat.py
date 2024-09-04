import json


def find_id_by_name(json_list, char_id):
    """在 JSON 列表中查找具有指定名称的对象，并返回其 ID。

    参数:
        json_list (list): 包含 JSON 对象的列表。
        name (str): 要查找的名称。

    返回:
        str or None: 找到的 ID，如果未找到则返回 None。
    """
    for item in json_list:
        if item.get('char_id') == char_id:
            return item.get('name')
    return None


def loadjson(file_path):
    """从 JSON 文件中加载数据。

    参数:
        file_path (str): JSON 文件的路径。

    返回:
        dict or list: 解析后的 JSON 数据。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
    except json.JSONDecodeError:
        print(f"文件不是有效的 JSON 格式: {file_path}")
    except Exception as e:
        print(f"发生错误: {e}")


# 示例用法
data1 = loadjson('closure-talk-2024-07-14-14-11-22.json')

data2 = loadjson('closure-talk-2024-07-25-12-30-53.json')
data3 = loadjson('closure-talk-2024-08-05-12-40-41.json')

datas = [data1, data2, data3]

if __name__ == '__main__':
    for data in datas:
        context = []
        for chat in data['chat']:
            content = chat["content"]
            if chat.get('char_id', None):
                name = find_id_by_name(data['custom_chars'], chat.get('char_id'))
                if chat['yuzutalk']['type'] == "NARRATION":
                    context.append(f"({content})")
                else:
                    context.append(f"{name}: {content}")
            else:
                if chat['yuzutalk']['type'] == "NARRATION":
                    context.append(f"({content})")
                else:
                    context.append(f"分析员: {content}")

        print("\n".join(context))
