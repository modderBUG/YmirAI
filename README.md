# YmirAI
构建世界树公司的智能体项目。
尝试和各种虚拟角色进行语音聊天吧~

# 效果演示

| 角色                                  | 原声音                                                                                                           | AI合成                                                                    |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| ![逸仙](assert/85px-yixian.jpg)<br>逸仙 | [点击播放音频](http://si5c7yq6z.hn-bkt.clouddn.com/rwertoem4id64mao2x9hcs96l4tstnu.mp3)<br/>嗯，对女性做出这样的举动，想必指挥官也做好承担后果的心理准备了吧？ | [点我播放音频](http://si5c7yq6z.hn-bkt.clouddn.com/yixian.wav)</br>指挥官，需要帮忙吗。...呵，让我来帮指挥官大人缓解作战的疲劳吧...呵呵。 |
|                                     |                                                                                                               |                                                                         |
|                                     |                                                                                                               |                                                                         |

> 外链资源由[七牛云](https://portal.qiniu.com/kodo/bucket/resource-v2?bucketName=modderbug)提供

Demo演示

![占位符](assert/xx)
![占位符](assert/xx)
![占位符](assert/xx)

# TODO
- [x] 完成项目框架
- [x] 完成数据库连接框架
- [x] 语音合成接口
- [x] 登录接口
- [x] 展示角色接口
- [ ] 完成整个后端框架
- [ ] 完成前端框架
- [ ] 完成联调
- [ ] 其他
- [ ] 其他

 
# 项目部署
1. 克隆项目[CosyVoice](https://github.com/FunAudioLLM/CosyVoice)，并下载相关模型
2. 把本项目丢尽CosyVoice目录
```commandline
|- CosyVoice/
    |- YmirAI/
    |- Pretrain/
    |- ...
```
3. 启动qwen2-7b大模型
```commandline
python  -m vllm.entrypoints.openai.api_server  \
--model /home/wuxiaowei/pretrining/fastchat/Qwen2-7B-Instruct-GPTQ-Int4  \
--port 8216 --host 0.0.0.0  \
--max-model-len 16000  --served-model-name Qwen2-7B-Instruct-GPTQ-Int4   \
--tensor-parallel-size 1  --quantization gptq \
--gpu-memory-utilization 0.7
```
4. 启动项目
```commandline
cd CosyVoice/YmirAI
python cosy_server.py
```

# 赞助
- 请我喝咖啡


