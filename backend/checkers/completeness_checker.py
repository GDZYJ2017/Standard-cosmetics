import os
import yaml
from typing import Optional, Set, List
from .base import BaseChecker, CheckResult, Issue
from parsers.base import ParsedDocument


class CompletenessChecker(BaseChecker):
    """内容完整性检查器 - 对比参考标准章节结构"""

    def __init__(self, rules_path: Optional[str] = None):
        if rules_path is None:
            rules_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "rules", "base_rules.yaml"
            )
        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f)

    def check(self, draft: ParsedDocument, reference: Optional[ParsedDocument] = None) -> CheckResult:
        result = CheckResult(category="completeness", checker_name="内容完整性检查")
        result.issues.extend(self._check_basic_sections(draft))
        if reference:
            result.issues.extend(self._check_against_reference(draft, reference))
        return result

    def _check_basic_sections(self, draft: ParsedDocument) -> List[Issue]:
        """检查基础必要章节"""
        issues = []
        required = self.rules.get("required_sections", [])
        draft_titles = {s.title.strip() for s in draft.sections}
        draft_headings = {s.raw_heading.strip() for s in draft.sections}

        for sec_def in required:
            keywords = sec_def.get("keywords", [])
            found = False
            for kw in keywords:
                if any(kw in t or kw in h for t, h in zip(draft_titles, draft_headings)):
                    found = True
                    break
            if not found:
                issues.append(Issue(
                    level=sec_def.get("level", "major"),
                    category="completeness",
                    section="-",
                    title=f"缺少章节「{sec_def['name']}」",
                    description=f"初稿中未找到「{sec_def['name']}」章节。{sec_def.get('description', '')}",
                    reference="GB/T 1.1-2020",
                    suggestion=f"建议按照 GB/T 1.1-2020 规范补充「{sec_def['name']}」章节"
                ))

        return issues

    def _check_against_reference(self, draft: ParsedDocument, reference: ParsedDocument) -> List[Issue]:
        """对比参考标准检查缺失章节"""
        issues = []
        # 获取参考标准的章节标题集合
        ref_sections = {s.number: s for s in reference.sections}
        draft_sections = {s.number: s for s in draft.sections}

        # 按标题关键词匹配（因为不同标准的编号可能不同）
        ref_titles = {s.title.strip() for s in reference.sections}

        # 找出参考标准有但初稿没有的章节
        missing = []
        for num, sec in ref_sections.items():
            if num in ("cover", "preface", "appendix", ""):
                continue
            # 检查是否有相似标题
            found = False
            for d_num, d_sec in draft_sections.items():
                # 标题相似度：简单包含检查
                if sec.title and d_sec.title and (
                    sec.title in d_sec.title or d_sec.title in sec.title
                    or self._title_similarity(sec.title, d_sec.title) > 0.7
                ):
                    found = True
                    break
            if not found and sec.title and sec.level <= 2:
                missing.append(sec)

        if missing:
            # 分组报告，避免过多条目
            names = [f"「{s.raw_heading}」" for s in missing[:10]]
            issues.append(Issue(
                level="major",
                category="completeness",
                section="-",
                title=f"参考标准中存在但初稿中未找到的章节（{len(missing)}个）",
                description=f"对比参考标准《{reference.title}》，初稿中可能缺少以下章节：{', '.join(names)}"
                    + (f"等共{len(missing)}个章节" if len(missing) > 10 else ""),
                reference=reference.title,
                suggestion="请对照参考标准的章节结构，补充初稿中缺失的章节内容"
            ))

        return issues

    @staticmethod
    def _title_similarity(a: str, b: str) -> float:
        """简单的标题相似度计算（基于字符重叠）"""
        if not a or not b:
            return 0.0
        a_set = set(a)
        b_set = set(b)
        if not a_set or not b_set:
            return 0.0
        return len(a_set & b_set) / len(a_set | b_set)

