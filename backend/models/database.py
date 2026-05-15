from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, JSON
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL, DATA_DIR

# 确保数据目录存在（SQLite 文件要求其父目录存在）
os.makedirs(DATA_DIR, exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class Standard(Base):
    """参考标准文件"""
    __tablename__ = "standards"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)          # 标准名称
    number = Column(String(50), nullable=False)         # 标准号，如 GB/T 1.1-2020
    file_name = Column(String(200), nullable=False)     # 原始文件名
    file_path = Column(String(500), nullable=False)     # 存储路径
    file_type = Column(String(10), nullable=False)      # pdf 或 docx
    file_size = Column(Integer, default=0)
    upload_time = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, default="")


class ReviewBatch(Base):
    """批量审查批次"""
    __tablename__ = "review_batches"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)           # 批次名称（如"2024年第一批送审稿"）
    total_count = Column(Integer, default=0)             # 总任务数
    done_count = Column(Integer, default=0)               # 已完成数
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class ReviewTask(Base):
    """审查任务"""
    __tablename__ = "review_tasks"

    id = Column(String(36), primary_key=True)
    batch_id = Column(String(36), nullable=True)         # 所属批次ID（批量审查时关联）
    name = Column(String(200), nullable=False)
    standard_id = Column(Text, nullable=False)           # 参考标准 ID（多选时用逗号分隔）
    draft_file_name = Column(String(200), nullable=False)
    draft_file_path = Column(String(500), nullable=False)
    draft_file_type = Column(String(10), nullable=False)
    status = Column(String(20), default="pending")        # pending/running/done/failed
    progress = Column(Integer, default=0)                 # 0-100
    current_step = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_msg = Column(Text, default="")

    # ── 各阶段时间戳（用于看板耗时展示）──────────────────────────────────
    parsing_started_at = Column(DateTime, nullable=True)   # 开始解析时间
    analysis_started_at = Column(DateTime, nullable=True) # 开始AI分析时间
    # ── 报告摘要（从ReviewReport反查，为看板列表加速）─────────────────────
    score = Column(Float, nullable=True)                  # 综合评分（仅done时有值）
    critical_issues = Column(Integer, default=0)
    major_issues = Column(Integer, default=0)
    minor_issues = Column(Integer, default=0)


class ReviewReport(Base):
    """审查报告"""
    __tablename__ = "review_reports"

    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), nullable=False, unique=True)
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    major_issues = Column(Integer, default=0)
    minor_issues = Column(Integer, default=0)
    score = Column(Float, default=100.0)
    result_json = Column(Text, default="{}")            # 完整审查结果 JSON
    html_report_path = Column(String(500), default="")
    word_report_path = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
