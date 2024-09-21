import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor

import tqdm


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


if __name__ == '__main__':
    # send_ocr_request(r"D:\projects\pythonproject\YmirAI\trainning\video_ocr\ocr_dir\吃醋后醉酒的芬妮_saved\frame_0.jpg")

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
