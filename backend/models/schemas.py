from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class StandardCreate(BaseModel):
    name: str
    number: str
    description: Optional[str] = ""


class StandardOut(BaseModel):
    id: str
    name: str
    number: str
    file_name: str
    file_type: str
    file_size: int
    upload_time: datetime
    description: str

    class Config:
        from_attributes = True


class ReviewTaskCreate(BaseModel):
    name: str
    standard_id: str


class ReviewTaskOut(BaseModel):
    id: str
    batch_id: Optional[str] = None
    name: str
    standard_id: str
    draft_file_name: str
    draft_file_type: str
    status: str
    progress: int
    current_step: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    parsing_started_at: Optional[datetime] = None
    analysis_started_at: Optional[datetime] = None
    error_msg: str
    score: Optional[float] = None
    critical_issues: Optional[int] = 0
    major_issues: Optional[int] = 0
    minor_issues: Optional[int] = 0

    class Config:
        from_attributes = True


class IssueItem(BaseModel):
    id: str
    level: str          # critical / major / minor / suggestion
    category: str       # format / completeness / terminology / semantic
    section: str        # 章节号
    title: str          # 问题标题
    description: str    # 问题描述
    reference: str      # 参考依据
    suggestion: str     # 改进建议


class ReportData(BaseModel):
    task_id: str
    task_name: str
    draft_file: str
    reference_standard: str
    total_issues: int
    critical_issues: int
    major_issues: int
    minor_issues: int
    score: float
    issues: List[IssueItem]
    created_at: datetime


class ReportOut(BaseModel):
    id: str
    task_id: str
    total_issues: int
    critical_issues: int
    major_issues: int
    minor_issues: int
    score: float
    created_at: datetime

    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[Any] = None
