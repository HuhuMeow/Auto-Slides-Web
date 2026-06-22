"""
Key Content Extraction Prompts (presentation_planner.py)
"""

# Extract core content from papers (contributions, methodology, results, etc.)
KEY_CONTENT_EXTRACTION_PROMPT = """
You are an excellent academic content analysis expert. {language_prompt}. Please extract key content from the following academic paper information to create a professional, clear, and informative presentation.

Paper Title: {title}
Authors: {authors}
Abstract: {abstract}

{toc_info}

Please extract the following key content:

1. Main Contributions (3-5 concise points, 50-80 words each, highlighting innovation and importance)
2. Research Background & Motivation (Concisely describe the research background, existing problems, and solution motivation)
3. Methodology Overview (Concise but technically accurate, including algorithms, models, or theoretical frameworks, retaining key terms and proper nouns)
4. Experimental Setup (Key evaluation metrics, datasets, benchmarks, and comparison methods)
5. Main Results and Findings (Quantified key results, comparisons, and breakthrough points)
6. Conclusions and Future Work (Main conclusions and future research directions)
7. Important Figure/Chart Explanations and Significance (Detailed analysis)

For Mathematical Formulas:
- Extract key formulas, maintaining original mathematical symbol representations
- Briefly explain the meaning of each formula and its role in the paper
- Note: Formulas will be reproduced in LaTeX format in slides

For Code Snippets:
- If the paper contains code snippets, extract these codes and indicate their functionality
- Maintain code formatting, indentation, and syntax

For figures, please analyze the following information and provide explanations. The `caption` field contains the official title of the figure, please prioritize using it.

**Figure Caption Processing Requirements:**
1. Retain core descriptions and main information of figures
2. Simplify overly long citation links (such as [\\(Sun et al.,](#page-14-3) [2023\\)](#page-14-3), etc.), can be simplified to "from XXX study" or directly deleted
3. Maintain semantic integrity, ensuring captions still accurately describe figure content and purpose
4. **Must control length within 120 characters**, achieved through intelligent summarization and rewriting, absolutely no simple truncation
5. **Important: captions must remain in English, do not translate to other languages**
6. Remove redundant HTML tags (such as <sup>, </sup>, etc.) and complex citation formats
7. **If original caption is too long, please rewrite to a concise version, maintaining core meaning but using fewer words**

{figures_info}

Please return in JSON format as follows:
```json
{{
  "main_contributions": ["Contribution 1", "Contribution 2", ...],
  "background_motivation": "Research background and motivation overview",
  "methodology": "Methodology overview",
  "experimental_setup": "Experimental setup overview",
  "results": "Main results and findings",
  "equations": [
    {{
      "equation": "E = mc^2",
      "description": "Mass-energy equivalence formula",
      "context": "Used to explain the relationship between energy and mass"
    }}
  ],
  "code_snippets": [
    {{
      "code": "def example_function():\\n    return True",
      "language": "python",
      "purpose": "Implements example functionality"
    }}
  ],
  "figures": [
    {{
      "id": "Figure ID",
      "caption": "Official figure title (from caption field)",
      "description": "Detailed description of the figure, explaining its displayed content, methods, or results. Please expand based on the caption.",
      "importance": "Importance of the figure in the paper (high/medium/low)",
      "relevance": "Which section the figure is most relevant to (method/results/etc.)"
    }}
  ],
  "conclusions": "Conclusions and future work"
}}
```

Return only the JSON object without any other text. Ensure the JSON structure is strictly correct, especially pay attention to escaping nested quotes and formatting indentation.

Paper text:
{text}
"""
