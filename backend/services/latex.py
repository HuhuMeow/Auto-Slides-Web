"""
特殊字符处理模块：处理PDF到LaTeX转换过程中的特殊字符和Unicode字符
"""

import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# 特殊字符映射表：Unicode字符 -> LaTeX命令
UNICODE_TO_LATEX_MAP = {
    # 希腊字母（小写）
    'α': r'$\alpha$',
    'β': r'$\beta$',
    'γ': r'$\gamma$',
    'δ': r'$\delta$',
    'ε': r'$\varepsilon$',
    'ζ': r'$\zeta$',
    'η': r'$\eta$',
    'θ': r'$\theta$',
    'ι': r'$\iota$',
    'κ': r'$\kappa$',
    'λ': r'$\lambda$',
    'μ': r'$\mu$',
    'ν': r'$\nu$',
    'ξ': r'$\xi$',
    'ο': r'$o$',  # omicron通常用普通的o
    'π': r'$\pi$',
    'ρ': r'$\rho$',
    'σ': r'$\sigma$',
    'τ': r'$\tau$',
    'υ': r'$\upsilon$',
    'φ': r'$\phi$',
    'χ': r'$\chi$',
    'ψ': r'$\psi$',
    'ω': r'$\omega$',

    # 希腊字母（大写）
    'Α': r'$A$',  # Alpha通常用普通的A
    'Β': r'$B$',  # Beta通常用普通的B
    'Γ': r'$\Gamma$',
    'Δ': r'$\Delta$',
    'Ε': r'$E$',  # Epsilon通常用普通的E
    'Ζ': r'$Z$',  # Zeta通常用普通的Z
    'Η': r'$H$',  # Eta通常用普通的H
    'Θ': r'$\Theta$',
    'Ι': r'$I$',  # Iota通常用普通的I
    'Κ': r'$K$',  # Kappa通常用普通的K
    'Λ': r'$\Lambda$',
    'Μ': r'$M$',  # Mu通常用普通的M
    'Ν': r'$N$',  # Nu通常用普通的N
    'Ξ': r'$\Xi$',
    'Ο': r'$O$',  # Omicron通常用普通的O
    'Π': r'$\Pi$',
    'Ρ': r'$P$',  # Rho通常用普通的P
    'Σ': r'$\Sigma$',
    'Τ': r'$T$',  # Tau通常用普通的T
    'Υ': r'$\Upsilon$',
    'Φ': r'$\Phi$',
    'Χ': r'$X$',  # Chi通常用普通的X
    'Ψ': r'$\Psi$',
    'Ω': r'$\Omega$',

    # 常用符号
    '✓': r'$\checkmark$',
    '✗': r'$\times$',
    '✘': r'$\times$',
    '×': r'$\times$',
    '±': r'$\pm$',
    '∓': r'$\mp$',
    '≈': r'$\approx$',
    '≠': r'$\neq$',
    '≤': r'$\leq$',
    '≥': r'$\geq$',
    '≪': r'$\ll$',
    '≫': r'$\gg$',
    '→': r'$\rightarrow$',
    '←': r'$\leftarrow$',
    '↑': r'$\uparrow$',
    '↓': r'$\downarrow$',
    '↔': r'$\leftrightarrow$',
    '⇒': r'$\Rightarrow$',
    '⇐': r'$\Leftarrow$',
    '⇔': r'$\Leftrightarrow$',

    # 数学符号
    '∞': r'$\infty$',
    '∑': r'$\sum$',
    '∏': r'$\prod$',
    '∫': r'$\int$',
    '∂': r'$\partial$',
    '∇': r'$\nabla$',
    '∀': r'$\forall$',
    '∃': r'$\exists$',
    '∈': r'$\in$',
    '∉': r'$\notin$',
    '∅': r'$\emptyset$',
    '⊂': r'$\subset$',
    '⊃': r'$\supset$',
    '⊆': r'$\subseteq$',
    '⊇': r'$\supseteq$',
    '∪': r'$\cup$',
    '∩': r'$\cap$',
    '⊕': r'$\oplus$',
    '⊗': r'$\otimes$',
    '⊥': r'$\perp$',
    '∥': r'$\parallel$',
    '∠': r'$\angle$',
    '∴': r'$\therefore$',
    '∵': r'$\because$',

    # 上下标符号
    '⁰': r'$^0$',
    '¹': r'$^1$',
    '²': r'$^2$',
    '³': r'$^3$',
    '⁴': r'$^4$',
    '⁵': r'$^5$',
    '⁶': r'$^6$',
    '⁷': r'$^7$',
    '⁸': r'$^8$',
    '⁹': r'$^9$',

    # 其他常用符号
    '°': r'$^\circ$',  # 度数符号
    '‰': r'$\permille$',  # 千分号，需要额外包
    '…': r'$\ldots$',  # 省略号
    '–': r'--',  # en-dash
    '—': r'---',  # em-dash
    ''': r"'",  # 左单引号
    ''': r"'",  # 右单引号
    '"': r'``',  # 左双引号（Unicode，不是ASCII）
    '"': r"''",  # 右双引号（Unicode，不是ASCII）
    '✓': r'$\checkmark$',  # checkmark符号，需要amssymb包
}

# 需要额外LaTeX包的字符
SPECIAL_PACKAGES_REQUIRED = {
    r'$\checkmark$': ['amssymb'],
    r'$\permille$': ['textcomp'],
}

def convert_unicode_to_latex(text: str) -> str:
    """
    将文本中的Unicode特殊字符转换为LaTeX命令

    Args:
        text: 输入文本

    Returns:
        str: 转换后的文本
    """
    if not text:
        return text

    result = text
    conversions_made = []

    # 首先处理单引号括起来的文本：'text' -> ``text''
    import re
    quote_pattern = r"'([^']+)'"
    if re.search(quote_pattern, result):
        result = re.sub(quote_pattern, r"``\1''", result)
        conversions_made.append("单引号文本 → LaTeX双引号格式")

    # 然后逐个替换特殊字符
    for unicode_char, latex_cmd in UNICODE_TO_LATEX_MAP.items():
        if unicode_char in result:
            result = result.replace(unicode_char, latex_cmd)
            conversions_made.append(f"{unicode_char} → {latex_cmd}")

    if conversions_made:
        logger.debug(f"特殊字符转换: {', '.join(conversions_made)}")

    return result

def clean_caption_for_latex(caption: str) -> str:
    """
    清理caption中的Markdown链接和LaTeX特殊字符

    Args:
        caption: 原始caption文本

    Returns:
        str: 清理后的LaTeX兼容caption
    """
    if not caption:
        return caption

    result = caption

    # 移除或转换Markdown链接: [text](#link) -> text
    result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', result)

    # 首先处理单引号括起来的文本：'text' -> `text'
    result = re.sub(r"'([^']+)'", r"`\1'", result)

    # 然后转换其他LaTeX特殊字符
    latex_special_chars = {
        '#': r'\#',
        '$': r'\$',
        '%': r'\%',
        '&': r'\&',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '^': r'\textasciicircum{}',
        '~': r'\textasciitilde{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
        # 处理引号问题
        '"': r"''",  # 将直引号转换为LaTeX的双引号
        '"': r"''",  # 智能双引号结束
        '"': r"``",  # 智能双引号开始
        "'": r"'",   # 智能单引号转普通单引号
        "'": r"'",   # 智能单引号转普通单引号
        # 处理特殊符号
        '…': r'\ldots{}',
        '–': r'--',
        '—': r'---',
    }

    for char, replacement in latex_special_chars.items():
        result = result.replace(char, replacement)

    # 处理连续的单引号（将''text''转换为``text''格式）
    result = re.sub(r"''([^']+)''", r'``\1\'\'', result)

    # 清理连续的空格
    result = re.sub(r'\s+', ' ', result).strip()

    logger.debug(f"Caption cleaned: {caption[:50]}... -> {result[:50]}...")
    return result

def extract_required_packages(latex_text: str) -> List[str]:
    """
    根据LaTeX文本中使用的特殊命令，提取需要的包

    Args:
        latex_text: LaTeX文本

    Returns:
        List[str]: 需要的包名列表
    """
    required_packages = set()

    for latex_cmd, packages in SPECIAL_PACKAGES_REQUIRED.items():
        if latex_cmd in latex_text:
            required_packages.update(packages)

    return list(required_packages)

def ensure_latex_packages(latex_content: str, additional_packages: List[str] = None) -> str:
    """
    确保LaTeX文档包含必要的包声明

    Args:
        latex_content: LaTeX文档内容
        additional_packages: 额外需要的包

    Returns:
        str: 更新后的LaTeX内容
    """
    if additional_packages is None:
        additional_packages = []

    # 从文档内容中检测需要的包
    auto_detected_packages = extract_required_packages(latex_content)
    all_needed_packages = list(set(additional_packages + auto_detected_packages))

    if not all_needed_packages:
        return latex_content

    # 查找\documentclass行
    lines = latex_content.split('\n')
    insert_position = 0

    for i, line in enumerate(lines):
        if line.strip().startswith(r'\documentclass'):
            insert_position = i + 1
            break

    # 检查已存在的包声明
    existing_packages = set()
    for line in lines[insert_position:]:
        if line.strip().startswith(r'\usepackage'):
            # 提取包名
            match = re.search(r'\\usepackage(?:\[.*?\])?\{([^}]+)\}', line)
            if match:
                existing_packages.add(match.group(1))
        elif line.strip().startswith(r'\begin{document}'):
            break

    # 添加缺失的包
    new_package_lines = []
    for package in all_needed_packages:
        if package not in existing_packages:
            new_package_lines.append(f'\\usepackage{{{package}}}')
            logger.info(f"添加LaTeX包: {package}")

    if new_package_lines:
        # 在适当位置插入包声明
        lines[insert_position:insert_position] = new_package_lines
        return '\n'.join(lines)

    return latex_content

def preprocess_content_for_llm(content: str) -> str:
    """
    在送入LLM之前预处理内容，标记特殊字符

    Args:
        content: 原始内容

    Returns:
        str: 预处理后的内容
    """
    # 这里可以添加特殊标记来提醒LLM保留特殊字符
    # 例如用特殊标记包围重要的Unicode字符

    # 对于常见的特殊字符，添加保护标记
    protected_content = content

    # 保护希腊字母
    for greek_char in ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω']:
        if greek_char in protected_content:
            protected_content = protected_content.replace(greek_char, f"[GREEK:{greek_char}]")

    # 保护符号
    symbol_map = {'✓': '[CHECKMARK]', '✗': '[XMARK]', '×': '[TIMES]'}
    for symbol, placeholder in symbol_map.items():
        if symbol in protected_content:
            protected_content = protected_content.replace(symbol, placeholder)

    return protected_content

def postprocess_content_from_llm(content: str) -> str:
    """
    处理LLM返回的内容，恢复特殊字符标记

    Args:
        content: LLM返回的内容

    Returns:
        str: 恢复后的内容
    """
    restored_content = content

    # 恢复希腊字母
    greek_pattern = r'\[GREEK:([αβγδεζηθικλμνξοπρστυφχψω])\]'
    def restore_greek(match):
        return match.group(1)
    restored_content = re.sub(greek_pattern, restore_greek, restored_content)

    # 恢复符号
    symbol_restore_map = {'[CHECKMARK]': '✓', '[XMARK]': '✗', '[TIMES]': '×'}
    for placeholder, symbol in symbol_restore_map.items():
        restored_content = restored_content.replace(placeholder, symbol)

    return restored_content

def validate_special_chars_in_output(original_text: str, processed_text: str) -> List[str]:
    """
    验证处理后的文本是否保留了原文的特殊字符（考虑LaTeX转换）

    Args:
        original_text: 原始文本
        processed_text: 处理后的文本

    Returns:
        List[str]: 丢失的特殊字符列表
    """
    original_special_chars = set()
    truly_lost_chars = []

    # 检查原文中的所有已知特殊字符
    for char in UNICODE_TO_LATEX_MAP.keys():
        if char in original_text:
            original_special_chars.add(char)

    # 对于每个原文中的特殊字符，检查是否在处理后的文本中以某种形式存在
    for char in original_special_chars:
        latex_equivalent = UNICODE_TO_LATEX_MAP[char]

        # 检查是否存在原始字符或LaTeX等价物
        if char not in processed_text and latex_equivalent not in processed_text:
            truly_lost_chars.append(char)

    if truly_lost_chars:
        logger.warning(f"检测到真正丢失的特殊字符: {truly_lost_chars}")

    return truly_lost_chars
