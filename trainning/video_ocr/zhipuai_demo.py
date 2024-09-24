import base64
from zhipuai import ZhipuAI

img_path = r"D:\projects\pythonproject\YmirAI\trainning\video_ocr\ocr_dir\里芙芬妮的正宫之争【尘白禁区】_saved\frame_3.jpg"
with open(img_path, 'rb') as img_file:
    img_base = base64.b64encode(img_file.read()).decode('utf-8')

client = ZhipuAI(api_key="292f3523ec14f6a97da3e748844afff4.ReUUNKOWFXJcMdIM") # 填写您自己的APIKey
response = client.chat.completions.create(
    model="glm-4v-plus",  # 填写需要调用的模型名称
    messages=[
      {
        "role": "user",
        "content": [
          {
            "type": "image_url",
            "image_url": {
                "url": img_base
            }
          },
          {
            "type": "text",
            "text": "请描述这个图片"
          }
        ]
      }
    ]
)
print(response.choices[0].message)