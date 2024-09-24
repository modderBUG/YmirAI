import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import base64
import tqdm
from PIL import Image, ImageEnhance,ImageFilter
import io
from PIL import Image
import io

def enhance_image(image, contrast_factor=1.5, gamma_factor=1.5):
    # 增强对比度
    enhancer = ImageEnhance.Contrast(image)
    enhanced_image = enhancer.enhance(contrast_factor)

    # 增强 gamma
    # 使用 gamma 校正公式: output = 255 * (input / 255) ** (1 / gamma)
    gamma_corrected = enhanced_image.point(lambda x: 255 * (x / 255) ** (1 / gamma_factor))

    return gamma_corrected


def crop_black_borders(image_path):
    # 打开图片
    image = Image.open(image_path)

    # 转换为灰度图
    gray_image = image.convert("L")

    # 获取图片的尺寸
    width, height = gray_image.size

    # 找到黑边的边界
    left, upper, right, lower = 0, 0, width, height

    # 查找左边界
    for x in range(width):
        if gray_image.crop((x, 0, x + 1, height)).getextrema()[0] > 0:
            left = x
            break

    # 查找右边界
    for x in range(width - 1, -1, -1):
        if gray_image.crop((x, 0, x + 1, height)).getextrema()[0] > 0:
            right = x + 1
            break

    # 查找上边界
    for y in range(height):
        if gray_image.crop((0, y, width, y + 1)).getextrema()[0] > 0:
            upper = y
            break

    # 查找下边界
    for y in range(height - 1, -1, -1):
        if gray_image.crop((0, y, width, y + 1)).getextrema()[0] > 0:
            lower = y + 1
            break

    # 裁剪图片
    cropped_image = image.crop((left, upper, right, lower))

    # 如果没有裁剪，返回原图的 BytesIO
    if left == 0 and upper == 0 and right == width and lower == height:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=95)  # 保存原图为JPEG
        img_byte_arr.seek(0)
        # image.save("aaaa.png")
        return img_byte_arr

    # 将裁剪后的图片保存到 BytesIO
    img_byte_arr = io.BytesIO()
    cropped_image.save(img_byte_arr, format='JPEG', quality=95)  # 保存裁剪后的图像为JPEG
    img_byte_arr.seek(0)  # 重置指针到开始位置
    # cropped_image.save("aaaa.png")

    return img_byte_arr
# 示例用法
# cropped_image_bytes = crop_black_borders('path/to/your/image.png')


def encode_image(image_path):
    image_file = crop_black_borders(image_path)


    return base64.b64encode(image_file.read()).decode('utf-8')

QWEN_CHAT_URL = "http://74.120.172.183:8216/v1/chat/completions"
def qwen_chat(prompts):
    data = {
        "model": "Qwen2-7B-Instruct-GPTQ-Int4",  # "chatglm3-6b",
        "messages": prompts,
        "temperature": 0.01,  # 调整温度，通常介于0.2和1.0之间
        # "top_k": 5,
        # "top_P": 1,
        "max_tokens": 768,
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



sys_prompts = '''你是图片文字识别专家，从图片中提取文本。
- 任务要求：识别图片中的文本，包括：角色名称、对话记录、旁白文本
注意版面右侧角色是分析员
- 输出格式
张三：xxx
分析员：xxx

'''


def chat_with_img(image_path):
    base64_image = encode_image(image_path)
    messages = [
        {
            "role": "system",
            "content": sys_prompts
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "提取以下对话，逐行输出记录和旁白文本："},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ]

    res = qwen_chat(messages)
    return res


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
import re
def natural_sort_key(filename):
    # 使用正则表达式提取数字部分
    return [int(text) if text.isdigit() else text for text in re.split(r'(\d+)', filename)]

def main():
    main_dir = 'ocr_dir'

    ocr_dirs = os.listdir(main_dir)

    for dir_name in ocr_dirs:
        files = os.listdir(f"{main_dir}/{dir_name}")
        task_img = [f"{main_dir}/{dir_name}/{i}" for i in files]
        task_img = sorted(task_img, key=natural_sort_key)

        with ThreadPoolExecutor(3) as pool:
            res = list(tqdm.tqdm(pool.map(chat_with_img, task_img), desc="img", total=len(task_img)))

        # pages = [page for page in res]
        # pages = ["\n".join(page) for page in res]
        all_text = "\n---\n".join(res)

        with open(f"{dir_name}.txt", "w", encoding="utf-8") as f:
            f.write(all_text)


if __name__ == '__main__':
    main()
    # send_ocr_request(r"D:\projects\pythonproject\YmirAI\trainning\video_ocr\ocr_dir\吃醋后醉酒的芬妮_saved\frame_0.jpg")

    # chat_with_img(r"D:\projects\pythonproject\YmirAI\trainning\video_ocr\ocr_dir\芙提雅小老师的新发明【尘白禁区】_saved\frame_0.jpg")