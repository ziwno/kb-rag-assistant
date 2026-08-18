"""PDF 文本提取。

优先使用 pdfplumber (表格/版式还原更好)，失败时回退 PyPDF2。
"""
import logging

import pdfplumber
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def extract_text(file_path: str) -> str:
    """提取 PDF 全文，页间以空行分隔。"""
    texts: list[str] = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                texts.append(page_text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("pdfplumber 解析失败 (%s)，回退到 PyPDF2", exc)
        reader = PdfReader(file_path)
        for page in reader.pages:
            texts.append(page.extract_text() or "")

    return "\n\n".join(texts).strip()
