# 项目记忆 - Claw (标准审查助手)

## 项目概述
- 标准审查助手 Web 应用，支持国家标准(GB/T 1.1-2020)和化妆品/牙膏检验方法的智能审查
- 前后端分离：FastAPI + 原生 HTML/CSS/JS
- 后端目录: `backend/`，前端目录: `frontend/`

## 用户信息
- 用户在化妆品领域工作（药检所/方所），关注化妆品检验方法
- 提供了7份国家药监局已发布的检验方法文档作为参考

## 技术架构
- **解析器**: DocxParser 支持通用标准和检验方法两种文档类型自动识别
- **检查器**: FormatChecker(GB/T 1.1) + CompletenessChecker + TerminologyChecker + InspectionMethodChecker(化妆品专用)
- **AI服务**: DeepSeek API，支持通用标准和检验方法两套 Prompt
- **文档路由**: review_service 根据解析结果自动选择检查流程

## 关键数据文件
- `backend/rules/inspection_method.yaml` - 检验方法格式规则
- `backend/data/cosmetic_terms.yaml` - 化妆品专业术语库(~100+术语)
- `backend/checkers/inspection_method_checker.py` - 检验方法专项检查器(14维度)

## 2026-04-08: 规范文档增强（基于用户提供的《化妆品检验方法标准文本规范.md》）
根据用户提供的详细规范文档，新增8个检查维度：
1. 附录类型标注（资料性/规范性）—— 维度七
2. 范围章节三要素（方法规定+适用基质+目标物指引）—— 维度八
3. 定性判定离子丰度比偏差表（4档：±20%/±25%/±30%/±50%）—— 维度九
4. 基质分类一致性（范围章节 vs 5.3样品处理）—— 维度十
5. 附录A/B序号一致性检查 —— 维度十一
6. 交叉引用完整性（附录引用是否存在）—— 维度十二
7. 数值范围格式（波浪号~代替短横线-，禁止ppm混用）—— 维度十三
8. 仪器条件增强（天平感量、离心机转速）—— 维度十四
同时修复：术语检查器主术语边界检查bug、章节匹配器附录编号精确匹配bug、评分公式扣分权重过高问题

## 2026-04-03: 化妆品检验方法专项优化
基于7份国家药监局检验方法文档进行二次优化：
1. 创建检验方法专属规则和化妆品术语库
2. 扩展DocxParser支持检验方法文档类型识别和附录表格解析
3. 新增InspectionMethodChecker(6个检查维度)
4. 更新review_service/ai_service支持文档类型路由
5. 前端适配化妆品检验方法语境
6. 用4份真实文档验证通过

## 2026-04-09: 多参考共识审查功能（语法修复）
实现多参考文档"共识审查"模式——先从多份参考标准合成共识，再以共识为基准审查初稿。
- `ai_service.py`: `CONSENSUS_INSPECTION_COMPARE_PROMPT` 和 `CONSENSUS_GENERAL_COMPARE_PROMPT` 常量原被放在模块级别(indent=0)，导致 `class AIService` 在此处关闭，后续 `compare_sections` 等方法(indent=4)出现在 class 外部引发 IndentationError
- 修复：将 `backend/services/ai_service.py` 第 287-365 行的 CONSENSUS 常量整体缩进 4 空格移入 class 内部，三个文件均通过语法检查

## 前端路径修复
- `index.html` 原先引用 `/static/css/style.css`、`/static/js/api.js` 等绝对路径
- 用 `file:///` 直接打开时这些路径无法解析，导致页面无样式无交互
- 已改为相对路径 `css/style.css`、`js/api.js`、`js/app.js`
- 后端 `main.py` 新增 `/css/{path}` 和 `/js/{path}` 路由，确保通过 HTTP 服务访问时也能正常加载
