import json
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NETEASE_API_KEY", "")
API_URL = "https://api.siliconflow.cn/v1/embeddings"
MODEL = "BAAI/bge-large-zh-v1.5"

VOCAB_PATH = os.path.join(os.path.dirname(__file__), "../vocab/ielts_vocab.json")
CACHE_PATH = os.path.join(os.path.dirname(__file__), "../vocab/ielts_meanings_embedding_cache.json")

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# 获取 meanings 的 embedding
def get_embedding(text):
    payload = {
        "model": MODEL,
        "input": text,
        "encoding_format": "float"
    }
    resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
    if resp.status_code != 200:       
        print(f"API 响应内容: {resp.text}")
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]

# 读取词汇表
with open(VOCAB_PATH, "r", encoding="utf-8") as f:
    vocab = json.load(f)

cache = []
for entry in vocab:
    word = entry.get("word", "")
    meanings = entry.get("meanings", [])
    if not meanings:
        continue
    # 合并所有 meanings 作为一个语义单元
    text = "；".join(meanings)
    try:
        embedding = get_embedding(text)
        cache.append({
            "word": word,
            "meanings": meanings,
            "embedding": embedding
        })
        print(f"{word} 已缓存 embedding。")
    except Exception as e:
        print(f"{word} embedding 失败: {e}")
    time.sleep(0.8)  # 避免 API 请求过快

with open(CACHE_PATH, "w", encoding="utf-8") as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

print(f"全部完成，embedding 缓存已保存于 {CACHE_PATH}") 