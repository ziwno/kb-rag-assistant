"""Celery Worker 启动模块。

启动命令: celery -A celery_worker worker --loglevel=info
"""
from app.tasks.file_processor import celery_app

__all__ = ["celery_app"]
