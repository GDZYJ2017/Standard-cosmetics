import re
from typing import List
from .base import BaseParser, ParsedDocument, DocumentSection, TermDefinition

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class PdfParser(BaseParser):
    """PDF 文档解析器（基于 pdfplumber + 启发式规则重建结构）"""

    # 标题特征：字体较大、或符合章节编号格式
    HEADING_PATTERN = re.compile(
        r'^([A-Z]?\d+(?:\.\d+)*)\s+\S'   # 带编号标题
    )
    # 无编号但可能是章节名（全大写或首字母大写短行）
    SPECIAL_HEADING = re.compile(r'^(前\s*言|引\s*言|范\s*围|目\s*次|附\s*录)')

    def parse(self, file_path: str) -> ParsedDocument:
        if not PDF_AVAILABLE:
            raise ImportError("pdfplumber 未安装，请运行: pip install pdfplumber")

        with pdfplumber.open(file_path) as pdf:
            all_lines = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_lines.extend(text.split("\n"))

        full_text = "\n".join(line for line in all_lines if line.strip())
        title = self._find_title(all_lines)
        sections = self._rebuild_sections(all_lines)
        terms = self._extract_terms(sections)

        return ParsedDocument(
            title=title,
            sections=sections,
            terms=terms,
            full_text=full_text,
            metadata={"file_type": "pdf", "lines": len(all_lines)}
        )

    def _find_title(self, lines: List[str]) -> str:
        """启发式查找文档标题：前20行中最长的非编号行"""
        candidates = []
        for line in lines[:30]:
            line = line.strip()
            if line and len(line) > 8 and not self.HEADING_PATTERN.match(line):
                candidates.append(line)
        if candidates:
            return max(candidates, key=len)
        return "未知标题"

    def _rebuild_sections(self, lines: List[str]) -> List[DocumentSection]:
        """重建文档章节结构"""
        sections: List[DocumentSection] = []
        current_section = None
        current_content = []

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            is_heading = bool(self.HEADING_PATTERN.match(line_stripped)) or \
                         bool(self.SPECIAL_HEADING.match(line_stripped))

            if is_heading:
                if current_section is not None:
                    current_section.content = "\n".join(current_content)
                    sections.append(current_section)
                    current_content = []

                number = self._extract_section_number(line_stripped)
                if number:
                    level = self._get_level_from_number(number)
                    title_text = re.sub(r'^[A-Z]?\d+(?:\.\d+)*\s+', '', line_stripped).strip()
                else:
                    level = 0
                    title_text = line_stripped
                    number = ""

                current_section = DocumentSection(
                    number=number,
                    title=title_text,
                    level=level,
                    content="",
                    raw_heading=line_stripped
                )
            else:
                if current_section is not None:
                    current_content.append(line_stripped)

        if current_section is not None:
            current_section.content = "\n".join(current_content)
            sections.append(current_section)

        return sections

    def _extract_terms(self, sections: List[DocumentSection]) -> List[TermDefinition]:
        """从术语章节提取术语"""
        terms = []
        term_keywords = ["术语", "定义", "术语和定义"]
        term_sections = [
            s for s in sections
            if any(kw in s.title for kw in term_keywords)
        ]
        for sec in term_sections:
            lines = sec.content.split("\n")
            for i, line in enumerate(lines):
                m = re.match(r'^(\d+\.\d+(?:\.\d+)?)\s+(.+)', line.strip())
                if m:
                    definition = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    terms.append(TermDefinition(
                        term=m.group(2).strip(),
                        definition=definition,
                        section=sec.number
                    ))
        return terms
