from .base import BaseParser, ParsedDocument, DocumentSection, TermDefinition
from .docx_parser import DocxParser
from .pdf_parser import PdfParser


def get_parser(file_path: str) -> BaseParser:
    """根据文件扩展名返回对应解析器"""
    ext = file_path.rsplit(".", 1)[-1].lower()
    if ext in ("docx", "doc"):
        return DocxParser()
    elif ext == "pdf":
        return PdfParser()
    else:
        raise ValueError(f"不支持的文件格式: {ext}，请使用 .docx 或 .pdf")


__all__ = [
    "BaseParser", "ParsedDocument", "DocumentSection", "TermDefinition",
    "DocxParser", "PdfParser", "get_parser"
]
