import json
import httpx
import asyncio
import logging
from typing import Optional, List
from parsers.base import ParsedDocument, DocumentSection
from checkers.base import Issue

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

logger = logging.getLogger(__name__)

# ============================================================
# 多参考共识合成 Prompt - 化妆品/牙膏检验方法
# ============================================================
INSPECTION_METHOD_CONSENSUS_PROMPT = """你是一位资深的化妆品检验方法审查专家，擅长从多份检验方法标准文档中提炼共性要求。

请仔细阅读以下 N 篇（N={ref_count}）化妆品/牙膏检验方法参考标准，然后输出一份结构化的"共识文档"，代表这些标准之间的共同要求。

【参考标准列表】
{ref_titles}

【各参考标准的完整内容】
{ref_contents}

请以以下 JSON 格式输出（共识提炼结果）：
```json
{{
  "consensus_sections": [
    {{
      "section_theme": "章节主题（如：方法原理、试剂与溶剂、仪器条件、定性判定依据、定量参数、样品前处理、回收率验证、精密度验证、附录等）",
      "common_requirements": [
        "所有参考标准在该主题上的共同要求条款1",
        "共同要求条款2（列出所有参考标准一致同意的技术要求）"
      ],
      "consensus_values": {{
        "mentioned_field": "所有参考都提供的具体数值/参数汇总"
      }},
      "acceptable_variations": [
        "各参考之间存在差异、但均可接受的技术选择（如：不同溶剂品牌、不同色谱柱型号等）"
      ],
      "notes": "备注说明"
    }}
  ],
  "overall_common_elements": {{
    "must_have_parameters": ["所有标准都要求列出的参数（如：检出限、定量下限、线性范围、相关系数、回收率、精密度等）"],
    "reagent_purity_requirements": "所有标准对试剂纯度的共同要求",
    "terminology_common": ["所有标准共同使用的标准术语列表"],
    "calculation_common": "所有标准共同的计算公式/结果表述方式",
    "units_and_ranges": "所有标准共同使用的数值范围和单位规范"
  }},
  "areas_of_disagreement": [
    {{
      "topic": "存在分歧的主题",
      "reference_approaches": {{"标准A": "标准A的方案", "标准B": "标准B的方案"}},
      "assessment": "分歧评估：这些差异是否影响检测结果的准确性和可比性"
    }}
  ],
  "summary": "多标准共识总结（一段话）"
}}
```

**提炼原则**：
1. **共同要求 vs 可接受差异**：严格区分"所有参考一致同意的要求"（必须包含在共识中）与"各参考可接受的差异"（放在 acceptable_variations）
2. **数值收敛**：如果同一参数在不同参考中略有差异（如检出限0.001~0.005mg/kg），取代表性范围而非单一值
3. **章节主题抽象**：重点提炼内容主题（如"基质标准溶液的制备"），而非死扣章节编号
4. **严谨判断**：如果两个参考在某个技术上真的不一致，不要强行捏合，应放入 areas_of_disagreement

请直接输出 JSON，不要有其他内容。"""


# ============================================================
# 多参考共识合成 Prompt - 化妆品标准（检验方法格式）
# ============================================================
GENERAL_CONSENSUS_PROMPT = """你是一位资深的化妆品标准审查专家，擅长从多份化妆品标准文本中提炼共性格式规范和技术要求。

请仔细阅读以下 N 篇（N={ref_count}）化妆品标准参考文档，然后输出一份结构化的"共识文档"。

【参考标准列表】
{ref_titles}

【各参考标准的完整内容】
{ref_contents}

请以 JSON 格式输出：
```json
{{
  "common_structure": {{
    "required_sections": ["所有标准都包含的必要章节"],
    "section_order_pattern": "章节顺序的共同模式",
    "optional_sections": ["部分标准包含的非必要章节"]
  }},
  "format_conventions": {{
    "numbering_style": "章节编号的共同风格",
    "terminology": ["所有标准共同使用的规范术语"],
    "规范性要求": "所有标准共同的规范性表述方式"
  }},
  "technical_common": {{
    "shared_technical_requirements": ["所有标准在技术内容上的共同要求"],
    "shared_parameters": ["所有标准共同引用的参数或指标"]
  }},
  "acceptable_variations": [
    "各参考之间存在差异、但均可接受的技术选择或表述方式"
  ],
  "areas_of_disagreement": [
    {{"topic": "分歧主题", "approaches": {{"标准A": "方案", "标准B": "方案"}}, "assessment": "评估"}}
  ],
  "summary": "共性总结"
}}
```

请直接输出 JSON，不要有其他内容。"""


# 语义分析 Prompt 模板 - 化妆品标准
SEMANTIC_COMPARE_PROMPT = """你是一位资深的化妆品标准审查专家。请对比分析以下两份标准文档对应章节的内容差异。

【参考标准】《{ref_title}》
{ref_section_heading}：
{ref_section_content}

【待审初稿】（对应章节）
{draft_section_heading}：
{draft_section_content}

请从以下维度进行专业审查：
1. **内容差异**：初稿与参考标准在该章节有哪些实质性差异？是否有遗漏、新增或矛盾的内容？
2. **表述质量**：初稿的表述是否准确、规范？是否使用了化妆品标准的术语和格式？
3. **技术合理性**：技术指标和参数是否合理？是否与参考标准保持一致或有所改进？
4. **改进建议**：针对发现的问题，请给出具体的修改建议。

请以 JSON 格式输出审查结果，格式如下：
```json
{{
  "has_issues": true/false,
  "issues": [
    {{
      "level": "critical/major/minor/suggestion",
      "title": "问题标题（简短）",
      "description": "详细问题描述",
      "suggestion": "具体修改建议"
    }}
  ],
  "summary": "该章节整体审查意见总结（一句话）"
}}
```

注意：
- 如果该章节内容与参考标准一致且质量良好，has_issues 设为 false，issues 为空数组
- 如果初稿没有对应章节，请明确指出并给出建议
- **章节编号仅作匹配线索，不代表对应证明**。初稿和参考标准由不同人独立撰写，章节编号不同或同一编号下内容主题不同是完全正常的，不代表任何一方有错误
- **以初稿内容为准，评估其自身质量**，不应因初稿与参考使用了不同试剂、不同仪器型号或不同操作细节就判定为错误
- 只输出 JSON，不要输出其他内容"""

# 语义分析 Prompt 模板 - 化妆品/牙膏检验方法
INSPECTION_METHOD_COMPARE_PROMPT = """你是一位资深的化妆品检验方法审查专家，熟悉国家药监局发布的化妆品/牙膏检验方法规范。请对比分析以下两份检验方法文档对应章节的内容质量。

【参考方法】《{ref_title}》
{ref_section_heading}：
{ref_section_content}

【待审初稿】（对应章节）
{draft_section_heading}：
{draft_section_content}

请从以下检验方法特有维度进行专业审查：
1. **方法原理**：原理描述是否清晰、准确？检测原理与技术路线是否合理？
2. **定量参数**：检出限(LOD)、定量下限(LOQ)、线性范围、相关系数等参数是否完整且合理？
3. **操作步骤完整性**：样品前处理（按基质分类）、标准溶液制备、仪器条件、定性判定、定量测定等步骤是否完整？
4. **试剂与仪器规范**：有机溶剂是否标注纯度（色谱纯/分析纯）？仪器条件参数是否齐全？标准品信息是否引用附录？
5. **计算与验证**：计算公式是否正确？是否包含回收率和精密度数据？
6. **表述规范性**：是否使用"精确至X.XXXXg"、"涡旋混匀"、"0.22μm滤膜过滤"等检验方法标准术语？

请以 JSON 格式输出审查结果，格式如下：
```json
{{
  "has_issues": true/false,
  "issues": [
    {{
      "level": "critical/major/minor/suggestion",
      "title": "问题标题（简短）",
      "description": "详细问题描述",
      "suggestion": "具体修改建议"
    }}
  ],
  "summary": "该章节整体审查意见总结（一句话）"
}}
```

**最关键的审查原则——严格遵守，绝不允许违背**：
1. **两个文档的章节编号体系可能完全不同，绝不能用编号是否相同来判断对应关系**。同一个编号（如5.2）在两篇文档中可能描述完全不同的内容，这是完全正常的，不代表任何一方有误。
2. **拿到这对章节后，第一件事：判断两者是否在同一主题上**。如果参考章节讲"基质标准工作溶液的制备"而初稿章节讲"样品处理"，或两者描述的操作类型完全不同，**立即输出 `{"has_issues": false, "issues": [], "summary": "两章节内容主题不同，无需对比"}`**，不要做进一步的审查，不要报告任何错误。
3. **只有当两个章节确实在讨论同一主题时**，才按照以下维度进行审查：方法原理是否清晰、定量参数是否完整、操作步骤是否合理、试剂仪器是否规范、计算验证是否正确、表述是否规范。
4. **绝不能因为初稿缺少参考方法的某个步骤就报"内容缺失"**。检验方法允许将同一类操作分散到不同章节，或将多个步骤合并，只要最终方法完整合理即可。必须检查初稿全文确认该步骤真的不存在，而不是因为它出现在不同编号的章节下就认为缺失。
5. **绝不能因为初稿与参考使用了不同溶剂/仪器/操作顺序就判错**。只要初稿的技术选择是合理的，就不应标记为问题。

- 如果两章节内容主题不同，has_issues 设为 false，issues 为空数组，summary 填"两章节内容主题不同，无需对比"
- 如果初稿该章节内容质量良好，has_issues 设为 false，issues 为空数组
- 只输出 JSON，不要输出其他内容"""


class AIService:
    """DeepSeek AI 语义分析服务"""

    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = DEEPSEEK_BASE_URL
        self.model = DEEPSEEK_MODEL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0
        )

    async def synthesize_multi_reference(
        self,
        references: List[ParsedDocument],
        doc_type: str = "inspection_method"
    ) -> dict:
        """将多份参考标准合成为一份共识文档。

        Args:
            references: 多份参考标准解析结果
            doc_type: 文档类型

        Returns:
            共识合成结果 dict，包含 consensus_sections、overall_common_elements、
            areas_of_disagreement、summary
        """
        if len(references) < 2:
            return {}

        ref_count = len(references)
        titles_block = "\n".join(
            f"  [{i+1}] 《{r.title or '未命名标准'}》"
            for i, r in enumerate(references)
        )

        # 每份参考取关键章节（取前20个，以避免 token 爆炸）
        contents_parts = []
        for i, ref in enumerate(references):
            ref_name = ref.title or f"参考标准{i+1}"
            sections_text = []
            for sec in ref.sections[:20]:
                heading = sec.raw_heading or sec.title or f"章节{sec.number}"
                content = sec.content[:800].strip()  # 每节最多800字
                if content:
                    sections_text.append(f"【{heading}】\n{content}")
            sections_str = "\n---\n".join(sections_text) if sections_text else "（无章节内容）"
            contents_parts.append(
                f"=== 参考标准 [{i+1}] 《{ref_name}》 ===\n{sections_str}"
            )
        contents_block = "\n\n".join(contents_parts)

        if doc_type == "inspection_method":
            prompt_template = INSPECTION_METHOD_CONSENSUS_PROMPT
            system_role = (
                "你是一位资深的化妆品/牙膏检验方法审查专家，擅长从多份参考标准中提炼共性要求。"
                "请严格按 JSON 格式输出，不要输出任何其他内容。"
            )
        else:
            prompt_template = GENERAL_CONSENSUS_PROMPT
            system_role = (
                "你是一位资深的国家标准审查专家，擅长从多份标准文本中提炼共性格式规范。"
                "请严格按 JSON 格式输出，不要输出任何其他内容。"
            )

        prompt = prompt_template.format(
            ref_count=ref_count,
            ref_titles=titles_block,
            ref_contents=contents_block,
        )

        try:
            result = await self._call_llm(prompt, system_role=system_role)
            return result if result else {}
        except Exception as e:
            logger.error(f"多参考共识合成失败: {e}")
            return {}


    # ============================================================
    # 多参考共识感知审查 Prompt - 化妆品/牙膏检验方法
    # ============================================================
    CONSENSUS_INSPECTION_COMPARE_PROMPT = """你是一位资深的化妆品/牙膏检验方法审查专家。你已经获得了由多份参考标准提炼出的"共识要求"，请基于这些共识对初稿进行审查。
    
    【多参考标准提炼出的共识要求】
    {consensus_text}
    
    【待审初稿全文】
    {draft_content}
    
    请从以下维度审查初稿是否满足共识要求：
    1. **必须包含的参数**（所有参考都要求的）：检出限(LOD)、定量下限(LOQ)、线性范围、相关系数、回收率、精密度等，初稿是否都有提供？
    2. **方法原理**：初稿的检测原理是否清晰？原理描述是否与共识要求一致？
    3. **试剂与仪器规范**：有机溶剂是否标注了纯度等级？仪器条件是否完整？
    4. **操作步骤完整性**：样品前处理、标准溶液配制、仪器测定、定性判定、定量计算等步骤是否完整？
    5. **表述规范性**：是否使用了标准化的检验方法术语（如"精确至X.XXXXg"、"涡旋混匀"、"0.22μm滤膜过滤"等）？
    6. **合理差异识别**：初稿与共识要求的差异，是否属于可接受的合理改进（如不同溶剂品牌、不同仪器型号、不同的前处理条件）？如果是，请明确说明。
    
    请以 JSON 格式输出审查结果：
    ```json
    {{
      "has_issues": true/false,
      "consensus_based_issues": [
        {{
          "level": "critical/major/minor/suggestion",
          "consensus_requirement": "对应的共识要求描述",
          "title": "问题标题",
          "description": "详细说明",
          "suggestion": "修改建议"
        }}
      ],
      "acceptable_differences": [
        {{"description": "初稿与共识的差异描述", "reason": "为什么这个差异是可接受的"}}
      ],
      "summary": "整体审查意见（一句话）"
    }}
    ```
    
    **审查原则**：
    - 共识要求是所有参考标准一致同意的内容，初稿必须满足，如有违背则应报告问题
    - 各参考之间可接受的差异（即 acceptable_variations）不应报为问题
    - 初稿在满足共识要求的前提下，可以有自己的方法特色和技术选择
    - 只输出 JSON，不要输出其他内容"""
    
    
    
    # ============================================================
    # 多参考共识感知审查 Prompt - 化妆品标准
    # ============================================================
    CONSENSUS_GENERAL_COMPARE_PROMPT = """你是一位资深的化妆品标准审查专家。你已经获得了由多份参考标准提炼出的"共识要求"，请基于这些共识对初稿进行审查。
    
    【多参考标准提炼出的共识要求】
    {consensus_text}
    
    【待审初稿全文】
    {draft_content}
    
    请审查初稿是否满足这些共识要求，并输出 JSON 格式：
    ```json
    {{
      "has_issues": true/false,
      "consensus_based_issues": [
        {{
          "level": "critical/major/minor/suggestion",
          "consensus_requirement": "对应的共识要求",
          "title": "问题标题",
          "description": "详细说明",
          "suggestion": "修改建议"
        }}
      ],
      "acceptable_differences": [
        {{"description": "差异描述", "reason": "可接受原因"}}
      ],
      "summary": "整体意见"
    }}
    ```
    
    只输出 JSON，不要输出其他内容。"""


    # ============================================================
    # 规范原文全文对照审查 Prompt - 化妆品/牙膏检验方法
    # 核心差异：AI 同时收到完整规范原文 + 完整初稿全文，
    #          做真正的"拿着规范审初稿"，而非碎片对比
    # ============================================================
    SPEC_INSPECTION_COMPARE_PROMPT = """你是一位资深的化妆品/牙膏检验方法审查专家，持有《化妆品检验方法标准文本规范》完整知识。请对初稿进行系统性规范对照审查。

【化妆品检验方法标准文本规范 原文】

{spec_content}

【待审初稿 完整全文】

{draft_content}

---

## 审查要求

请仔细对照规范原文与初稿全文，进行以下维度的系统性审查：

### 一、结构性审查
- 章节顺序是否完整（1范围 → 2方法提要 → 3试剂和材料 → 4仪器和设备 → 5分析步骤 → 6计算 → 7图谱 → 附录）
- 5.x子节是否完整（5.1/5.2（如需）/5.3/5.4/5.5/5.6）
- 6.x子节是否完整（6.1计算 + 6.2回收率和精密度）
- 附录标注是否正确（附录A资料性、附录B规范性、附录C资料性按需）

### 二、章节内容规范性审查
**第1章 范围**：三要素是否齐全（方法规定 + 适用基质 + 目标物指引）；基质分类用语是否规范（液体水基类/膏霜乳类/凝胶类/液体油基类/粉剂类/蜡基类）

**第2章 方法提要**：原理链条是否完整（提取→分离→检测→定性→定量→计算）；检出限/定量下限是否给出具体数值并注明取样量条件

**第3章 试剂和材料**：总则句是否存在；有机溶剂是否标注色谱纯/分析纯；标准品是否引至附录A；溶液配制是否含储存条件和有效期

**第4章 仪器和设备**：主机仪器是否含关键配置；分析天平是否注感量；离心机是否注转速

**第5章 分析步骤**：
- 5.1是否描述至少5个浓度点的标准系列溶液制备
- 5.2/5.3基质分类顺序是否与范围章节一致
- 样品处理每类是否含完整要素（取样量→提取溶剂→前处理→分离→待测）
- 5.4参考条件：色谱条件是否完整；≥10种目标物时质谱参数是否引至附录B
- 5.5定性判定：是否含保留时间偏差标准 + 离子丰度比偏差表（±20%/±25%/±30%/±50%四档）
- 5.6定量测定：是否引用5.1/5.2、是否描述标准曲线横纵坐标

**第6章 计算**：公式是否完整；符号说明是否每行一个含单位；精密度是否有量化标准；6.2回收率和精密度数据是否完整

**第7章 图谱**：图题格式是否规范（"图1"无空格）；是否有峰标注

**附录**：类型标注是否正确；附录A序号/CAS/分子式/分子量列是否完整；附录B定量离子对是否标注*；附录A/B序号是否一一对应

### 三、一致性审查
- 范围章节基质分类 vs 5.3样品处理基质分类
- 目标物数量：范围→方法提要→附录A→附录B四处是否一致
- 试剂编号：正文引用（3.x）是否存在
- 单位体系：全文是否统一（μg/g或mg/kg，不混用ppm）

### 四、格式规范审查
- 数值范围是否用波浪号~（非短横线-）
- **浓度单位：全文是否统一；滤膜孔径必须用希腊字母μ（μm），不能用ASCII字母um**
- 交叉引用格式是否正确（章节用阿拉伯数字、试剂用3.x、附录用字母）
- 英文标题是否符合"等N种"格式且首字母大写
- **特别注意：搜索全文中所有类似"0.22um"、"0.45um"的写法，均应修正为"0.22μm"、"0.45μm"**

---

## 输出格式

请严格按以下 JSON 格式输出审查结果，不要输出任何其他内容：

```json
{{
  "has_issues": true/false,
  "结构性问题": [
    {{
      "level": "critical/major/minor",
      "title": "问题标题",
      "规范要求": "规范原文对应要求",
      "初稿现状": "初稿中的实际表述或缺失情况",
      "修改建议": "具体修改方案"
    }}
  ],
  "内容规范性问题": [
    {{
      "level": "critical/major/minor",
      "章节": "对应章节号",
      "title": "问题标题",
      "规范要求": "规范原文对应要求",
      "初稿现状": "初稿中的实际表述",
      "修改建议": "具体修改方案"
    }}
  ],
  "一致性问题": [
    {{
      "level": "critical/major/minor",
      "title": "问题标题",
      "描述": "不一致的具体表现",
      "修改建议": "修改方案"
    }}
  ],
  "格式规范问题": [
    {{
      "level": "minor/suggestion",
      "位置": "出现位置",
      "title": "问题标题",
      "规范要求": "正确格式",
      "修改建议": "具体修改方案"
    }}
  ],
  "修改优先级": {{
    "高优先级": ["必须修正的关键问题列表"],
    "中优先级": ["应当修正的问题列表"],
    "低优先级": ["建议优化的问题列表"]
  }},
  "summary": "整体审查意见（一段话，总结主要问题和优先行动方向）"
}}
```

**审查原则**：
- 严格以规范原文为准绳，对照初稿现状进行判断
- 同一问题只在一个分类下报告，不重复
- critical/major 问题必须给出具体修改建议（可copy-paste直接用的表述）
- 只输出 JSON，不要输出其他任何内容"""


    async def compare_sections(
        self,
        draft_section: DocumentSection,
        ref_section: DocumentSection,
        ref_title: str = "",
        doc_type: str = "general_standard"
    ) -> List[Issue]:
        """对比两个章节的语义差异"""
        # 根据文档类型选择 Prompt
        if doc_type == "inspection_method":
            prompt_template = INSPECTION_METHOD_COMPARE_PROMPT
            system_role = "你是一位资深的化妆品检验方法审查专家，熟悉国家药监局发布的化妆品/牙膏检验方法规范。请严格按照要求的 JSON 格式输出。"
        else:
            prompt_template = SEMANTIC_COMPARE_PROMPT
            system_role = "你是一位资深的化妆品标准审查专家，擅长对比分析化妆品标准文本的差异和问题。请严格按照要求的 JSON 格式输出。"

        prompt = prompt_template.format(
            ref_title=ref_title or "参考标准",
            ref_section_heading=ref_section.raw_heading,
            ref_section_content=(ref_section.content[:2000] + "...") if len(ref_section.content) > 2000 else ref_section.content,
            draft_section_heading=draft_section.raw_heading,
            draft_section_content=(draft_section.content[:2000] + "...") if len(draft_section.content) > 2000 else draft_section.content,
        )

        try:
            response = await self._call_llm(prompt, system_role=system_role)
            if response:
                return self._parse_ai_issues(response, draft_section.number)
        except Exception as e:
            logger.error(f"AI 语义分析失败: {e}")

        return []

    async def compare_documents(
        self,
        draft: ParsedDocument,
        reference: ParsedDocument,
        progress_callback=None,
        doc_type: str = "general_standard",
        consensus: dict = None
    ) -> List[Issue]:
        """对比两份文档的所有章节。

        Args:
            consensus: 多参考共识合成结果（dict）。提供此参数时使用共识感知审查，
                        只报告真正违背共识的问题，避免大量"差异噪音"。
        """
        # 多参考共识模式
        if consensus:
            return await self._compare_against_consensus(draft, consensus, progress_callback, doc_type)

        # 单参考模式：逐章节配对对比
        all_issues = []
        matched_pairs = self._match_sections(draft, reference)
        total = len(matched_pairs)
        for idx, (draft_sec, ref_sec) in enumerate(matched_pairs):
            if progress_callback:
                result = progress_callback(idx, total, draft_sec.raw_heading)
                if hasattr(result, '__await__'):
                    await result
            issues = await self.compare_sections(draft_sec, ref_sec, reference.title, doc_type=doc_type)
            all_issues.extend(issues)
            await asyncio.sleep(0.5)
        return all_issues

    async def specification_review(
        self,
        draft: ParsedDocument,
        progress_callback=None,
        doc_type: str = "inspection_method"
    ) -> List[Issue]:
        """规范原文全文对照审查（专为化妆品标准设计）

        Args:
            draft: 初稿解析结果
            progress_callback: 进度回调
            doc_type: 文档类型

        Returns:
            结构化审查问题列表
        """
        import os as _os
        from config import SPEC_INSPECTION_METHOD

        if progress_callback:
            await progress_callback(0, 1, "加载规范文档...")

        # 读取规范原文
        if not _os.path.exists(SPEC_INSPECTION_METHOD):
            logger.warning(f"规范文档不存在: {SPEC_INSPECTION_METHOD}")
            return []

        with open(SPEC_INSPECTION_METHOD, "r", encoding="utf-8") as f:
            spec_content = f.read()

        # 整理初稿全文（取前50节，每节500字以控制token）
        ds = []
        for sec in draft.sections[:50]:
            h = sec.raw_heading or sec.title or f"章节{sec.number}"
            c = sec.content[:500].strip()
            if c:
                ds.append(f"【{h}】\n{c}")
        draft_content = "\n\n".join(ds) if ds else draft.full_text[:5000]

        if progress_callback:
            await progress_callback(0, 1, "AI规范对照审查中...")

        prompt = self.SPEC_INSPECTION_COMPARE_PROMPT.format(
            spec_content=spec_content,
            draft_content=draft_content
        )
        system_role = (
            "你是一位资深的化妆品/牙膏检验方法审查专家，持有《化妆品检验方法标准文本规范》完整知识。"
            "请严格按要求的 JSON 格式输出，不要输出任何其他内容。"
        )

        try:
            resp = await self._call_llm(prompt, system_role=system_role)
            if not resp:
                return []

            issues = []
            all_issues_list = (
                resp.get("结构性问题", [])
                + resp.get("内容规范性问题", [])
                + resp.get("一致性问题", [])
                + resp.get("格式规范问题", [])
            )

            for item in all_issues_list:
                level = item.get("level", "suggestion")
                section = item.get("章节", item.get("位置", "-"))
                title = item.get("title", "")
                description = (
                    f"[规范要求] {item.get('规范要求', '')}\n"
                    f"[初稿现状] {item.get('初稿现状', item.get('描述', ''))}"
                )
                suggestion = item.get("修改建议", "")
                issues.append(Issue(
                    level=level,
                    category="spec_review",
                    section=section,
                    title=title,
                    description=description,
                    reference="规范原文全文对照审查",
                    suggestion=suggestion
                ))

            logger.info(f"规范原文审查完成: {len(issues)} 个问题")
            return issues

        except Exception as e:
            logger.error(f"规范原文审查失败: {e}")
            return []

    async def _compare_against_consensus(
        self, draft: ParsedDocument, consensus: dict, progress_callback, doc_type: str
    ) -> List[Issue]:
        """基于多参考共识对初稿进行一次性整体审查（不逐章节对比）。"""
        if progress_callback:
            await progress_callback(0, 1, "共识感知审查中...")

        # 整理共识文本
        sections = consensus.get("consensus_sections", [])
        parts = []
        for sec in sections:
            theme = sec.get("section_theme", "")
            common = sec.get("common_requirements", [])
            variations = sec.get("acceptable_variations", [])
            parts.append(f"【{theme}】共同要求：{'；'.join(common) if common else '（无）'}"
                         + (f"\n  可接受差异：{'；'.join(variations)}" if variations else ""))
        sections_text = "\n\n".join(parts) if parts else ""

        overall = consensus.get("overall_common_elements", {})
        oparts = []
        if overall.get("must_have_parameters"):
            oparts.append("必须参数：" + "、".join(overall["must_have_parameters"]))
        if overall.get("reagent_purity_requirements"):
            oparts.append("试剂纯度：" + overall["reagent_purity_requirements"])
        if overall.get("terminology_common"):
            oparts.append("标准术语：" + "、".join(overall["terminology_common"]))
        if overall.get("calculation_common"):
            oparts.append("计算方式：" + overall["calculation_common"])
        overall_text = "\n".join(oparts)

        disagreements = consensus.get("areas_of_disagreement", [])
        dparts = []
        for d in disagreements:
            approaches = d.get("reference_approaches", {})
            dparts.append(f"【{d.get('topic', '')}】{'；'.join(f'{k}={v}' for k, v in approaches.items())}")
        disagree_text = "\n".join(dparts) if dparts else ""

        ct_parts = []
        if sections_text:
            ct_parts.append(f"【各主题共同要求】\n{sections_text}")
        if overall_text:
            ct_parts.append(f"【通用共同要求】\n{overall_text}")
        if disagree_text:
            ct_parts.append(f"【存在分歧的领域（不作为审查依据）】\n{disagree_text}")
        consensus_text = "\n\n".join(ct_parts)

        # 初稿全文（前30节，每节300字）
        ds = []
        for sec in draft.sections[:30]:
            h = sec.raw_heading or sec.title or f"章节{sec.number}"
            c = sec.content[:300].strip()
            if c:
                ds.append(f"【{h}】\n{c}")
        draft_content = "\n\n".join(ds) if ds else draft.content[:4000]

        if doc_type == "inspection_method":
            pt = CONSENSUS_INSPECTION_COMPARE_PROMPT
            sr = ("你是一位资深的化妆品/牙膏检验方法审查专家。"
                  "请严格按 JSON 格式输出，不要输出任何其他内容。")
        else:
            pt = CONSENSUS_GENERAL_COMPARE_PROMPT
            sr = ("你是一位资深的化妆品标准审查专家。"
                  "请严格按 JSON 格式输出，不要输出任何其他内容。")

        prompt = pt.format(consensus_text=consensus_text, draft_content=draft_content)
        try:
            resp = await self._call_llm(prompt, system_role=sr)
            if not resp:
                return []
            issues = []
            if resp.get("consensus_based_issues"):
                for item in resp["consensus_based_issues"]:
                    issues.append(Issue(
                        level=item.get("level", "suggestion"),
                        category="semantic",
                        section="全文",
                        title=item.get("title", ""),
                        description=f"[共识要求: {item.get('consensus_requirement', '')}] {item.get('description', '')}",
                        reference="多参考共识审查",
                        suggestion=item.get("suggestion", "")
                    ))
            if resp.get("acceptable_differences"):
                logger.info(f"初稿与共识可接受差异: {resp['acceptable_differences']}")
            return issues
        except Exception as e:
            logger.error(f"共识审查失败: {e}")
            return []

    def _match_sections(
        self, draft: ParsedDocument, reference: ParsedDocument
    ) -> List[tuple]:
        """匹配初稿和参考标准中的对应章节"""
        pairs = []
        # 第一阶段：按编号匹配
        ref_by_num = {s.number: s for s in reference.sections}
        for d_sec in draft.sections:
            if d_sec.number in ref_by_num:
                pairs.append((d_sec, ref_by_num[d_sec.number]))

        # 质量过滤：如果编号配对的两个章节标题毫无主题重叠，
        # 说明编号相同只是巧合，拆散这对，让标题匹配阶段重新找
        filtered = []
        for d_sec, r_sec in pairs:
            if self._topics_overlap(d_sec.title, r_sec.title):
                filtered.append((d_sec, r_sec))
            # else: 编号相同但标题主题不同，不保留此配对
        pairs = filtered

        # 再尝试按标题关键词匹配
        draft_matched = {d.number for d, _ in pairs}
        for d_sec in draft.sections:
            if d_sec.number in draft_matched or not d_sec.title:
                continue
            for r_sec in reference.sections:
                if r_sec.number in {r.number for _, r in pairs}:
                    continue
                if not r_sec.title:
                    continue
                # 附录类章节：必须附录编号完全相同才能匹配（如"附录A"只能配"附录A"，不能配"附录B"）
                import re
                draft_appendix_match = re.match(r'^(附录[ABCDEFGHIJKLMNOPQRSTUVWXYZ])', d_sec.title.strip())
                ref_appendix_match = re.match(r'^(附录[ABCDEFGHIJKLMNOPQRSTUVWXYZ])', r_sec.title.strip())
                if draft_appendix_match and ref_appendix_match:
                    # 附录编号不同，不匹配
                    if draft_appendix_match.group(1) != ref_appendix_match.group(1):
                        continue
                    # 附录编号相同，正常匹配
                    pairs.append((d_sec, r_sec))
                    break
                # 非附录类：使用简单的标题包含匹配
                if (d_sec.title in r_sec.title or r_sec.title in d_sec.title):
                    pairs.append((d_sec, r_sec))
                    break

        return pairs

    @staticmethod
    def _topics_overlap(title1: str, title2: str) -> bool:
        """判断两个章节标题是否在同一主题上"""
        if not title1 or not title2:
            return True  # 标题缺失时不拆散配对
        # 提取中英文内容词
        import re
        words1 = set(re.findall(r'[\u4e00-\u9fff]+|[A-Za-z0-9]+', title1))
        words2 = set(re.findall(r'[\u4e00-\u9fff]+|[A-Za-z0-9]+', title2))
        # 过滤掉数字编号和常见虚词
        stopwords = {'的', '与', '和', '或', '及', '及其', '第', '章', '节', '条', '方法', '规范', '要求', '标准'}
        words1 -= stopwords
        words2 -= stopwords
        # 有交集说明主题重叠
        return bool(words1 & words2)

    async def _call_llm(self, prompt: str, system_role: str = None) -> Optional[dict]:
        """调用 DeepSeek API"""
        if not self.api_key:
            logger.warning("DeepSeek API Key 未配置，跳过 AI 分析")
            return None

        if system_role is None:
            system_role = "你是一位资深的化妆品标准审查专家，擅长对比分析化妆品标准文本的差异和问题。请严格按照要求的 JSON 格式输出。"

        try:
            resp = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_role},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4096
                }
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            # 提取 JSON
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"AI 返回内容 JSON 解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            return None

    def _parse_ai_issues(self, ai_result: dict, section: str) -> List[Issue]:
        """解析 AI 返回的审查结果"""
        issues = []
        if not ai_result or not ai_result.get("has_issues"):
            return issues

        for item in ai_result.get("issues", []):
            issues.append(Issue(
                level=item.get("level", "suggestion"),
                category="semantic",
                section=section,
                title=item.get("title", ""),
                description=item.get("description", ""),
                reference="AI 语义分析",
                suggestion=item.get("suggestion", "")
            ))

        return issues

    async def close(self):
        await self.client.aclose()
