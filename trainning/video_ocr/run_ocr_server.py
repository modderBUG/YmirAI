import os
import sys
import subprocess

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, "../..")))
import numpy as np
import cv2
import time
import os
import tools.infer.utility as utility
from tools.infer.predict_system import TextSystem


def merge_ocr_results_by_line(ocr_results, y_threshold=5):
    # 按y坐标排序
    ocr_results.sort(key=lambda x: (x['points'][0][1] + x['points'][2][1]) / 2)

    merged_lines = []
    current_line = []
    current_y = None

    for result in ocr_results:
        # 计算当前文本块的垂直中心
        y_center = (result['points'][0][1] + result['points'][2][1]) / 2

        if current_y is None:
            # 初始化第一行
            current_y = y_center

        if abs(y_center - current_y) <= y_threshold:
            # 如果在同一行内，添加到当前行
            current_line.append(result)
        else:
            # 否则，保存当前行，并开始新的一行
            merged_lines.append(current_line)
            current_line = [result]
            current_y = y_center

    # 添加最后一行
    if current_line:
        merged_lines.append(current_line)

    # 格式化输出
    merged_text = [' '.join([item['transcription'] for item in line]) for line in merged_lines]

    return merged_text


from flask import Flask, request, jsonify
import cv2
import numpy as np
import threading

app = Flask(__name__)


class OCRModel():
    def __init__(self):
        args = utility.parse_args()
        print(args)
        # args['det_model_dir']="./tools/infer/ch_PP-OCRv4_det_infer"
        # args['rec_model_dir']="./tools/infer/ch_PP-OCRv4_rec_infer"
        # args['use_angle_cls']=False

        # args.add_argument("--det_model_dir", type=str,default="./tools/infer/ch_PP-OCRv4_det_infer")
        # args.add_argument("--rec_model_dir", type=str,default="./tools/infer/ch_PP-OCRv4_rec_infer")

        # args.set_defaults(det_model_dir="./tools/infer/ch_PP-OCRv4_det_infer")  # 修改 foo 的默认值
        # args.set_defaults(rec_model_dir="./tools/infer/ch_PP-OCRv4_rec_infer")  # 修改 bar 的默认值

        args.det_model_dir = "./tools/infer/ch_PP-OCRv4_det_infer"
        args.rec_model_dir = "./tools/infer/ch_PP-OCRv4_rec_infer"
        self.text_sys = TextSystem(args)
        self.lock = threading.Lock()  # 线程锁，确保每次只能一个线程使用模型

    def predict(self, img):
        with self.lock:  # 使用上下文管理器来自动处理锁的获取和释放
            dt_boxes, rec_res, time_dict = self.text_sys(img)

        # 将识别结果格式化
        res = [
            {
                "transcription": rec_res[i][0],
                "points": np.array(dt_boxes[i]).astype(np.int32).tolist(),
            }
            for i in range(len(dt_boxes))
        ]
        merged_text = merge_ocr_results_by_line(res)
        return merged_text


# 创建OCR模型的全局实例
ocr_model = OCRModel()


@app.route('/ocr', methods=['POST'])
def ocr_service():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()

    # 将二进制文件转换为OpenCV图像
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "Failed to decode image"}), 400

    try:
        # 调用OCR模型的预测函数
        result = ocr_model.predict(img)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8218)

