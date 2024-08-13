# YmirAI
构建世界树公司的智能体项目

# 效果演示

```html
<iframe frameborder="no" border="0" marginwidth="0" marginheight="0" width=330 height=86 src="cosy_app/character/changchun/2ynqkip0d01q7imqx0crvebanywu8ld.mp3">音频文件无法显示</iframe>

<audio src="cosy_app/character/changchun/2ynqkip0d01q7imqx0crvebanywu8ld.mp3">音频文件无法显示</audio>
```



| 角色 | 原声音                                                                                                           | AI合成                                                                    |
|----|---------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| 逸仙 | [点击播放音频](cosy_app/character/yixian/rwertoem4id64mao2x9hcs96l4tstnu.mp3)<br/>嗯，对女性做出这样的举动，想必指挥官也做好承担后果的心理准备了吧？ | [点我播放音频](assert/yixian.html)</br>指挥官，需要帮忙吗。...呵，让我来帮指挥官大人缓解作战的疲劳吧...呵呵。 |
|    |                                                                                                               |                                                                         |
|    |                                                                                                               |                                                                         |


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


