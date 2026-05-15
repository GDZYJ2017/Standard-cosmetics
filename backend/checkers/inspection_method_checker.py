import re
import os
import yaml
from typing import Optional, List, Dict, Any
from .base import BaseChecker, CheckResult, Issue
from parsers.base import ParsedDocument


class InspectionMethodChecker(BaseChecker):
    """化妆品/牙膏检验方法专项检查器

    检查维度：
    1. 章节结构完整性（必要章节是否存在）
    2. 方法提要要素（检出限/定量下限等）
    3. 试剂和仪器规范（纯度标注、仪器条件）
    4. 数据参数检查（回收率、精密度、计算公式）
    5. 附录标准品信息表（必备列、格式规范）
    """

    def __init__(self, rules_path: Optional[str] = None):
        if rules_path is None:
            rules_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "rules", "inspection_method.yaml"
            )
        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f)

    def check(self, draft: ParsedDocument, reference: Optional[ParsedDocument] = None) -> CheckResult:
        """执行检验方法专项检查"""
        result = CheckResult(category="inspection_method", checker_name="检验方法专项检查")
        result.issues.extend(self._check_required_sections(draft))
        result.issues.extend(self._check_method_summary(draft))
        result.issues.extend(self._check_reagent_instrument(draft))
        result.issues.extend(self._check_data_parameters(draft))
        result.issues.extend(self._check_appendix_tables(draft))
        result.issues.extend(self._check_language_norms(draft))
        result.issues.extend(self._check_appendix_type_annotations(draft))
        result.issues.extend(self._check_scope_three_elements(draft))
        result.issues.extend(self._check_section_numbering_structure(draft))
        result.issues.extend(self._check_qualitative_ion_abundance_table(draft))
        result.issues.extend(self._check_matrix_classification_consistency(draft))
        result.issues.extend(self._check_appendix_ab_consistency(draft))
        result.issues.extend(self._check_cross_references(draft))
        result.issues.extend(self._check_number_format_norms(draft))
        result.issues.extend(self._check_instrument_conditions(draft))
        return result

    # ================================================================
    # 维度一：章节结构完整性
    # ================================================================
    def _check_required_sections(self, draft: ParsedDocument) -> List[Issue]:
        """检查必要章节是否齐全"""
        issues = []
        required = self.rules.get("required_sections", [])
        all_titles = " ".join(s.title + " " + s.raw_heading for s in draft.sections)
        all_content = draft.full_text

        for sec_def in required:
            keywords = sec_def.get("keywords", [])
            found = False
            for kw in keywords:
                if kw in all_titles:
                    found = True
                    break

            if not found:
                # 检查内容中是否有间接提及（更宽松）
                for kw in keywords:
                    if kw in all_content:
                        found = True
                        break

            if not found:
                issues.append(Issue(
                    level=sec_def.get("level", "critical"),
                    category="inspection_method",
                    section="-",
                    title=f"缺少必要章节「{sec_def['name']}」",
                    description=f"检验方法文档中未找到「{sec_def['name']}」章节。"
                                f"{sec_def.get('description', '')}",
                    reference="国家药监局检验方法文档规范",
                    suggestion=f"建议补充「{sec_def['name']}」章节，"
                               f"内容应包括：{sec_def.get('description', '')}"
                ))

        # 检查分析步骤的必要子章节
        analysis_step_keywords = ["分析步骤", "操作步骤", "测定步骤"]
        has_analysis_step = any(kw in all_titles for kw in analysis_step_keywords)

        if has_analysis_step:
            required_subs = []
            for sec_def in required:
                if sec_def.get("name") == "分析步骤":
                    required_subs = sec_def.get("required_subsections", [])
                    break

            for sub_def in required_subs:
                sub_found = any(
                    kw in all_content
                    for kw in sub_def.get("keywords", [])
                )
                if not sub_found:
                    issues.append(Issue(
                        level=sub_def.get("level", "major"),
                        category="inspection_method",
                        section="5",
                        title=f"分析步骤缺少「{sub_def['name']}」部分",
                        description=f"第5章分析步骤中未找到「{sub_def['name']}」相关内容",
                        reference="国家药监局检验方法文档规范",
                        suggestion=f"建议在分析步骤中补充「{sub_def['name']}」的详细描述"
                    ))

        # 检查章节编号连续性
        numbered = [
            s for s in draft.sections
            if s.number and s.level == 1 and s.number.isdigit()
        ]
        if len(numbered) >= 2:
            nums = sorted(int(s.number) for s in numbered)
            for i in range(len(nums) - 1):
                if nums[i + 1] - nums[i] > 1:
                    issues.append(Issue(
                        level="critical",
                        category="inspection_method",
                        section=str(nums[i]),
                        title="章节编号不连续",
                        description=f"章节编号从 {nums[i]} 跳到 {nums[i+1]}，存在断号",
                        reference="检验方法文档编写规范",
                        suggestion="请检查并修正章节编号，确保编号连续"
                    ))

        return issues

    # ================================================================
    # 维度二：方法提要要素检查
    # ================================================================
    def _check_method_summary(self, draft: ParsedDocument) -> List[Issue]:
        """检查方法提要章节是否包含关键要素"""
        issues = []
        required = self.rules.get("required_sections", [])

        # 找到方法提要章节
        summary_section = None
        summary_keywords = ["方法提要", "方法原理", "原理"]
        for sec in draft.sections:
            for kw in summary_keywords:
                if kw in sec.title or kw in sec.raw_heading:
                    summary_section = sec
                    break
            if summary_section:
                break

        if not summary_section:
            # 已在必要章节检查中报告
            return issues

        content = summary_section.content

        # 检查方法提要的必要要素
        for sec_def in required:
            if sec_def.get("name") == "方法提要":
                elements = sec_def.get("required_elements", [])
                for elem in elements:
                    elem_keywords = elem.get("keywords", [])
                    found = any(kw in content for kw in elem_keywords)
                    if not found:
                        issues.append(Issue(
                            level=elem.get("level", "critical"),
                            category="inspection_method",
                            section=summary_section.number or "2",
                            title=f"方法提要缺少「{elem['name']}」",
                            description=f"方法提要章节中未提及「{elem['name']}」。"
                                       f"（搜索关键词：{', '.join(elem_keywords)}）",
                            reference="检验方法文档编写规范",
                            suggestion=f"建议在方法提要中补充「{elem['name']}」的相关数据"
                        ))
        return issues

    # ================================================================
    # 维度三：试剂和仪器规范检查
    # ================================================================
    def _check_reagent_instrument(self, draft: ParsedDocument) -> List[Issue]:
        """检查试剂纯度标注、仪器条件完整性"""
        issues = []
        language_rules = self.rules.get("language_rules", [])

        # 找到试剂和材料章节
        reagent_section = None
        reagent_keywords = ["试剂和材料", "试剂、材料", "试剂材料"]
        for sec in draft.sections:
            for kw in reagent_keywords:
                if kw in sec.title or kw in sec.raw_heading:
                    reagent_section = sec
                    break
            if reagent_section:
                break

        if reagent_section:
            content = reagent_section.content

            # 检查有机溶剂纯度标注
            organic_solvents = [
                "乙腈", "甲醇", "甲酸", "乙酸", "正己烷", "二氯甲烷",
                "四氢呋喃", "异丙醇", "丙酮", "乙醇"
            ]
            unpurified = []
            for solvent in organic_solvents:
                # 找到溶剂出现但未标注纯度的情况
                if solvent in content:
                    # 检查该行是否包含纯度标注
                    lines_with_solvent = [
                        line for line in content.split("\n")
                        if solvent in line
                    ]
                    has_purity = any(
                        "色谱纯" in line or "分析纯" in line or "优级纯" in line
                        for line in lines_with_solvent
                    )
                    if not has_purity:
                        unpurified.append(solvent)

            if unpurified:
                issues.append(Issue(
                    level="major",
                    category="inspection_method",
                    section=reagent_section.number or "3",
                    title="部分有机溶剂未标注纯度等级",
                    description=f"以下有机溶剂在试剂章节中出现但未标注纯度等级（色谱纯/分析纯/优级纯）："
                                f"{', '.join(unpurified)}",
                    reference="检验方法编写规范",
                    suggestion="有机溶剂应标注纯度等级，如「乙腈（色谱纯）」"
                ))

            # 检查标准品引用格式
            has_appendix_ref = "详见附录" in content or "见附录" in content
            has_standard = "标准品" in content or "对照品" in content or "标准物质" in content
            if has_standard and not has_appendix_ref:
                issues.append(Issue(
                    level="major",
                    category="inspection_method",
                    section=reagent_section.number or "3",
                    title="标准品信息未引用附录",
                    description="试剂章节中提及标准品/对照品，但未引用附录中的标准品详细信息表",
                    reference="检验方法文档规范",
                    suggestion="建议在标准品描述后添加「详见附录A」的引用"
                ))

        # 检查仪器条件（在分析步骤中）
        instrument_keywords = ["仪器参考条件", "仪器条件", "色谱条件", "质谱条件"]
        for sec in draft.sections:
            for kw in instrument_keywords:
                if kw in sec.title or kw in sec.raw_heading:
                    # 仪器条件子章节存在即可
                    break

        return issues

    # ================================================================
    # 维度四：数据参数检查
    # ================================================================
    def _check_data_parameters(self, draft: ParsedDocument) -> List[Issue]:
        """检查计算章节中的回收率、精密度等数据参数"""
        issues = []
        required = self.rules.get("required_sections", [])

        # 找到计算/结果表述章节（包括子章节）
        calc_section = None
        calc_keywords = ["计算", "分析结果的表述", "结果计算", "结果表述"]
        calc_full_content = ""
        calc_number = "6"

        for sec in draft.sections:
            for kw in calc_keywords:
                if kw in sec.title or kw in sec.raw_heading:
                    if calc_section is None:
                        calc_section = sec
                        calc_number = sec.number or "6"
                    calc_full_content += sec.content + "\n"
                    # 也收集子章节内容
                    sub_sections = [
                        s for s in draft.sections
                        if s.number and s.number.startswith(calc_number + ".")
                    ]
                    for sub in sub_sections:
                        calc_full_content += sub.content + "\n"
                    break

        if not calc_section:
            # 已在必要章节检查中报告
            return issues

        # 使用包含子章节的完整内容
        content = calc_full_content

        # 获取计算章节的必要要素
        for sec_def in required:
            if sec_def.get("name") in ["计算"]:
                elements = sec_def.get("required_elements", [])
                for elem in elements:
                    elem_keywords = elem.get("keywords", [])
                    found = any(kw in content for kw in elem_keywords)
                    if not found:
                        issues.append(Issue(
                            level=elem.get("level", "major"),
                            category="inspection_method",
                            section=calc_section.number or "6",
                            title=f"计算章节缺少「{elem['name']}」数据",
                            description=f"计算/结果表述章节中未提及「{elem['name']}」",
                            reference="检验方法文档规范",
                            suggestion=f"建议在计算章节中补充「{elem['name']}」的相关数据和表述"
                        ))

        # 检查计算公式是否存在（增强：支持多种公式形式）
        # 形式1: 等号/不等于号  形式2: "公式"关键词  形式3: 分数下标  形式4: 数学运算符
        has_formula = (
            bool(re.search(r'[=＝]', content))
            or "公式" in content
            or bool(re.search(r'[÷×±∑]', content))
            or bool(re.search(r'[mMcCwW]\s*[₀₁₂₃₄₅₆₇₈₉₀]/', content))
        )
        if not has_formula:
            issues.append(Issue(
                level="critical",
                category="inspection_method",
                section=calc_section.number or "6",
                title="计算章节缺少计算公式",
                description="计算章节中未发现定量计算公式。检验方法必须包含明确的计算公式（如质量分数 w = m₁/m₂×100）。",
                reference="化妆品检验方法标准文本规范 第6章",
                suggestion="在计算章节中补充定量计算公式，例如：w = m₁/m₂×100（式中：w——质量分数，%；m₁——目标物质量，g；m₂——样品取样量，g）"
            ))

        return issues

    # ================================================================
    # 维度五：附录标准品信息表检查
    # ================================================================
    def _check_appendix_tables(self, draft: ParsedDocument) -> List[Issue]:
        """检查附录A标准品信息表是否规范"""
        issues = []
        appendix_rules = self.rules.get("appendix_table_rules", [])

        # 从 metadata 中获取附录数据
        appendix_data = draft.metadata.get("appendix_data", {})
        tables = draft.metadata.get("tables", [])

        if not appendix_data.get("has_appendix_a") and not tables:
            # 没有找到附录表格，检查是否有附录章节
            has_appendix = any(
                "附录" in (s.title + s.raw_heading)
                for s in draft.sections
            )
            if has_appendix:
                issues.append(Issue(
                    level="major",
                    category="inspection_method",
                    section="附录",
                    title="附录表格未能正确解析",
                    description="文档中包含附录章节，但未能提取到标准品信息表格。"
                                "请确认附录中包含规范的表格格式。",
                    reference="检验方法文档规范",
                    suggestion="附录A应包含标准品信息表，列名包括：序号、中文名称、英文名称、CAS号、分子式、纯度"
                ))
            return issues

        # 检查标准品表格的列
        if appendix_data.get("standard_compound_tables"):
            for table_info in appendix_data["standard_compound_tables"]:
                header = table_info.get("header", [])
                rule = appendix_rules[0] if appendix_rules else {}
                required_cols = rule.get("required_columns", [])

                missing_cols = []
                for col in required_cols:
                    # 去除空格后匹配，兼容 "CAS 号" 和 "CAS号" 等差异
                    col_normalized = col.replace(" ", "").replace("　", "")
                    if not any(
                        col in h or col_normalized in h.replace(" ", "").replace("　", "")
                        for h in header
                    ):
                        missing_cols.append(col)

                if missing_cols:
                    issues.append(Issue(
                        level=rule.get("level", "major"),
                        category="inspection_method",
                        section="附录A",
                        title="标准品信息表缺少必备列",
                        description=f"附录A标准品信息表中缺少以下必备列：{', '.join(missing_cols)}。"
                                    f"当前表头：{', '.join(header)}",
                        reference="检验方法文档规范",
                        suggestion=f"建议在标准品信息表中添加列：{', '.join(missing_cols)}"
                    ))

                # 检查表格数据行数
                row_count = table_info.get("row_count", 0)
                if row_count <= 1:  # 只有表头没有数据
                    issues.append(Issue(
                        level="critical",
                        category="inspection_method",
                        section="附录A",
                        title="标准品信息表无数据行",
                        description="附录A中的标准品信息表仅有表头，没有数据行",
                        reference="检验方法文档规范",
                        suggestion="请在标准品信息表中填写各标准品的详细信息"
                    ))

        # 检查是否有图谱章节
        has_figure_section = any(
            "图谱" in s.title or "色谱图" in s.title
            for s in draft.sections
        )
        if not has_figure_section:
            issues.append(Issue(
                level="minor",
                category="inspection_method",
                section="-",
                title="未发现图谱章节",
                description="检验方法文档通常应包含代表性图谱（如总离子流色谱图、MRM色谱图等）",
                reference="检验方法文档规范",
                suggestion="建议添加「图谱」章节，包含代表性色谱图/质谱图"
            ))

        return issues

    # ================================================================
    # 维度六：语言规范检查
    # ================================================================
    def _check_language_norms(self, draft: ParsedDocument) -> List[Issue]:
        """检查检验方法文档特有的语言规范"""
        issues = []
        content = draft.full_text

        # 检查离心条件完整性：有"离心"但缺少完整条件
        centrifuge_count = content.count("离心")
        if centrifuge_count > 0:
            # 检查是否有关联的转速和时间
            # 找到"离心"附近的文字，检查是否包含 r/min 和 min
            lines_with_centrifuge = [
                line for line in content.split("\n") if "离心" in line
            ]
            incomplete_centrifuge = 0
            for line in lines_with_centrifuge:
                has_speed = "r/min" in line or "rpm" in line or "转" in line
                has_time = "min" in line or "分钟" in line
                if not (has_speed and has_time):
                    incomplete_centrifuge += 1

            if incomplete_centrifuge > 0 and incomplete_centrifuge == len(lines_with_centrifuge):
                issues.append(Issue(
                    level="minor",
                    category="inspection_method",
                    section="-",
                    title="离心操作条件不完整",
                    description=f"文档中提及「离心」操作({centrifuge_count}处)，但未标注完整的离心条件（转速 r/min + 时间 min）",
                    reference="检验方法编写规范",
                    suggestion="离心操作应标注转速和时间，如「以10000 r/min离心10 min」"
                ))

        # 检查过滤操作是否标注滤膜孔径，且单位是否正确（μm vs um）
        filter_count = content.count("过滤") + content.count("滤膜")
        if filter_count > 0:
            # 检测 um 而非 μm（ASCII um 是常见错误写法）
            wrong_um = re.search(r'\b\d+(\.\d+)?\s*um\b', content, re.IGNORECASE)
            if wrong_um:
                issues.append(Issue(
                    level="major",
                    category="inspection_method",
                    section="-",
                    title="滤膜孔径单位错误：um 应为 μm",
                    description=f"检测到错误的单位写法「{wrong_um.group()}」，应使用希腊字母μ（μm）而非ASCII字母um",
                    reference="化妆品检验方法标准文本规范",
                    suggestion=f"将「{wrong_um.group()}」改为「{wrong_um.group().replace('um', 'μm').replace('Um', 'μm').replace('UM', 'μm')}」"
                ))
            else:
                has_pore_size = "0.22" in content or "0.45" in content or "µm" in content or "μm" in content
                if not has_pore_size:
                    issues.append(Issue(
                        level="minor",
                        category="inspection_method",
                        section="-",
                        title="过滤操作未标注滤膜孔径",
                        description=f"文档中提及过滤操作({filter_count}处)，但未标注滤膜孔径",
                        reference="检验方法编写规范",
                        suggestion="过滤操作应标注滤膜孔径，如「0.22μm微孔滤膜」"
                    ))

        # 检查范围章节的标准表述
        has_scope = any(
            "范围" in s.title for s in draft.sections
        )
        if has_scope:
            scope_section = next(
                (s for s in draft.sections if "范围" in s.title), None
            )
            if scope_section:
                scope_content = scope_section.content
                if "本方法规定了" not in scope_content:
                    issues.append(Issue(
                        level="minor",
                        category="inspection_method",
                        section=scope_section.number or "1",
                        title="范围章节缺少标准表述",
                        description="范围章节中未发现「本方法规定了...」的标准表述",
                        reference="检验方法文档规范",
                        suggestion="范围章节应使用「本方法规定了...」的固定表述格式"
                    ))
                if "本方法适用于" not in scope_content:
                    issues.append(Issue(
                        level="minor",
                        category="inspection_method",
                        section=scope_section.number or "1",
                        title="范围章节缺少适用范围表述",
                        description="范围章节中未发现「本方法适用于...」的标准表述",
                        reference="检验方法文档规范",
                        suggestion="范围章节应包含「本方法适用于...」的适用范围说明"
                    ))

        return issues

    # ================================================================
    # 章节编号层级结构预检（高优先级，在规则匹配之前执行）
    # 检查 5.4~5.6 章节的层级是否与规范一致
    # 规范规定：5.4仪器参考条件（含5.4.1色谱+5.4.2质谱），
    #          5.5定性判定（独立章节），5.6定量测定（独立章节）
    # 若起草者把5.5/5.6内容错误编为5.4.3/5.4.4，应检出
    # ================================================================
    def _check_section_numbering_structure(self, draft: ParsedDocument) -> List[Issue]:
        issues = []
        issues_by_num = {}
        for s in draft.sections:
            if s.number:
                issues_by_num[s.number] = s

        # 情况A：存在 5.4.3 或 5.4.4 的章节标题是"定性判定"或"定量测定"
        # 说明起草者把5.5/5.6错误地编为5.4的子节
        for s in draft.sections:
            if s.number in ("5.4.3", "5.4.4") and s.title:
                title = s.title.strip()
                if "定性判定" in title:
                    issues.append(Issue(
                        level="major",
                        category="inspection_method",
                        section="5.4.3",
                        title="「定性判定」章节编号错误：应为5.5，而非5.4.3",
                        description="「定性判定」是与「仪器参考条件」并列的独立章节，应编号为5.5，不应作为5.4的子节。规范规定章节顺序为：5.4仪器参考条件 → 5.5定性判定 → 5.6定量测定。",
                        reference="化妆品检验方法标准文本规范 第5章结构",
                        suggestion="将章节编号从「5.4.3 定性判定」更正为「5.5 定性判定」，作为第5章的独立主要章节"
                    ))
                elif "定量测定" in title:
                    issues.append(Issue(
                        level="major",
                        category="inspection_method",
                        section="5.4.4",
                        title="「定量测定」章节编号错误：应为5.6，而非5.4.4",
                        description="「定量测定」是与「仪器参考条件」并列的独立章节，应编号为5.6，不应作为5.4的子节。规范规定章节顺序为：5.4仪器参考条件 → 5.5定性判定 → 5.6定量测定。",
                        reference="化妆品检验方法标准文本规范 第5章结构",
                        suggestion="将章节编号从「5.4.4 定量测定」更正为「5.6 定量测定」，作为第5章的独立主要章节"
                    ))

        # 情况B：5.4存在且包含"质谱条件"子节（5.4.2），检查5.5/5.6是否缺失
        has_54 = "5.4" in issues_by_num
        has_542 = "5.4.2" in issues_by_num
        has_55 = "5.5" in issues_by_num
        has_56 = "5.6" in issues_by_num
        has_quality = any("定性判定" in (s.title or "") for s in draft.sections)
        has_quant = any("定量测定" in (s.title or "") for s in draft.sections)

        if has_54 and has_542 and not has_55 and has_quality:
            # 5.5缺失，但"定性判定"内容存在（被编为5.4.3了）
            pass  # 已在情况A处理
        if has_54 and has_542 and not has_56 and has_quant:
            # 5.6缺失，但"定量测定"内容存在（被编为5.4.4了）
            pass  # 已在情况A处理

        return issues

    # ================================================================
    # 维度七：附录类型标注检查
    # ================================================================
    def _check_appendix_type_annotations(self, draft: ParsedDocument) -> List[Issue]:
        issues = []
        appendix_sections = [
            s for s in draft.sections
            if s.title and "附录" in s.title and re.search(r"附录[A-Z]", s.title)
        ]
        for sec in appendix_sections:
            title = sec.title
            if "附录A" in title and "资料性" not in title and "规范性" not in title:
                issues.append(Issue(level="major", category="inspection_method", section=sec.number or "-",
                    title="附录A缺少类型标注",
                    description="附录A（标准品信息表）必须标注为「资料性附录」",
                    reference="化妆品检验方法标准文本规范 2.9",
                    suggestion="在附录A标题下方添加「（资料性附录）」"))
            elif "附录B" in title and "资料性" not in title and "规范性" not in title:
                issues.append(Issue(level="major", category="inspection_method", section=sec.number or "-",
                    title="附录B缺少类型标注",
                    description="附录B（质谱监测离子对参数）必须标注为「规范性附录」",
                    reference="化妆品检验方法标准文本规范 2.10",
                    suggestion="在附录B标题下方添加「（规范性附录）」"))
            elif "附录C" in title and "资料性" not in title and "规范性" not in title:
                issues.append(Issue(level="major", category="inspection_method", section=sec.number or "-",
                    title="附录C缺少类型标注",
                    description="附录C（补充信息）应标注附录类型（资料性或规范性）",
                    reference="化妆品检验方法标准文本规范 2.11",
                    suggestion="在附录C标题下方添加「（资料性附录）」或「（规范性附录）」标注"))
        return issues

    # ================================================================
    # 维度八：范围章节三要素检查
    # ================================================================
    def _check_scope_three_elements(self, draft: ParsedDocument) -> List[Issue]:
        issues = []
        scope_section = None
        for sec in draft.sections:
            if "范围" in sec.title:
                scope_section = sec
                break
        if not scope_section:
            return issues
        content = scope_section.content
        has_method = "本方法规定了" in content or "本方法规定" in content
        has_matrix = "本方法适用于" in content
        has_target_ref = "附录A" in content
        if not has_method:
            issues.append(Issue(level="critical", category="inspection_method", section=scope_section.number or "1",
                title="范围章节缺少方法规定要素",
                description="范围章节中未发现「本方法规定了...」的方法规定表述",
                reference="化妆品检验方法标准文本规范 2.2",
                suggestion="范围章节第一句应为「本方法规定了[方法名称]测定化妆品中[目标物]的含量」"))
        if not has_matrix:
            issues.append(Issue(level="critical", category="inspection_method", section=scope_section.number or "1",
                title="范围章节缺少适用基质要素",
                description="范围章节中未发现「本方法适用于...」的适用基质表述",
                reference="化妆品检验方法标准文本规范 2.2",
                suggestion="范围章节应包含「本方法适用于[基质列表]化妆品中[目标物]的定性筛查与定量测定」"))
        if not has_target_ref:
            issues.append(Issue(level="major", category="inspection_method", section=scope_section.number or "1",
                title="范围章节缺少目标物指引",
                description="范围章节中未发现对附录A的引用，目标物信息应统一引至附录A",
                reference="化妆品检验方法标准文本规范 2.2",
                suggestion="在范围章节末尾添加「本方法所包含的目标物的中文名称、英文名称、CAS号等信息详见附录A」"))
        return issues

    # ================================================================
    # 维度九：定性判定离子丰度比偏差表检查
    # ================================================================
    def _check_qualitative_ion_abundance_table(self, draft: ParsedDocument) -> List[Issue]:
        issues = []
        qualitative_section = None
        for sec in draft.sections:
            if "定性" in sec.title:
                qualitative_section = sec
                break
        if not qualitative_section:
            return issues
        content = qualitative_section.content
        has_any_deviation = "±20%" in content or "±25%" in content or "±30%" in content or "±50%" in content
        if not has_any_deviation:
            issues.append(Issue(level="critical", category="inspection_method",
                section=qualitative_section.number or "5.5",
                title="定性判定缺少离子丰度比偏差表",
                description="定性判定章节未发现完整的离子丰度比允许偏差表（应为±20%/±25%/±30%/±50%）",
                reference="化妆品检验方法标准文本规范 2.5.5",
                suggestion="在定性判定章节中补充离子丰度比允许偏差表：±20%（K>50%）、±25%（50%≥K>20%）、±30%（20%≥K>10%）、±50%（K≤10%）"))
        return issues

    # ================================================================
    # 维度十：基质分类一致性检查
    # ================================================================
    def _check_matrix_classification_consistency(self, draft: ParsedDocument) -> List[Issue]:
        issues = []
        standard_matrices = ["膏霜乳液", "膏霜乳", "液体水基", "凝胶", "液体油基", "粉剂", "蜡基"]
        scope_section = None
        sample_section = None
        for sec in draft.sections:
            if "范围" in sec.title:
                scope_section = sec
            if "样品处理" in sec.title or "样品制备" in sec.title or "试样处理" in sec.title:
                sample_section = sec
        if not scope_section or not sample_section:
            return issues
        scope_matrices = [m for m in standard_matrices if m in scope_section.content]
        missing_in_sample = [m for m in scope_matrices if m not in sample_section.content]
        if missing_in_sample:
            issues.append(Issue(level="critical", category="inspection_method", section="1/5.3",
                title="基质分类不一致：范围章节与样品处理章节存在差异",
                description=f"范围章节中提到了 [{', '.join(missing_in_sample)}]，但样品处理章节（5.3）中未找到对应处理方法",
                reference="化妆品检验方法标准文本规范 2.2 / 2.6.3",
                suggestion=f"请在5.3样品处理章节中添加 [{', '.join(missing_in_sample)}] 的处理方法，或确认范围章节的基质分类是否准确"))
        return issues

    # ================================================================
    # 维度十一：附录A/B序号一致性检查
    # ================================================================
    def _check_appendix_ab_consistency(self, draft: ParsedDocument) -> List[Issue]:
        issues = []
        import re
        appendix_a = None
        appendix_b = None
        for sec in draft.sections:
            if sec.title and "附录A" in sec.title:
                appendix_a = sec
            if sec.title and "附录B" in sec.title:
                appendix_b = sec
        if not appendix_a or not appendix_b:
            return issues
        a_nums = set(int(m.group(1)) for m in re.finditer(r'^\s*(\d+)\s+[^\d\s]', appendix_a.content, re.MULTILINE))
        b_nums = set(int(m.group(1)) for m in re.finditer(r'^\s*(\d+)\s+[^\d\s]', appendix_b.content, re.MULTILINE))
        if a_nums and b_nums and sorted(a_nums) != sorted(b_nums):
            issues.append(Issue(level="major", category="inspection_method", section="附录A/B",
                title="附录A与附录B序号不一致",
                description=f"附录A序号为 {sorted(a_nums)}，附录B序号为 {sorted(b_nums)}，两者必须一一对应",
                reference="化妆品检验方法标准文本规范 2.9 / 2.10",
                suggestion="请核对附录A和附录B，确保两表中相同序号对应的目标物名称一致"))
        return issues

    # ================================================================
    # 维度十二：交叉引用完整性检查
    # ================================================================
    def _check_cross_references(self, draft: ParsedDocument) -> List[Issue]:
        issues = []
        appendix_sections = {s.title for s in draft.sections if s.title and "附录" in s.title}
        content = draft.full_text
        if "附录A" in content and not any("附录A" in t for t in appendix_sections):
            issues.append(Issue(level="major", category="inspection_method", section="-",
                title="正文引用了附录A，但附录A章节不存在",
                description="正文中有「附录A」引用，但文档中未找到附录A章节",
                reference="化妆品检验方法标准文本规范 3.5",
                suggestion="请确认是否需要添加附录A（标准品信息表），或修改正文中的引用"))
        return issues

    # ================================================================
    # 维度十三：数值范围格式规范检查
    # ================================================================
    def _check_number_format_norms(self, draft: ParsedDocument) -> List[Issue]:
        issues = []
        import re
        content = draft.full_text
        range_with_dash = re.findall(r'(?<![a-zA-Z0-9\-\-])(\d+\.?\d*)\s*-\s*(\d+\.?\d*)(?![a-zA-Z\-\-])', content)
        if range_with_dash:
            examples = ", ".join(f"{v1}-{v2}" for v1, v2 in range_with_dash[:3])
            issues.append(Issue(level="minor", category="inspection_method", section="-",
                title="数值范围使用了短横线而非波浪号",
                description=f"发现数值范围使用短横线连接：[{examples}]，应使用波浪号「~」连接",
                reference="化妆品检验方法标准文本规范 3.4",
                suggestion="将数值范围中的短横线「-」替换为波浪号「~」，如「0.1~0.5 mL」"))
        if "ppm" in content and ("μg/g" in content or "mg/kg" in content):
            issues.append(Issue(level="minor", category="inspection_method", section="-",
                title="单位体系中同时存在ppm与其他单位",
                description="文档中同时使用了「ppm」和「μg/g」或「mg/kg」，应统一使用μg/g或mg/kg",
                reference="化妆品检验方法标准文本规范 3.4",
                suggestion="将所有ppm替换为μg/g或mg/kg（1 mg/kg = 1 μg/g）"))
        return issues

    # ================================================================
    # 维度十四：仪器条件增强检查
    # ================================================================
    def _check_instrument_conditions(self, draft: ParsedDocument) -> List[Issue]:
        issues = []
        import re
        instrument_section = None
        for sec in draft.sections:
            if "仪器" in sec.title:
                instrument_section = sec
                break
        if not instrument_section:
            return issues
        content = instrument_section.content
        if ("分析天平" in content or "天平" in content) and not re.search(r'感量[0-9．,，]+g', content):
            issues.append(Issue(level="major", category="inspection_method", section=instrument_section.number or "4",
                title="分析天平未注明感量",
                description="仪器章节中提到分析天平，但未注明感量（如「感量0.0001 g」）",
                reference="化妆品检验方法标准文本规范 2.5",
                suggestion="在分析天平后添加感量标注，如「分析天平（感量0.0001 g和0.00001 g）」"))
        if "离心机" in content and not re.search(r'\d+\s*r/min|转速可达\d+', content):
            issues.append(Issue(level="major", category="inspection_method", section=instrument_section.number or "4",
                title="离心机未注明转速",
                description="仪器章节中提到离心机，但未注明转速（如「转速可达8000 r/min」）",
                reference="化妆品检验方法标准文本规范 2.5",
                suggestion="在离心机后添加转速标注，如「离心机（转速可达8000 r/min）」"))
        return issues
