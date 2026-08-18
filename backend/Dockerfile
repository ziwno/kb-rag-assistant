# 后端镜像: Python 3.11 + FastAPI
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 先复制依赖清单，利用 Docker 层缓存加快重建
# 使用清华 PyPI 镜像加速国内网络下的依赖安装 (可覆盖: --build-arg PIP_INDEX_URL=...)
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
COPY requirements.txt .
RUN pip install --upgrade pip -i ${PIP_INDEX_URL} \
    && pip install -r requirements.txt -i ${PIP_INDEX_URL}

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
