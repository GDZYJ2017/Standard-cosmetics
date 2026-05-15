from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class DocumentSection:
    """文档章节"""
    number: str          # 章节编号，如 "1", "1.1", "2.3.1"
    title: str           # 章节标题
    level: int           # 层级深度：1=章, 2=条, 3=款
    content: str         # 章节正文
    raw_heading: str     # 原始标题文本（含编号）


@dataclass
class TermDefinition:
    """术语定义"""
    term: str
    definition: str
    section: str         # 所在章节


@dataclass
class ParsedDocument:
    """解析后的文档"""
    title: str
    sections: List[DocumentSection] = field(default_factory=list)
    terms: List[TermDefinition] = field(default_factory=list)
    full_text: str = ""
    metadata: Dict = field(default_factory=dict)

    def get_section(self, number: str) -> Optional[DocumentSection]:
        for s in self.sections:
            if s.number == number:
                return s
        return None

    def get_chapter_numbers(self) -> List[str]:
        return [s.number for s in self.sections if s.level == 1]


class BaseParser(ABC):
    """文档解析器基类"""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        pass

    def _extract_section_number(self, text: str) -> Optional[str]:
        """从标题文本中提取章节编号"""
        import re
        text = text.strip()
        # 匹配 "1", "1.1", "1.1.1", "A.1" 等格式
        m = re.match(r'^([A-Z]?\d+(?:\.\d+)*)\s+', text)
        if m:
            return m.group(1)
        # 匹配纯数字行（章级别）
        m = re.match(r'^(\d+)$', text)
        if m:
            return m.group(1)
        return None

    def _get_level_from_number(self, number: str) -> int:
        """根据编号推断层级"""
        if not number:
            return 1
        return len(number.split('.'))
