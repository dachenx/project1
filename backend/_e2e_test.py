# -*- coding: utf-8 -*-
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

import requests

base = "http://127.0.0.1:8000"


def log(*a):
    print(*a, flush=True)


# 1. 登录
tok = requests.post(base + "/api/auth/login", json={"username": "admin", "password": "123456"}).json()["access_token"]
h = {"Authorization": "Bearer " + tok}
log("1. 登录成功")

# 2. 建知识库
kb = requests.post(base + "/api/kb", json={"name": "商品测试库"}, headers=h).json()
kb_id = kb["id"]
log("2. 知识库 id =", kb_id)

# 3. 上传文档
with open("_sample_products.txt", "rb") as f:
    r = requests.post(base + f"/api/kb/{kb_id}/documents", files={"file": ("sample_products.txt", f, "text/plain")}, headers=h)
doc = r.json()
doc_id = doc["id"]
log("3. 文档 id =", doc_id, "status =", doc["status"])

# 4. 轮询直到 ready（首次会下载 BGE 模型，较慢）
status = "parsing"
for i in range(90):
    docs = requests.get(base + f"/api/kb/{kb_id}/documents", headers=h).json()
    d = next((x for x in docs if x["id"] == doc_id), None)
    if d is None:
        log("文档不见了")
        break
    status = d["status"]
    if status == "ready":
        log("4. 入库完成，分块数 =", d["chunk_count"])
        break
    if status == "failed":
        log("4. 入库失败:", d.get("error"))
        break
    time.sleep(5)

if status != "ready":
    log("4. 未能入库完成，终止")
    sys.exit(1)

# 5. 新建会话
conv = requests.post(base + "/api/conversations", json={}, headers=h).json()
cid = conv["id"]
log("5. 会话 id =", cid)

# 6. 流式问答
question = "小米14的处理器和电池容量是多少？"
log("6. 提问:", question)
r = requests.post(base + f"/api/chat/{cid}", json={"question": question, "kb_id": kb_id}, headers=h, stream=True)
for line in r.iter_lines():
    if line:
        log(line.decode("utf-8"))

log("=== E2E 测试完成 ===")
