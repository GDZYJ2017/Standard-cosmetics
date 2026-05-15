import json
import uuid
import logging
from datetime import datetime
from typing import Optional, List
from parsers import get_parser, ParsedDocument
from checkers import FormatChecker, CompletenessChecker, TerminologyChecker
from checkers.inspection_method_checker import InspectionMethodChecker
from .ai_service import AIService

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REPORTS_DIR

logger = logging.getLogger(__name__)


class ReviewService:
    """审查编排服务 - 协调各检查器和 AI 分析
    专为化妆品标准审查设计：
    - inspection_method: 化妆品/牙膏检验方法（使用检验方法专项检查器）
    - cosmetic_standard: 化妆品标准（使用化妆品标准专用检查器）
    """

    def __init__(self, progress_updater=None):
        """
        Args:
            progress_updater: 异步回调函数 (task_id, progress, step, status)
        """
        self.progress_updater = progress_updater
        self.format_checker = FormatChecker()
        self.completeness_checker = CompletenessChecker()
        self.terminology_checker = TerminologyChecker()
        self.inspection_checker = InspectionMethodChecker()
        self.ai_service = AIService()

    def _detect_doc_type(self, draft_doc: ParsedDocument) -> str:
        """根据解析结果判断文档类型，专注于化妆品标准"""
        # 默认使用检验方法类型，因为这是化妆品标准的主要类型
        return draft_doc.metadata.get("doc_type", "inspection_method")

    async def run_review(self, task_id: str, draft_path: str, ref_path: str,
                         task_name: str = "", ref_paths: List[str] = None):
        """执行完整审查流程（根据文档类型自动路由检查器）

        Args:
            ref_path: 单个参考标准路径（兼容旧接口）
            ref_paths: 多个参考标准路径（优先使用）；多参考时会先合成共识，再以共识为基准审查
        """
        import datetime as _dt
        try:
            # 阶段1：解析文档
            await self._update_progress(task_id, 5, "正在解析文档...", "running")

            # 1. 解析初稿
            draft_doc = get_parser(draft_path).parse(draft_path)

            # 识别文档类型
            doc_type = self._detect_doc_type(draft_doc)
            is_inspection = doc_type == "inspection_method"
            logger.info(f"文档类型识别: {doc_type} (title={draft_doc.title})")

            # 2. 解析参考（单路径或多路径）
            all_ref_docs: List[ParsedDocument] = []
            if ref_paths and len(ref_paths) > 1:
                # 多参考：解析所有参考文档
                for rp in ref_paths:
                    try:
                        rd = get_parser(rp).parse(rp)
                        all_ref_docs.append(rd)
                    except Exception as e:
                        logger.warning(f"解析参考文档失败 {rp}: {e}")
                ref_names = " / ".join(d.title or "未命名" for d in all_ref_docs)
                logger.info(f"多参考模式：{len(all_ref_docs)} 份参考标准 -> {ref_names}")
            elif ref_path:
                # 单参考
                ref_doc = get_parser(ref_path).parse(ref_path)
                all_ref_docs = [ref_doc]
                ref_names = ref_doc.title or "参考标准"
            else:
                all_ref_docs = []

            # 3. 多参考共识合成（仅多参考时执行）
            consensus = None
            if len(all_ref_docs) > 1:
                await self._update_progress(task_id, 10, "多参考共识提炼中...", "running")
                try:
                    consensus = await self.ai_service.synthesize_multi_reference(
                        all_ref_docs, doc_type=doc_type
                    )
                    logger.info(f"共识合成完成: {consensus.get('summary', '')[:100]}")
                except Exception as e:
                    logger.error(f"共识合成失败（降级为单参考对比）: {e}")
                    consensus = None

            # 主参考文档：多参考时用第一份（用于规则检查器的兼容性）
            ref_doc = all_ref_docs[0] if all_ref_docs else None

            all_issues = []

            if is_inspection:
                # ========== 化妆品检验方法文档审查流程 ==========
                await self._update_progress(task_id, 15, "检验方法结构检查中...", "running")

                # 2a. 检验方法专项检查（章节结构+方法提要+试剂仪器+数据参数+附录）
                inspection_result = self.inspection_checker.check(draft_doc, ref_doc)
                all_issues.extend(inspection_result.issues)

                await self._update_progress(task_id, 40, "术语和格式检查中...", "running")

                # 2b. 术语检查（使用内置化妆品术语库）
                terminology_result = self.terminology_checker.check(draft_doc, ref_doc)
                all_issues.extend(terminology_result.issues)

                # 2c. AI 规范原文全文对照审查（高优先级执行）
                # 这是核心升级：AI 直接拿到完整规范原文 + 完整初稿，
                # 做系统性规范对照，而非碎片化章节对比
                await self._update_progress(task_id, 60, "AI 规范原文对照审查中...", "running")

                spec_review_issues = []
                try:
                    async def on_spec_progress(current, total, heading):
                        pct = 60 + int(30 * current / max(total, 1))
                        await self._update_progress(task_id, min(pct, 90), f"规范审查: {heading}", "running")

                    spec_review_issues = await self.ai_service.specification_review(
                        draft_doc,
                        progress_callback=on_spec_progress,
                        doc_type="inspection_method"
                    )
                except Exception as e:
                    logger.error(f"AI 规范原文审查异常（跳过）: {e}")

                all_issues.extend(spec_review_issues)

                # 2d. AI 语义分析（仅在有多参考共识时额外执行）
                if consensus:
                    await self._update_progress(task_id, 92, "AI 共识感知审查中...", "running")
                    semantic_issues = []
                    try:
                        semantic_issues = await self.ai_service.compare_documents(
                            draft_doc, ref_doc, progress_callback=None,
                            doc_type="inspection_method", consensus=consensus
                        )
                    except Exception as e:
                        logger.error(f"AI 共识审查异常（跳过）: {e}")
                    all_issues.extend(semantic_issues)
            else:
                # ========== 化妆品标准审查流程 ==========
                await self._update_progress(task_id, 15, "格式合规性检查中...", "running")

                format_result = self.format_checker.check(draft_doc, ref_doc)
                all_issues.extend(format_result.issues)

                await self._update_progress(task_id, 35, "内容完整性检查中...", "running")

                completeness_result = self.completeness_checker.check(draft_doc, ref_doc)
                all_issues.extend(completeness_result.issues)

                await self._update_progress(task_id, 50, "术语一致性检查中...", "running")

                terminology_result = self.terminology_checker.check(draft_doc, ref_doc)
                all_issues.extend(terminology_result.issues)

                await self._update_progress(task_id, 65, "AI 语义分析中...", "running")

                semantic_issues = []
                try:
                    async def on_progress(current, total, heading):
                        pct = 65 + int(20 * current / max(total, 1))
                        await self._update_progress(task_id, min(pct, 85), f"语义分析: {heading}", "running")

                    semantic_issues = await self.ai_service.compare_documents(
                        draft_doc, ref_doc, progress_callback=on_progress, consensus=consensus
                    )
                except Exception as e:
                    logger.error(f"AI 语义分析异常（跳过）: {e}")

                all_issues.extend(semantic_issues)

            await self._update_progress(task_id, 90, "生成审查报告...", "running")

            # 汇总结果
            report_data = self._build_report_data(
                task_id, task_name, draft_doc, ref_doc, all_issues, doc_type,
                multi_ref_names=ref_names if len(all_ref_docs) > 1 else None
            )

            # 保存结果
            report_path = os.path.join(REPORTS_DIR, f"{task_id}.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)

            await self._update_progress(task_id, 100, "审查完成", "done")

            return report_data

        except Exception as e:
            logger.error(f"审查任务异常: {e}", exc_info=True)
            await self._update_progress(task_id, 0, str(e), "failed")
            raise

    def _build_report_data(
        self, task_id, task_name, draft_doc, ref_doc, all_issues,
        doc_type="general_standard", multi_ref_names: str = None
    ) -> dict:
        """构建报告数据"""
        critical = sum(1 for i in all_issues if i.level == "critical")
        major = sum(1 for i in all_issues if i.level == "major")
        minor = sum(1 for i in all_issues if i.level == "minor")
        total = len(all_issues)

        # 计算评分（100分制，扣分制；降低权重避免分数过低）
        score = max(0, 100 - critical * 5 - major * 2 - minor * 1)

        # 多参考时显示汇总名称
        ref_title = multi_ref_names if multi_ref_names else (ref_doc.title if ref_doc else "")

        return {
            "task_id": task_id,
            "task_name": task_name,
            "draft_title": draft_doc.title,
            "draft_file": draft_doc.metadata.get("file_type", ""),
            "reference_title": ref_title,
            "reference_standard": "",
            "multi_reference": multi_ref_names is not None,
            "doc_type": doc_type,
            "total_issues": total,
            "critical_issues": critical,
            "major_issues": major,
            "minor_issues": minor,
            "score": score,
            "issues": [
                {
                    "id": issue.id,
                    "level": issue.level,
                    "category": issue.category,
                    "section": issue.section,
                    "title": issue.title,
                    "description": issue.description,
                    "reference": issue.reference,
                    "suggestion": issue.suggestion
                }
                for issue in all_issues
            ],
            "created_at": datetime.utcnow().isoformat()
        }

    async def _update_progress(self, task_id, progress, step, status):
        """更新任务进度"""
        if self.progress_updater:
            await self.progress_updater(task_id, progress, step, status)

    async def close(self):
        await self.ai_service.close()
