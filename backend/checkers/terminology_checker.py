import re
import os
import yaml
from typing import Optional, List, Set
from .base import BaseChecker, CheckResult, Issue
from parsers.base import ParsedDocument


class TerminologyChecker(BaseChecker):
    """术语一致性检查器 - 对比初稿与参考标准的术语使用
    支持化妆品检验方法内置术语库
    """

    TERM_SECTIONS = ["术语", "定义", "术语和定义", "缩略语"]

    # 操作类术语 categories：这些术语的 aliases 描述的是相关但不同的具体操作，
    # 而不是可互换的同义词，因此不进行"多种写法"检查
    _OPERATION_CATEGORIES = {
        "分离操作", "浓缩操作", "净化操作", "配制操作", "前处理操作",
        "称量操作", "移液操作", "混合操作", "提取操作"
    }

    def __init__(self):
        """初始化，加载内置术语库"""
        self._builtin_terms = self._load_builtin_terms()

    def _load_builtin_terms(self) -> dict:
        """加载内置化妆品术语库"""
        terms = {}
        try:
            terms_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "cosmetic_terms.yaml"
            )
            if os.path.exists(terms_path):
                with open(terms_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    # 将所有类别的术语收集到一个字典
                    for category, items in data.items():
                        if isinstance(items, list):
                            for item in items:
                                term_name = item.get("term", "")
                                aliases = item.get("aliases", [])
                                if term_name:
                                    terms[term_name] = {
                                        "aliases": aliases,
                                        "category": item.get("category", category)
                                    }
        except Exception:
            pass
        return terms

    def check(self, draft: ParsedDocument, reference: Optional[ParsedDocument] = None) -> CheckResult:
        result = CheckResult(category="terminology", checker_name="术语一致性检查")

        # 检查文档类型
        doc_type = draft.metadata.get("doc_type", "general_standard")

        if doc_type == "inspection_method":
            # 检验方法文档：使用内置术语库 + 参考标准对比
            result.issues.extend(self._check_builtin_terms_usage(draft))

        # 通用检查
        result.issues.extend(self._check_term_definitions(draft))
        if reference and reference.terms:
            result.issues.extend(self._check_terminology_consistency(draft, reference))
            result.issues.extend(self._check_term_usage(draft, reference))

        return result

    def _check_builtin_terms_usage(self, draft: ParsedDocument) -> List[Issue]:
        """检查文档中对内置术语的使用情况

        只有仪器设备、试剂耗材等真正的同义词才进行"多种写法"检查。
        操作类术语（如过滤、定容、精密移取等）的 aliases 描述的是相关但不同的
        具体操作方法，不是可互换的同义词，因此跳过此类检查。
        """
        issues = []
        full_text = draft.full_text

        if not self._builtin_terms:
            return issues

        import re
        checked_aliases = set()
        for term_name, term_info in self._builtin_terms.items():
            aliases = term_info.get("aliases", [])
            if not aliases or term_name in checked_aliases:
                continue

            category = term_info.get("category", "")

            # 操作类术语：aliases 描述的是不同具体操作，不做"多种写法"检查
            if category in self._OPERATION_CATEGORIES:
                checked_aliases.update([term_name] + aliases)
                continue

            found_variants = []
            # 主术语检查：同样需要边界验证，避免把 alias 内部的 substring 当成独立出现
            # 例如"比色管"在"具塞比色管"中不能算独立出现
            before_ok_main = re.search(r'(?<![\u4e00-\u9fff])' + re.escape(term_name), full_text)
            if term_name in full_text and before_ok_main:
                found_variants.append(term_name)

            for alias in aliases:
                if alias not in full_text or alias in found_variants:
                    continue

                # 排除 alias 作为其他注册术语子串的情况
                is_substring_of_other = any(
                    alias in other_term and alias != other_term
                    for other_term in self._builtin_terms.keys()
                )
                if is_substring_of_other:
                    continue

                # 独立出现判断：alias 前面必须是 CJK 范围之外或字符串边界
                # alias 后面必须是 CJK 范围之外
                # 但如果 alias 后面紧跟的是测量单位符号（µ/μ/m 等）+ 拉丁字符（m/L/g等），
                # 说明 alias 是某个完整操作名称（如"0.22 µm滤膜过滤"）的子串，不算独立出现
                before_ok = re.search(r'(?<![\u4e00-\u9fff])' + re.escape(alias), full_text)
                if not before_ok:
                    continue

                # 检查后面是否紧跟测量单位
                # 例如"滤膜过滤"在"0.22 µm滤膜过滤"中，后面跟的是"µm"单位
                unit_suffix = re.search(
                    re.escape(alias) + r'(?:\s*)([µμ]?m[lLg]|[µμ]?g/m[lL]|[µμ]?L|[cm]?m|kPa|MPa|eV|r/min)',
                    full_text
                )
                if unit_suffix:
                    # alias 后面跟了测量单位，说明是某完整操作名称的一部分，跳过
                    continue

                found_variants.append(alias)

            if len(found_variants) > 1:
                main_term = found_variants[0]
                variant_list = found_variants[1:]
                if len(variant_list) >= 1:
                    meaningful_variants = [v for v in variant_list if len(v) >= 2]
                    if meaningful_variants:
                        issues.append(Issue(
                            level="suggestion",
                            category="terminology",
                            section="-",
                            title=f"术语「{main_term}」存在多种写法",
                            description=f"文档中同时使用了「{main_term}」和「{'、'.join(meaningful_variants[:3])}」等多种写法",
                            reference="术语一致性规范",
                            suggestion=f"建议统一使用「{main_term}」，保持术语一致性"
                        ))

            checked_aliases.update([term_name] + aliases)

        return issues

    def _check_term_definitions(self, draft: ParsedDocument) -> List[Issue]:
        """检查初稿自身的术语定义质量"""
        issues = []
        if not draft.terms:
            # 检查是否有术语章节但没有提取到术语
            has_term_section = any(
                any(kw in s.title or kw in s.raw_heading for kw in self.TERM_SECTIONS)
                for s in draft.sections
            )
            if has_term_section:
                issues.append(Issue(
                    level="major",
                    category="terminology",
                    section="-",
                    title="术语章节未提取到有效术语条目",
                    description="初稿中包含术语章节，但未能识别出有效的术语定义条目。可能格式不符合规范。",
                    reference="GB/T 1.1-2020 第8章",
                    suggestion="请确保术语条目按照「编号 术语名\\n定义」的格式编写"
                ))
            else:
                issues.append(Issue(
                    level="minor",
                    category="terminology",
                    section="-",
                    title="未发现术语和定义章节",
                    description="初稿中没有「术语和定义」章节。如果标准中使用了专业术语或缩略语，建议添加该章节。",
                    reference="GB/T 1.1-2020 第8章",
                    suggestion="如果标准涉及专业术语，建议参照 GB/T 1.1-2020 第8章添加「术语和定义」章节"
                ))
            return issues

        # 检查每个术语是否有定义
        undefined = [t for t in draft.terms if not t.definition.strip()]
        if undefined:
            names = [t.term for t in undefined[:5]]
            issues.append(Issue(
                level="critical",
                category="terminology",
                section="术语和定义",
                title="部分术语缺少定义",
                description=f"以下术语条目缺少定义说明：{', '.join(names)}"
                    + (f"等共{len(undefined)}个" if len(undefined) > 5 else ""),
                reference="GB/T 1.1-2020 第8.2条",
                suggestion="请为所有术语条目添加明确的定义说明"
            ))

        # 检查术语编号格式
        for t in draft.terms:
            if t.section and not re.match(r'^3\.\d+$', t.section):
                issues.append(Issue(
                    level="minor",
                    category="terminology",
                    section=t.section,
                    title="术语编号格式建议",
                    description=f"术语「{t.term}」位于第{t.section}节，按惯例术语应从第3章开始编号（如3.1、3.2）",
                    reference="GB/T 1.1-2020 第8.1条",
                    suggestion="建议将术语和定义章节设为第3章，术语编号从3.1开始"
                ))
                break  # 只报告一次

        return issues

    def _check_terminology_consistency(self, draft: ParsedDocument, reference: ParsedDocument) -> List[Issue]:
        """对比初稿与参考标准的术语差异"""
        issues = []
        ref_term_names = {t.term for t in reference.terms}
        draft_term_names = {t.term for t in draft.terms}

        # 参考标准有但初稿没有的术语
        ref_only = ref_term_names - draft_term_names
        if ref_only:
            names = list(ref_only)[:8]
            issues.append(Issue(
                level="major",
                category="terminology",
                section="术语和定义",
                title=f"参考标准中的术语在初稿中未出现（{len(ref_only)}个）",
                description=f"参考标准《{reference.title}》中定义了以下术语，但初稿的术语章节中未包含：{', '.join(names)}"
                    + (f"等共{len(ref_only)}个" if len(ref_only) > 8 else ""),
                reference=reference.title,
                suggestion="请检查是否需要在初稿中定义这些术语，或确认这些术语与初稿无关"
            ))

        # 初稿有但参考标准没有的术语
        draft_only = draft_term_names - ref_term_names
        if draft_only:
            names = list(draft_only)[:8]
            issues.append(Issue(
                level="minor",
                category="terminology",
                section="术语和定义",
                title=f"初稿中存在参考标准未定义的术语（{len(draft_only)}个）",
                description=f"初稿定义了以下术语，但参考标准中未包含：{', '.join(names)}"
                    + (f"等共{len(draft_only)}个" if len(draft_only) > 8 else ""),
                reference=reference.title,
                suggestion="请确认这些术语是否为初稿新引入的专业概念，如是请确保定义准确"
            ))

        return issues

    def _check_term_usage(self, draft: ParsedDocument, reference: ParsedDocument) -> List[Issue]:
        """检查术语在正文中的使用一致性"""
        issues = []
        for ref_term in reference.terms:
            term = ref_term.term
            if len(term) < 2:
                continue
            # 在初稿正文中搜索该术语
            if term in draft.full_text:
                # 检查是否有近似但不完全相同的变体（如空格、符号差异）
                variants = self._find_term_variants(term, draft.full_text)
                if variants:
                    issues.append(Issue(
                        level="minor",
                        category="terminology",
                        section="-",
                        title=f"术语「{term}」可能存在变体写法",
                        description=f"在初稿中发现了可能与「{term}」相同但写法不同的术语：{', '.join(variants[:3])}",
                        reference=f"参考标准定义：{ref_term.definition[:50]}...",
                        suggestion=f"请统一使用标准术语「{term}」，避免使用不同写法的变体"
                    ))
        return issues

    @staticmethod
    def _find_term_variants(term: str, text: str) -> List[str]:
        """查找术语的可能变体"""
        variants = []
        # 检查术语的去空格版本、全半角差异等
        term_no_space = term.replace(" ", "").replace("　", "")
        if term_no_space != term and term_no_space in text:
            variants.append(f"「{term_no_space}」（无空格）")

        # 检查全角/半角差异
        import unicodedata
        normalized = unicodedata.normalize("NFKC", term)
        if normalized != term and normalized in text:
            variants.append(f"「{normalized}」（标准化后）")

        return variants
