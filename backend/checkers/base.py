from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass, field
from parsers.base import ParsedDocument
import uuid


@dataclass
class Issue:
    """单个检查问题"""
    id: str = ""
    level: str = "minor"       # critical / major / minor / suggestion
    category: str = ""         # format / completeness / terminology / semantic
    section: str = ""          # 章节号
    title: str = ""
    description: str = ""
    reference: str = ""
    suggestion: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:8]


@dataclass
class CheckResult:
    """检查结果集"""
    category: str
    checker_name: str
    issues: List[Issue] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "critical")

    @property
    def major_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "major")

    @property
    def minor_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "minor")

    @property
    def suggestion_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "suggestion")


class BaseChecker(ABC):
    """检查器基类"""

    @abstractmethod
    def check(self, draft: ParsedDocument, reference: Optional[ParsedDocument] = None) -> CheckResult:
        pass
