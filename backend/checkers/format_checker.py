import re
import yaml
import os
from typing import Optional, List
from .base import BaseChecker, CheckResult, Issue
from parsers.base import ParsedDocument


class FormatChecker(BaseChecker):
    """格式合规性检查器 - 基于 GB/T 1.1-2020 规则"""

    def __init__(self, rules_path: Optional[str] = None):
        if rules_path is None:
            rules_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "rules", "gbt_1_1_2020.yaml"
            )
        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f)

    def check(self, draft: ParsedDocument, reference: Optional[ParsedDocument] = None) -> CheckResult:
        result = CheckResult(category="format", checker_name="格式合规性检查")
        result.issues.extend(self._check_chapter_order(draft))
        result.issues.extend(self._check_title_format(draft))
        result.issues.extend(self._check_numbering(draft))
        result.issues.extend(self._check_references(draft))
        return result

    def _check_chapter_order(self, draft: ParsedDocument) -> List[Issue]:
        """检查章节顺序和必要章节"""
        issues = []
        chapter_config = self.rules.get("chapter_order", [])
        found_chapters = {s.number: s for s in draft.sections}

        required_missing = []
        for ch in chapter_config:
            if not ch.get("required", False):
                continue
            num = ch.get("number", "")
            keywords = ch.get("keywords", [])
            # 检查编号匹配或关键词匹配
            found = num in found_chapters
            if not found and keywords:
                found = any(
                    any(kw in s.title or kw in s.raw_heading for kw in keywords)
                    for s in draft.sections
                )
            if not found:
                required_missing.append(ch["name"])

        if required_missing:
            issues.append(Issue(
                level="critical",
                category="format",
                section="-",
                title="缺少必要章节",
                description=f"标准初稿缺少以下必要章节：{', '.join(required_missing)}",
                reference="GB/T 1.1-2020",
                suggestion=f"请补充缺失的章节：{', '.join(required_missing)}"
            ))

        # 检查编号连续性
        numbered = [s for s in draft.sections if s.number and s.level == 1 and s.number.isdigit()]
        if numbered:
            nums = sorted(int(s.number) for s in numbered)
            for i in range(len(nums) - 1):
                if nums[i + 1] - nums[i] > 1:
                    issues.append(Issue(
                        level="critical",
                        category="format",
                        section=str(nums[i]),
                        title="章节编号不连续",
                        description=f"章节编号从 {nums[i]} 跳到 {nums[i+1]}，存在断号",
                        reference="GB/T 1.1-2020 第6章",
                        suggestion="请检查并修正章节编号，确保编号连续"
                    ))

        return issues

    def _check_title_format(self, draft: ParsedDocument) -> List[Issue]:
        """检查标题格式"""
        issues = []
        title_rules = self.rules.get("title_format_rules", [])

        for sec in draft.sections:
            if not sec.title:
                continue
            # 标题末尾标点检查
            forbidden_endings = ["。", "，", "；", "：", ".", ","]
            for rule in title_rules:
                if rule.get("name") == "标题不应包含标点符号":
                    for ch in forbidden_endings:
                        if sec.title.endswith(ch):
                            issues.append(Issue(
                                level=rule.get("level", "major"),
                                category="format",
                                section=sec.number,
                                title="标题末尾包含标点符号",
                                description=f"章节「{sec.raw_heading}」末尾包含不应有的标点「{ch}」",
                                reference=rule.get("check", "GB/T 1.1-2020"),
                                suggestion="标题末尾不应使用标点符号（问号、叹号除外），请删除"
                            ))
                            break

            # 悬置段检查
            if not sec.content.strip():
                issues.append(Issue(
                    level="major",
                    category="format",
                    section=sec.number,
                    title="标题下无正文内容（悬置段）",
                    description=f"章节「{sec.raw_heading}」下没有正文内容",
                    reference="GB/T 1.1-2020 第6.2.1条",
                    suggestion="请在标题下方添加正文内容，或将该标题合并到其他章节"
                ))

        return issues

    def _check_numbering(self, draft: ParsedDocument) -> List[Issue]:
        """检查编号格式"""
        issues = []
        num_rules = self.rules.get("numbering_rules", [])

        for sec in draft.sections:
            if not sec.number:
                continue
            for rule in num_rules:
                if rule.get("level") == sec.level and rule.get("pattern"):
                    if not re.match(rule["pattern"], sec.number):
                        issues.append(Issue(
                            level="major",
                            category="format",
                            section=sec.number,
                            title=f"{rule.get('name', '编号格式错误')}",
                            description=f"章节「{sec.raw_heading}」的编号格式不符合规范。规则：{rule.get('check', '')}",
                            reference="GB/T 1.1-2020 第6章",
                            suggestion=f"请按标准格式修正编号"
                        ))

        return issues

    def _check_references(self, draft: ParsedDocument) -> List[Issue]:
        """检查引用格式"""
        issues = []
        ref_rules = self.rules.get("reference_rules", [])
        full_text = draft.full_text

        # 查找文本中的标准号引用
        # 匹配 GB/T 1.1-2020, GB 3100-1993 等格式
        std_pattern = r'([A-Z]{1,3}/T?\s*\d+\.?\d*\s*-\s*\d{4})'
        found_refs = re.findall(std_pattern, full_text)

        if found_refs:
            # 检查格式是否规范（标准号各部分间应有空格）
            for ref in set(found_refs):
                # 检查 GB/T 之间和数字与年份之间是否有适当分隔
                if not re.search(r'[A-Z]{1,3}/T?\s+\d', ref):
                    issues.append(Issue(
                        level="minor",
                        category="format",
                        section="-",
                        title="标准号格式不规范",
                        description=f"引用的标准号「{ref}」格式不规范，字母与数字之间应有空格",
                        reference="GB/T 1.1-2020",
                        suggestion=f"请修正为规范格式，如「{ref}」"
                    ))

        return issues
