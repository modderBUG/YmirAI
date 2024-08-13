import json

# server config
SERVER_PORT = 8213
SERVER_NAME = "0.0.0.0"

# llm api config
TEMPERATURE = 0.8
TOP_P = 0.8
TOP_K = 30
MAX_TOKENS = 208

API_HEADERS = {
    'Content-Type': 'application/json',
}

API_URL = 'http://74.120.172.183:8216/v1/chat/completions'
MODEL_TYPE = "Qwen2-7B-Instruct-GPTQ-Int4"

TOKEN_EXPIRATION_TIME = 3600