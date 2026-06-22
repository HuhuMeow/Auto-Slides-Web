"""
轻量级演示计划生成模块：直接处理markdown文本生成演示计划
适配轻量级提取器的简化数据结构
"""
import os
import json
import logging
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("env.local"):
    load_dotenv("env.local")

# 尝试导入OpenAI相关包
try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    OPENAI_AVAILABLE = True

    # Import our unified LLM interface and parameter system
    from backend.llm.client import LLMInterface
    from backend.llm.settings import TaskType
    UNIFIED_INTERFACE_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    UNIFIED_INTERFACE_AVAILABLE = False

# 导入提示词
from backend.prompts import (
    KEY_CONTENT_EXTRACTION_PROMPT,
    SLIDES_PLANNING_PROMPT,
)
from backend.progress import emit_progress

class PlanningAgent:
    def __init__(
        self,
        lightweight_content_path: str,
        output_dir: str = "output",
        model_name: str = "gpt-4o",
        temperature: float = 0.2,
        api_key: Optional[str] = None,
        language: str = "zh"
    ):
        """
        初始化轻量级演示计划生成器

        Args:
            lightweight_content_path: 轻量级内容JSON文件路径
            output_dir: 输出目录
            model_name: 要使用的语言模型名称
            temperature: 模型生成的随机性程度
            api_key: OpenAI API密钥
            language: 输出语言，zh为中文，en为英文
        """
        self.lightweight_content_path = lightweight_content_path
        self.output_dir = output_dir
        self.model_name = model_name
        self.temperature = temperature
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.language = language

        # 设置日志
        self.logger = logging.getLogger(__name__)

        # 加载轻量级内容
        self.lightweight_content = self._load_lightweight_content()

        # 初始化模型
        self._init_model()

        # 演示计划数据
        self.paper_info = {}
        self.key_content = {}
        self.slides_plan = []
        self.presentation_plan = {}

    def _language_prompt(self) -> str:
        if self.language == "zh":
            return (
                "Please answer in Simplified Chinese. Translate all user-facing slide titles, "
                "bullet points, presenter notes, summaries, and recommendations into Chinese. "
                "Keep paper titles, author names, code identifiers, equations, and file paths unchanged when appropriate."
            )
        return "Please answer in English."

    def _load_lightweight_content(self) -> Dict[str, Any]:
        """加载轻量级内容"""
        try:
            with open(self.lightweight_content_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            return content
        except Exception as e:
            self.logger.error(f"加载轻量级内容失败: {str(e)}")
            return {}

    def _init_model(self):
        """初始化语言模型"""
        if not OPENAI_AVAILABLE:
            self.logger.warning("无法导入OpenAI相关包，将无法使用大语言模型生成演示计划")
            self.llm = None
            self.llm_interface = None
            emit_progress("Planning Agent", "Planning dependencies are unavailable", stage="planning", level="error")
            return

        if not self.api_key:
            self.logger.warning("未提供OpenAI API密钥，将无法使用大语言模型生成演示计划")
            self.llm = None
            self.llm_interface = None
            emit_progress("Planning Agent", "No model credential is available for planning", stage="planning", level="error")
            return

        try:
            emit_progress("Planning Agent", f"Initializing planning model {self.model_name}", stage="planning", progress=40)
            # Initialize unified LLM interface if available for better parameter control
            if UNIFIED_INTERFACE_AVAILABLE:
                self.llm_interface = LLMInterface(self.model_name, self.api_key)
                self.logger.info(f"已初始化统一LLM接口: {self.model_name} (使用优化参数)")
            else:
                self.llm_interface = None
                self.logger.warning("统一LLM接口不可用，使用传统方法")

            # Keep fallback LLM for compatibility
            self.llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                openai_api_key=self.api_key,
                openai_api_base=os.environ.get("OPENAI_API_BASE")
            )
            self.logger.info(f"已初始化语言模型: {self.model_name}")
            emit_progress("Planning Agent", "Planning model is ready", stage="planning", progress=41)
        except Exception as e:
            self.logger.error(f"初始化语言模型失败: {str(e)}")
            self.llm = None
            self.llm_interface = None
            emit_progress("Planning Agent", "Planning model initialization failed", stage="planning", level="error")

    def generate_presentation_plan(self) -> Dict[str, Any]:
        """
        生成演示计划

        Returns:
            Dict: 演示计划
        """
        if not self.lightweight_content:
            self.logger.error("没有轻量级内容可处理")
            return {}

        if not self.llm:
            self.logger.error("未初始化语言模型，无法生成演示计划")
            return {}

        emit_progress("Planning Agent", "Reading the enhanced paper and preparing a slide narrative", stage="planning", progress=42)

        # 提取论文基本信息
        self.logger.info("从markdown文本提取论文基本信息...")
        self.paper_info = self._extract_paper_info()
        emit_progress(
            "Planning Agent",
            f"Paper metadata extracted for {len(self.paper_info.get('authors', []))} author(s)",
            stage="planning",
            progress=45,
        )

        # 提取关键内容
        self.logger.info("从markdown文本提取论文关键内容...")
        self.key_content = self._extract_key_content(self.paper_info)
        emit_progress("Planning Agent", "Core contributions, method, evidence, and conclusions identified", stage="planning", progress=49)

        # 规划演示幻灯片
        self.logger.info("规划演示幻灯片...")
        self.slides_plan = self._plan_slides(self.paper_info, self.key_content)
        emit_progress("Planning Agent", f"Drafted a {len(self.slides_plan)}-slide presentation structure", stage="planning", progress=53)

        # 组装结果
        self.presentation_plan = {
            "paper_info": self.paper_info,
            "key_content": self.key_content,
            "slides_plan": self.slides_plan,
            "language": self.language,
            "pdf_path": self.lightweight_content.get("pdf_path", "")
        }

        return self.presentation_plan

    def _extract_paper_info(self) -> Dict[str, Any]:
        """
        从markdown文本提取论文基本信息

        Returns:
            Dict: 包含标题、作者、摘要等信息的字典
        """
        # 默认空结果
        paper_info = {
            "title": "",
            "authors": [],
            "affiliations": [],
            "abstract": "",
            "keywords": []
        }

        try:
            # 获取完整的markdown文本（包含标题、作者和摘要等）
            full_text = self.lightweight_content.get("full_text", "")
            first_part = full_text

            language_prompt = self._language_prompt()

            # 简化的论文信息提取提示
            paper_info_prompt = """
            你是一位学术论文分析专家。{language_prompt}。请从以下论文文本中提取基本信息：

            论文文本：
            {text}

            请提取以下信息并以JSON格式返回：
            1. 论文标题
            2. 作者列表
            3. 机构信息
            4. 摘要内容
            5. 关键词（如果有）

            返回格式：
            ```json
            {{
              "title": "论文标题",
              "authors": ["作者1", "作者2"],
              "affiliations": ["机构1", "机构2"],
              "abstract": "摘要内容",
              "keywords": ["关键词1", "关键词2"]
            }}
            ```

            仅返回JSON对象，不要有任何其他文字。
            """

            prompt = ChatPromptTemplate.from_template(paper_info_prompt)

            # 调用LLM
            chain = prompt | self.llm
            response = chain.invoke({
                "text": first_part,
                "language_prompt": language_prompt
            })

            # 解析结果
            response_text = response.content if hasattr(response, 'content') else str(response)

            # 提取JSON部分
            json_match = re.search(r'```(?:json)?(.*?)```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response_text.strip()

            # 尝试解析JSON
            extracted_info = json.loads(json_str)
            paper_info.update(extracted_info)

        except Exception as e:
            self.logger.error(f"提取论文信息时出错: {str(e)}")

        return paper_info

    def _extract_key_content(self, paper_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        从markdown文本提取论文关键内容

        Args:
            paper_info: 论文基本信息

        Returns:
            Dict: 论文关键内容
        """
        key_content = {
            "main_contributions": [],
            "methodology": "",
            "results": "",
            "figures": [],
            "conclusions": ""
        }

        try:
            # 获取完整的markdown文本
            full_text = self.lightweight_content.get("full_text", "")
            text_for_analysis = full_text

            # 获取图片信息
            images = self.lightweight_content.get("images", [])

            # 处理图片信息，为每个图片生成描述
            figures_info = []
            for img in images:
                figure_info = {
                    "id": img.get("id", ""),
                    "filename": img.get("filename", ""),
                    "path": img.get("path", ""),
                    "caption": img.get("caption", "")
                }
                figures_info.append(figure_info)

            language_prompt = self._language_prompt()

            prompt = ChatPromptTemplate.from_template(KEY_CONTENT_EXTRACTION_PROMPT)

            # 调用LLM
            chain = prompt | self.llm
            response = chain.invoke({
                "title": paper_info.get("title", ""),
                "authors": ", ".join(paper_info.get("authors", [])),
                "abstract": paper_info.get("abstract", ""),
                "toc_info": "",  # markdown文本已经包含结构信息
                "figures_info": json.dumps(figures_info, ensure_ascii=False),
                "text": text_for_analysis,
                "language_prompt": language_prompt
            })

            # 解析结果
            response_text = response.content if hasattr(response, 'content') else str(response)

            # 提取JSON部分
            json_match = re.search(r'```(?:json)?(.*?)```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response_text.strip()

            # 尝试解析JSON
            try:
                extracted_content = json.loads(json_str)
                key_content.update(extracted_content)
            except json.JSONDecodeError as e:
                self.logger.error(f"解析关键内容JSON时出错: {str(e)}")

            # 确保图片信息正确关联
            for idx, fig in enumerate(key_content.get("figures", [])):
                if idx < len(images):
                    original_img = images[idx]
                    fig["id"] = original_img.get("id", f"fig{idx+1}")
                    fig["filename"] = original_img.get("filename", "")
                    fig["path"] = original_img.get("path", "")
                    if not fig.get("caption"):
                        fig["caption"] = original_img.get("caption", "")

        except Exception as e:
            self.logger.error(f"提取关键内容时出错: {str(e)}")
            import traceback
            traceback.print_exc()

        return key_content

    def _plan_slides(self, paper_info: Dict[str, Any], key_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        规划演示幻灯片

        Args:
            paper_info: 论文基本信息
            key_content: 论文关键内容

        Returns:
            List: 幻灯片计划列表
        """
        slides_plan = []

        try:
            # 检查是否有增强内容
            enhanced_content = self.lightweight_content.get("enhanced_content", {})

            if enhanced_content:
                print(f"DEBUG: 使用增强内容分支")
                # 使用增强后的演讲导向内容
                presentation_sections = enhanced_content.get("presentation_sections", {})
                key_narratives = enhanced_content.get("key_narratives", {})
                enhanced_tables = enhanced_content.get("tables", [])
                print(f"DEBUG: 找到 {len(enhanced_tables)} 个表格")
                if enhanced_tables:
                    print(f"DEBUG: 第一个表格预览: {enhanced_tables[0].get('title', 'No title')}")
                enhanced_equations = enhanced_content.get("equations", [])

                language_prompt = self._language_prompt()

                prompt = ChatPromptTemplate.from_template(SLIDES_PLANNING_PROMPT)

                # 准备用户提示内容
                user_prompt_content = f"""Paper Information:
Title: {paper_info.get("title", "")}
Authors: {", ".join(paper_info.get("authors", []))}
Abstract: {paper_info.get("abstract", "")}

Key Paper Content:
Main Contributions: {json.dumps(key_content.get("main_contributions", []), ensure_ascii=False)}
Background & Motivation: {presentation_sections.get("background_context", "")}
Methodology: {presentation_sections.get("technical_approach", "")}
Experimental Setup: {presentation_sections.get("evidence_proof", "")}
Main Results: {presentation_sections.get("evidence_proof", "")}
Conclusions: {presentation_sections.get("impact_significance", "")}

Paper Figures/Tables Information:
Figures Info: {json.dumps(key_content.get("figures", []), ensure_ascii=False)}
Tables Info: {json.dumps(enhanced_tables, ensure_ascii=False)}"""

                print(f"DEBUG: tables_info 参数长度: {len(json.dumps(enhanced_tables, ensure_ascii=False))}")
                print(f"DEBUG: tables_info 预览: {json.dumps(enhanced_tables, ensure_ascii=False)[:200]}...")

                # 使用传统LLM调用但增加max_tokens参数
                print("DEBUG: 使用传统LLM调用，支持大token限制")

                # 创建具有大token限制的LLM实例
                enhanced_llm = ChatOpenAI(
                    model_name=self.model_name,
                    temperature=self.temperature,
                    max_tokens=12000,  # 增加token限制
                    openai_api_key=self.api_key,
                    openai_api_base=os.environ.get("OPENAI_API_BASE")
                )

                chain = prompt | enhanced_llm
                response = chain.invoke({
                    "title": paper_info.get("title", ""),
                    "authors": ", ".join(paper_info.get("authors", [])),
                    "abstract": paper_info.get("abstract", ""),
                    "contributions": json.dumps(key_content.get("main_contributions", []), ensure_ascii=False),
                    "background_motivation": presentation_sections.get("background_context", ""),
                    "methodology": presentation_sections.get("technical_approach", ""),
                    "experimental_setup": presentation_sections.get("evidence_proof", ""),
                    "results": presentation_sections.get("evidence_proof", ""),
                    "conclusions": presentation_sections.get("impact_significance", ""),
                    "figures_info": json.dumps(key_content.get("figures", []), ensure_ascii=False),
                    "tables_info": json.dumps(enhanced_tables, ensure_ascii=False),
                    "language_prompt": language_prompt
                })
            else:
                # 使用原有逻辑（向后兼容）
                language_prompt = self._language_prompt()

                prompt = ChatPromptTemplate.from_template(SLIDES_PLANNING_PROMPT)

                # 调用LLM
                chain = prompt | self.llm
                response = chain.invoke({
                    "title": paper_info.get("title", ""),
                    "authors": ", ".join(paper_info.get("authors", [])),
                    "abstract": paper_info.get("abstract", ""),
                    "contributions": json.dumps(key_content.get("main_contributions", []), ensure_ascii=False),
                    "background_motivation": key_content.get("background_motivation", ""),
                    "methodology": key_content.get("methodology", ""),
                    "experimental_setup": key_content.get("experimental_setup", ""),
                    "results": key_content.get("results", ""),
                    "conclusions": key_content.get("conclusions", ""),
                    "figures_info": json.dumps(key_content.get("figures", []), ensure_ascii=False),
                    "language_prompt": language_prompt
                })

            # 解析结果 - 传统LLM调用返回的是字符串
            response_text = response.content if hasattr(response, 'content') else str(response)

            # 提取JSON部分
            json_match = re.search(r'```(?:json)?(.*?)```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response_text.strip()

            # 尝试解析JSON
            slides_plan = json.loads(json_str)

            # Planner已经直接分配了图片，无需后置智能匹配
            self.logger.info("使用Planner直接分配的图片，跳过后置智能匹配")

            # 验证图片引用的有效性 - 使用原始图片数据而不是LLM可能修改过的数据
            original_figures = self.lightweight_content.get("images", [])
            available_figures = {fig["id"]: fig for fig in original_figures}

            for slide in slides_plan:
                if slide.get("includes_figure") and slide.get("figure_reference"):
                    fig_ref = slide.get("figure_reference")
                    if fig_ref and "id" in fig_ref:
                        fig_id = fig_ref.get("id")
                        if fig_id in available_figures:
                            # 使用原始图片信息（包含未被修改的caption）
                            matched_fig = available_figures[fig_id]
                            fig_ref.update(matched_fig)
                        else:
                            self.logger.warning(f"幻灯片引用了不存在的图片ID: {fig_id}")
                            slide["includes_figure"] = False
                            slide["figure_reference"] = None

        except Exception as e:
            self.logger.error(f"规划幻灯片时出错: {str(e)}")

        return slides_plan

    def save_presentation_plan(self, presentation_plan, output_file=None):
        """
        保存演示计划到JSON文件

        Args:
            presentation_plan: 演示计划
            output_file: 输出文件路径，如果为None则使用默认路径

        Returns:
            str: 保存的文件路径
        """
        if output_file is None:
            output_file = os.path.join(self.output_dir, "lightweight_presentation_plan.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(presentation_plan, f, ensure_ascii=False, indent=2)

        # 记录文件大小
        file_size = os.path.getsize(output_file)
        self.logger.info(f"演示计划已保存到: {output_file}")
        self.logger.info(f"文件大小: {file_size / 1024:.2f}KB")
        emit_progress("Planning Agent", "Presentation plan artifact saved", stage="planning", progress=54, level="success")

        return output_file
