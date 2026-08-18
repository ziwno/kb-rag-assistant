"""端到端冒烟测试 (Mock LLM，无需真实 API Key / Docker / Redis)。

用法:
    cd backend
    .venv/Scripts/python.exe scripts/smoke_test.py

覆盖: 健康检查 → 注册/登录 → 上传文本(异步处理) → 状态轮询 → RAG问答(非流式)
      → SSE 流式问答 → 摘要 → 权限校验(401/越权404/非法类型400) → 删除
"""
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

# ---------- 测试配置 (临时目录 + SQLite + 无 Celery) ----------
_tmp = tempfile.mkdtemp(prefix="kb_smoke_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["CHROMA_PERSIST_DIR"] = f"{_tmp}/chroma"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["USE_CELERY"] = "false"
os.environ["SECRET_KEY"] = "smoke-test-secret"
os.environ["LLM_PROVIDER"] = "openai"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.llm.base import LLMProvider  # noqa: E402

# ---------- Mock Provider (确定性向量 + 流式分块) ----------
class MockProvider(LLMProvider):
    def embed_texts(self, texts):
        vecs = []
        for t in texts:
            digest = hashlib.md5(t.encode("utf-8")).digest()
            vecs.append([((b / 255) - 0.5) * 2 for b in digest])  # 16 维
        return vecs

    def complete(self, messages, temperature=0.7):
        user_msg = next(m["content"] for m in reversed(messages) if m["role"] == "user")
        return f"[Mock回答] {user_msg[:30]}..."

    async def astream(self, messages, temperature=0.7):
        for c in ["M", "o", "c", "k", "流", "式", "输", "出"]:
            yield c

    def describe_image(self, image_path, prompt=None):
        return "这是一张示例图片的描述 (Mock)。"

# 注入 Mock: 各模块以 `from ..llm import get_llm_provider` 引用，
# 因此需要分别替换它们命名空间里的函数。
import app.parsers.image_parser as _img  # noqa: E402
import app.services.rag_service as _rag  # noqa: E402
import app.tasks.file_processor as _fp  # noqa: E402

_img.get_llm_provider = lambda: MockProvider()
_rag.get_llm_provider = lambda: MockProvider()
_fp.get_llm_provider = lambda: MockProvider()

from app import main as main_module  # noqa: E402

# 测试用多段中文文本 (超过 chunk_size，可切成多片)
_TEXT = (
    "人工智能（AI）是计算机科学的一个分支，它企图了解智能的实质，"
    "并生产出一种新的能以人类智能相似的方式做出反应的智能机器。\n"
    "机器学习是人工智能的核心，通过算法让计算机从数据中自动学习规律。"
    "深度学习则是机器学习的一个子集，使用多层神经网络进行特征提取。\n"
    "检索增强生成（RAG）结合了信息检索与大语言模型：先检索相关知识片段，"
    "再让模型基于片段生成回答，从而减少幻觉、提高准确性。\n"
    "在知识库助手中，用户上传的 PDF、图片、音频会先被解析为文本，"
    "然后切片、向量化并存入向量数据库，供后续问答检索使用。\n"
    "向量数据库（如 ChromaDB）通过计算向量相似度，快速找到与问题最相关的片段。"
    "这一流程被称为 RAG 流水线。\n"
) * 10

# ---------- 结果统计 ----------
_PASS, _FAIL = [], []


def check(name, cond, extra=""):
    ( _PASS if cond else _FAIL ).append(name)
    print(f"  {'✅' if cond else '❌'} {name} {extra}")


with TestClient(main_module.app) as client:
    print("\n== 1. 健康检查 ==")
    r = client.get("/health")
    check("GET /health", r.status_code == 200 and r.json()["status"] == "ok")

    print("\n== 2. 认证 ==")
    r = client.post("/api/auth/register", json={
        "username": "alice", "email": "alice@example.com", "password": "secret123"})
    check("POST /api/auth/register", r.status_code == 201, str(r.status_code))
    r = client.post("/api/auth/register", json={
        "username": "alice", "email": "alice@example.com", "password": "secret123"})
    check("注册重复用户 → 400", r.status_code == 400)

    r = client.post("/api/auth/login", json={"username": "alice", "password": "secret123"})
    check("POST /api/auth/login", r.status_code == 200 and "access_token" in r.json())
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/users/me", headers=headers)
    check("GET /api/users/me", r.status_code == 200 and r.json()["username"] == "alice")

    r = client.get("/api/files")
    check("未带 token → 401", r.status_code == 401)
    r = client.get("/api/files", headers={"Authorization": "Bearer invalid.token.xxx"})
    check("无效 token → 401", r.status_code == 401)

    # 第二个用户 (用于越权测试)
    client.post("/api/auth/register", json={
        "username": "bob", "email": "bob@example.com", "password": "secret123"})
    r = client.post("/api/auth/login", json={"username": "bob", "password": "secret123"})
    bob_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    print("\n== 3. 文件上传与异步处理 ==")
    r = client.post("/api/files/upload", files={"file": ("sample.txt", _TEXT, "text/plain")},
                    headers=headers)
    check("POST /api/files/upload → 202", r.status_code == 202, str(r.status_code))
    file_id = r.json().get("file_id")
    check("返回 file_id", bool(file_id))

    # 等待后台处理完成
    status = "pending"
    for _ in range(50):
        r = client.get(f"/api/files/{file_id}/status", headers=headers)
        status = r.json()["status"]
        if status in ("completed", "failed"):
            break
        time.sleep(0.2)
    check(f"处理最终状态为 completed (实际: {status})", status == "completed")
    check("chunk_count > 0", r.json()["chunk_count"] > 0)

    r = client.post("/api/files/upload",
                    files={"file": ("bad.exe", b"MZ\x90\x00", "application/octet-stream")},
                    headers=headers)
    check("上传不支持类型 → 400", r.status_code == 400)

    # 越权访问 bob 的 file_id (用 alice 创建的文件)
    r = client.post("/api/files/upload",
                    files={"file": ("bob.txt", b"bob data", "text/plain")},
                    headers=bob_headers)
    bob_file = r.json().get("file_id")
    r = client.get(f"/api/files/{bob_file}/status", headers=headers)
    check("alice 访问 bob 的文件 → 404", r.status_code == 404)

    print("\n== 4. RAG 问答 (非流式) ==")
    r = client.post("/api/chat/query", headers=headers,
                    json={"question": "文档讲了什么?", "file_ids": [file_id]})
    check("POST /api/chat/query", r.status_code == 200 and "answer" in r.json())
    check("回答包含 Mock 标记", "Mock" in r.json().get("answer", ""))
    check("返回引用来源", r.json().get("sources", []) == ["sample.txt"])

    print("\n== 5. SSE 流式问答 ==")
    events = []
    with client.stream("GET",
                       f"/api/chat/stream?question=流式测试&file_ids={file_id}",
                       headers=headers) as resp:
        check("stream 状态码 200", resp.status_code == 200)
        for line in resp.iter_lines():
            if line and line.startswith("data:"):
                events.append(line[5:].strip())
    types = [json.loads(e)["type"] for e in events if e != "[DONE]"]
    check("流包含 start/content/end 事件", {"start", "content", "end"} <= set(types))
    content = "".join(json.loads(e).get("chunk", "") for e in events
                      if e != "[DONE]" and json.loads(e)["type"] == "content")
    check("流式内容正确拼接", content == "Mock流式输出")
    end_sources = [json.loads(e).get("sources") for e in events
                   if e != "[DONE]" and json.loads(e)["type"] == "end"]
    check("结束事件带来源", end_sources and end_sources[0] == ["sample.txt"])

    print("\n== 6. 摘要 ==")
    r = client.post("/api/summarize", headers=headers, json={"file_ids": [file_id]})
    check("POST /api/summarize", r.status_code == 200 and "Mock" in r.json().get("answer", ""))
    r = client.post("/api/summarize", headers=headers, json={"file_ids": []})
    check("空 file_ids → 400", r.status_code == 400)

    print("\n== 7. 文件列表 / 删除 ==")
    r = client.get("/api/files", headers=headers)
    check("GET /api/files 返回 1 个文件", r.status_code == 200 and len(r.json()) == 1)
    r = client.delete(f"/api/files/{file_id}", headers=headers)
    check("DELETE /api/files/{id} → 204", r.status_code == 204)
    r = client.get("/api/files", headers=headers)
    check("删除后文件列表为空", r.status_code == 200 and len(r.json()) == 0)

print("\n" + "=" * 40)
print(f"通过 {len(_PASS)} 项 / 失败 {len(_FAIL)} 项")
if _FAIL:
    print("失败项:", _FAIL)
    sys.exit(1)
print("冒烟测试全部通过 ✅")
sys.exit(0)
