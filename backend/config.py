import os
from dotenv import load_dotenv

load_dotenv()

# AI API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 应用
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# 文件存储
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
STANDARDS_DIR = os.path.join(DATA_DIR, "standards")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

# 规范文档路径（化妆品检验方法标准文本规范）
SPEC_INSPECTION_METHOD = os.path.join(STANDARDS_DIR, "化妆品检验方法标准文本规范.md")

# 数据库（使用绝对路径，避免工作目录不一致）
_db_path = os.path.join(DATA_DIR, "standard_review.db").replace("\\", "/")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_db_path}")

# 上传限制
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# 确保目录存在
for d in [DATA_DIR, UPLOAD_DIR, STANDARDS_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)
