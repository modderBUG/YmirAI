# coding=utf-8
import cv2
import cv2
from PIL import Image
import imagehash
import os
import shutil
from video_download import video_download
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
def deal_v():
    video = cv2.VideoCapture(r"C:\Users\wwwwi\Downloads\【尘白】当分析员有了孩子后（1）.mp4")

    def extract_key_frames(video, threshold=0.1):
        previous_frame = None
        key_frames = []
        while video.isOpened():
            ret, current_frame = video.read()
            if not ret:
                break
            if previous_frame is None:
                previous_frame = current_frame
                key_frames.append(current_frame)
            diff = cv2.absdiff(previous_frame, current_frame)
            if diff.mean() > threshold:
                key_frames.append(current_frame)
                previous_frame = current_frame
        return key_frames

    key_frames = extract_key_frames(video, threshold=0.95)

    for index, frame in enumerate(key_frames):
        cv2.imwrite(f'tmp/frame_{index}.jpg', frame)


def extract_key_frames(video, threshold=0.1, time_interval=2):
    fps = video.get(cv2.CAP_PROP_FPS)  # Get the frame rate
    frame_interval = int(fps * time_interval)  # Calculate the number of frames for 2 seconds
    previous_frame = None
    key_frames = []
    frame_count = 0  # To keep track of the current frame index

    while video.isOpened():
        ret, current_frame = video.read()
        if not ret:
            break

        if previous_frame is None or frame_count % frame_interval == 0:
            # Only consider the frame if it's the first frame or spaced by the defined interval
            if previous_frame is not None:
                diff = cv2.absdiff(previous_frame, current_frame)
                if diff.mean() > threshold:
                    key_frames.append(current_frame)
            previous_frame = current_frame

        frame_count += 1

    return key_frames


def call_img(url):
    video = cv2.VideoCapture(url)
    file_name = os.path.basename(url).split(".")[0]
    dir_name = file_name
    tmp_dir = str(hash(file_name))

    os.makedirs(tmp_dir)
    os.makedirs(f"{dir_name}_saved")

    key_frames = extract_key_frames(video, threshold=0.1)
    for index, frame in enumerate(key_frames):

        cv2.imwrite(f"{tmp_dir}/frame_{index}.jpg", frame)

    video.release()  # Don't forget to release the video capture object

    def is_similar(image1, image2, threshold=5):
        hash1 = imagehash.phash(Image.open(image1))
        hash2 = imagehash.phash(Image.open(image2))
        return hash1 - hash2 < threshold

    def filter_similar_images(directory, threshold=5):
        images = sorted(os.listdir(directory))
        unique_images = []

        for i in range(len(images)):
            current_image_path = os.path.join(directory, images[i])
            is_unique = True

            for unique_image in unique_images:
                if is_similar(current_image_path, unique_image, threshold):
                    is_unique = False
                    break

            if is_unique:
                unique_images.append(current_image_path)

        return unique_images

    # 过滤相似图片
    unique_frames = filter_similar_images(tmp_dir, threshold=5)

    # 输出不相似的图片
    for index, frame in enumerate(unique_frames):
        print(f"Unique frame saved: {frame}")
        shutil.move(frame, f"{dir_name}_saved/{os.path.basename(frame)}")
    shutil.rmtree(tmp_dir)



def download_and_convert(url):
    v_name = video_download(url)
    call_img(v_name)
    return v_name

def run_urls_task(urls:list):

    if not os.path.exists("download"):
        os.mkdir('download')

    with ThreadPoolExecutor(5) as pool:
        video_names = list(tqdm(pool.map(download_and_convert,urls),desc="process",total=len(urls)))

    print(f"task done !:{video_names}")


if __name__ == '__main__':

    urls = [
        "https://www.bilibili.com/video/BV1FM4m1r7S1",
        # "https://www.bilibili.com/video/BV1NS411A7gA",
        # "https://www.bilibili.com/video/BV11S411P7aR",
        # "https://www.bilibili.com/video/BV1sf421Q7iG",
        # "https://www.bilibili.com/video/BV1UT421v7nj",
        # "https://www.bilibili.com/video/BV1Gm42157PG",
        # "https://www.bilibili.com/video/BV1Li421v74Y",
        # "https://www.bilibili.com/video/BV1bZ421p7y4",
        # "https://www.bilibili.com/video/BV1cD421g711",
        # "https://www.bilibili.com/video/BV194421X7vn",
        # "https://www.bilibili.com/video/BV1h4421S7Ng",
        # "https://www.bilibili.com/video/BV1Tf421Q7W4",
        # "https://www.bilibili.com/video/BV13z421z7S6",
        # "https://www.bilibili.com/video/BV1NH4y1w7uQ",
        # "https://www.bilibili.com/video/BV194421Q7pj",
        # "https://www.bilibili.com/video/BV1Af421z7rp",
        # "https://www.bilibili.com/video/BV1HAHUeQE54",
        # "https://www.bilibili.com/video/BV1MKpMeHENU",
        # "https://www.bilibili.com/video/BV1LHWheYEWr",
        # "https://www.bilibili.com/video/BV1ynpdejELq",
        # "https://www.bilibili.com/video/BV1JFenePEPV",
        # "https://www.bilibili.com/video/BV15hYSerEmW",
        # "https://www.bilibili.com/video/BV1fzvme5Ewo",
        # "https://www.bilibili.com/video/BV1uwvrejEod",
        # "https://www.bilibili.com/video/BV1dT421k7Vh",
        # "https://www.bilibili.com/video/BV17w4m1Y7tM",
        # "https://www.bilibili.com/video/BV1My411i7oR",
        # "https://www.bilibili.com/video/BV1zr421T7q8",
    ]

    run_urls_task(urls)

    # download_and_convert('https://www.bilibili.com/video/BV1zr421T7q8')

    # print(os.path.abspath("converted_img/里芙芬妮的正宫之争【尘白禁区】"))

