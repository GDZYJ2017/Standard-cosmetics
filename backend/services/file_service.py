import os
import uuid
import shutil
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import STANDARDS_DIR, UPLOAD_DIR, MAX_UPLOAD_SIZE_BYTES

ALLOWED_EXTENSIONS = {".docx", ".doc", ".pdf"}


def get_file_ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def validate_upload(filename: str, file_size: int) -> tuple:
    """验证上传文件，返回 (ok, error_msg)"""
    ext = get_file_ext(filename)
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件格式 '{ext}'，请上传 PDF 或 Word (.docx) 文件"
    if file_size > MAX_UPLOAD_SIZE_BYTES:
        return False, f"文件大小超出限制（最大 {MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB）"
    return True, ""


async def save_standard_file(file_content: bytes, original_name: str) -> dict:
    """保存参考标准文件"""
    ext = get_file_ext(original_name)
    file_id = uuid.uuid4().hex
    file_name = f"{file_id}{ext}"
    file_path = os.path.join(STANDARDS_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(file_content)

    return {
        "id": file_id,
        "file_name": original_name,
        "file_path": file_path,
        "file_type": ext.lstrip("."),
        "file_size": len(file_content)
    }


async def save_draft_file(file_content: bytes, original_name: str) -> dict:
    """保存待审初稿文件"""
    ext = get_file_ext(original_name)
    file_id = uuid.uuid4().hex
    file_name = f"{file_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(file_content)

    return {
        "id": file_id,
        "file_name": original_name,
        "file_path": file_path,
        "file_type": ext.lstrip("."),
        "file_size": len(file_content)
    }


def delete_standard_file(file_path: str):
    """删除标准文件"""
    if os.path.exists(file_path):
        os.remove(file_path)


def delete_draft_file(file_path: str):
    """删除初稿文件"""
    if os.path.exists(file_path):
        os.remove(file_path)
