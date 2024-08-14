import time

from flask import Flask, Response

from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许所有域名的跨域请求


@app.route('/text/stream',methods=['POST'])
def stream_text():
    text = "你好，我叫小娜。"

    def generate():
        for char in text:
            time.sleep(0.25)
            yield "data: "+ char + "\n\n"
        yield 'data: [DONE]\n\n'

    return Response(generate(), content_type='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True,port=8888)
