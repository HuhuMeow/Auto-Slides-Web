"""
Table and Equation Extraction Prompts (pdf_parser.py)
Specialized for precise extraction of tables and mathematical formulas while maintaining original formatting
"""

# Specialized prompt for extracting tables and equations
EXTRACT_TABLES_AND_EQUATIONS_PROMPT = """
You are a professional academic document analysis expert, specialized in precisely extracting tables and mathematical formulas from academic papers. Your task is to identify and extract all tables and important mathematical formulas from the provided full paper text.

🚨 **CRITICAL TABLE PROCESSING RULE**: When you encounter tables like this format:
```
| Model | LLaVA-1.5 Accuracy | LLaVA-1.5 F1 | InstructBLIP Accuracy | InstructBLIP F1 | Qwen-VL Accuracy | Qwen-VL F1 |
```
You MUST preserve this EXACT column structure. NEVER reorganize it into something like:
```
| Model | LLaVA-1.5 | | InstructBLIP | | Qwen-VL | |
| | Accuracy F1 Score Accuracy F1 Score Accuracy F1 Score | | |
```
This reorganization is FORBIDDEN and will break the data structure.

**Core Requirements**:
1. **Absolute Precision**: You must maintain the original format of extracted content without any modifications, simplifications, or rearrangements.
2. **Completeness**: Cannot miss any tables or important formulas.

**Table Extraction Requirements**:
- Identify all data tables in the paper, regardless of their complexity
- **Strictly maintain original Markdown format**: Table structure, number of columns, rows, and cell content must be completely consistent with the original
- **MULTI-ROW HEADER PRESERVATION**: If a table has multiple header rows (e.g., group headers + column headers), you MUST preserve ALL header rows in the exact same sequence
- **Example**: For tables like:
  ```
  |           | Group A Header | Group B Header |
  |-----------|----------------|----------------|
  | Method    | Col1 | Col2    | Col3 | Col4    |
  ```
  You MUST keep this exact 3-row structure (group headers + separator + column headers)
- **Special Emphasis**: Absolutely prohibit converting wide tables to long tables or making any layout adjustments
- **No Simplification**: Not allowed to omit any columns, rows, or data, even if the table is complex
- **Column Preservation Rule**: If the original table has N columns, your markdown output MUST have exactly N columns - never consolidate multiple columns into fewer columns
- **Header Structure Rule**: Each column header in the original must become a separate column header in your markdown - never merge headers from different columns
- **GROUP HEADER RULE**: If the original table contains group headers (dataset names, category headers), preserve them exactly as they appear
- Extract table titles and numbers
- Provide brief descriptions for each table

**Mathematical Formula Extraction Requirements**:
- Identify key mathematical formulas in the paper, particularly:
  - Core algorithm formulas
  - Important theoretical definitions
  - Key computational formulas
  - Evaluation metric definitions
- Maintain LaTeX format unchanged
- Provide brief explanations and context for each formula

**Output Format**:
Please strictly return results in the following JSON format:

```json
{{
  "tables": [
    {{
      "id": "table1",
      "title": "Table 1: Complete table title",
      "markdown_content": "| Column1 | Column2 | Column3 |\\n|---------|---------|---------|\\n| Data1 | Data2 | Data3 |",
      "description": "Brief description of table content and purpose"
    }}
  ],
  "equations": [
    {{
      "latex": "E = mc^2",
      "description": "Mass-energy equivalence formula",
      "context": "The role and significance of this formula in the paper"
    }}
  ]
}}
```

**Key Reminders**:
- Your responsibility is **extraction** not **reconstruction**
- The markdown_content field of tables must be a precise copy of the original table
- Do not attempt to "improve" or "optimize" table formatting
- If the original table is in wide format, the output must also be in wide format
- When encountering complex multi-column tables, must completely preserve all columns and data
- **CRITICAL**: NEVER reorganize table columns or merge column headers into other columns
- **MANDATORY**: Each original column must remain a separate column in your markdown output
- **FORBIDDEN**: Do NOT consolidate multiple columns into fewer columns for "readability"

**ABSOLUTE TABLE EXTRACTION RULE**:
- **COPY EXACTLY AS IS**: Extract tables with 100% fidelity to the original PDF format
- **NO INFERENCE**: Do NOT try to guess missing headers or fix formatting issues
- **NO RESTRUCTURING**: Do NOT reorganize columns, merge cells, or change layout
- **PRESERVE IMPERFECTIONS**: If the original table has missing headers, empty columns, or formatting issues,
  keep them exactly as they appear in the PDF
- **COMPLETE DATA**: Extract every single data value, even if it seems to break table structure
- **ORIGINAL INTENT**: The goal is to create a digital copy, not an improved version
- **ROW COMPLETENESS**: Count the number of data rows in the original table and ensure your markdown output has EXACTLY the same number of rows
- **ANTI-TRUNCATION**: Never stop extracting rows in the middle - always extract ALL rows until the table ends

**CRITICAL WARNING**:
- If you see a table with 6 data columns but only 5 headers, DO NOT delete the 6th column
- If you see empty header cells (like "| |"), keep them exactly as empty
- If you see malformed table structure, preserve the malformation
- **ROW LOSS PREVENTION**: If a table has 5 data rows, your output MUST have 5 data rows - no exceptions
- **VERIFY ROW COUNT**: Before outputting, count the rows in your markdown table and ensure it matches the original
- Your job is to be a photocopier, not an editor

**SPECIAL CHARACTER PRESERVATION**:
- **MANDATORY**: Preserve ALL special characters, symbols, and Unicode characters exactly as they appear
- **Common symbols to preserve**: ✓ (checkmarks), ✗ (X marks), ± (plus-minus), → (arrows), ≈ (approximately), ≤ ≥ (inequality symbols)
- **Greek letters**: α, β, γ, δ, ε, ζ, η, θ, ι, κ, λ, μ, ν, ξ, ο, π, ρ, σ, τ, υ, φ, χ, ψ, ω, Α, Β, Γ, Δ, Ε, Ζ, Η, Θ, Ι, Κ, Λ, Μ, Ν, Ξ, Ο, Π, Ρ, Σ, Τ, Υ, Φ, Χ, Ψ, Ω
- **Mathematical symbols**: ∀, ∃, ∈, ∉, ∅, ∞, ∑, ∏, ∫, ∂, ∇, ⊕, ⊗, ⊥, ∥, ∠, ∴, ∵
- **NEVER** replace special characters with approximations (e.g., don't replace ✓ with "Yes" or θ with "theta")
- **NEVER** omit special characters thinking they are formatting artifacts
- If unsure about a character, ALWAYS include it in the output

Full paper text:
{full_text}

Please start extracting and return only JSON format results.
"""
