"""
TEX Code Generation Prompts (tex_generator.py)
"""

# Generate LaTeX Beamer code
TEX_GENERATION_PROMPT = r"""
You are a LaTeX Beamer expert. Your task is to generate a complete, professional, and directly compilable Beamer presentation based on a JSON-formatted presentation plan. {language_prompt}.

**Input**:
You will receive a JSON object named `plan` containing the structure and content of the entire presentation.

**Task**:
Please strictly follow the content of `plan` and generate complete LaTeX Beamer code using the `{theme}` theme.

**🎯 SMART CONTENT LAYOUT RULES 🎯**:

**FIGURE-TABLE SEPARATION RULE**: When `includes_figure: true` AND `includes_table: true` in the SAME slide:
1. **CREATE FRAME 1**: `\\frametitle{{Title}}` + content + table ONLY
2. **CREATE FRAME 2**: `\\frametitle{{Title}}` + figure ONLY (no content text)
3. **RATIONALE**: Tables and figures together cause layout issues

**FIGURE-TEXT INTEGRATION RULE**: When ONLY `includes_figure: true` (no table):
- **PREFERRED**: `\\frametitle{{Title}}` + content + figure in SAME frame
- **LAYOUT**: Use two-column or figure placement that complements the text
- **BENEFIT**: Better content flow and space utilization

**Core Instructions**:

1.  **Document Header**:
    *   Use `\documentclass[10pt]{{beamer}}`.
    *   Import necessary packages: `graphicx`, `booktabs`, `adjustbox`, `multirow`, `utf8` (if needed), `ctex` (if Chinese).
    *   **MANDATORY for special characters**: Include `\usepackage[utf8]{{inputenc}}` and `\usepackage{{textcomp}}` and `\usepackage{{amssymb}}` for proper Unicode and symbol support.
    *   **MANDATORY for captions**: Include `\usepackage{{caption}}` to support `\captionof` commands in beamer frames.
    *   Set Beamer theme: `\usetheme{{{theme}}}`.
    *   Define title, author, institution, and date, which can be obtained from `plan.paper_info`.
    *   **CRITICAL for footer display**: If title or author is too long, create shortened versions for footer using `\title[Short Title]{{Full Title}}` and `\author[First Author et al.]{{Full Author List}}` format.

2.  **Title Page**:
    *   Use `\frame{{\titlepage}}` at the beginning of the document to create the title page.

3.  **Table of Contents**:
    *   After the title page, use `\frame{{\\frametitle{{Outline}} \tableofcontents}}` to create the table of contents.

4.  **Content Slides (Frames)**:
    *   Iterate through each slide object in `plan.slides_plan`.
    *   Create a `\begin{{frame}}` environment for each object.
    *   Use the slide object's `title` field to set `\frametitle`.

5.  **Content Rendering**:
    *   **Text**: Render each string in the `content` array as `\item`. Wrap them in `\begin{{itemize}}` ... `\end{{itemize}}`.
    *   **DYNAMIC SPACING OPTIMIZATION**: Use adaptive spacing based on content and slide elements:
        - **Text-only slides**: `\setlength{{\\itemsep}}{{0.6em}}` for comfortable reading
        - **Slides with figures**: `\setlength{{\\itemsep}}{{0.4em}}` to save space
        - **Slides with tables**: `\setlength{{\\itemsep}}{{0.3em}}` for maximum space efficiency
        - **High-density slides** (>4 items + figure/table): `\setlength{{\\itemsep}}{{0.2em}}`
    *   **Figures**: If `includes_figure` is `true`, use information from `figure_reference` to create a `figure` environment.
        *   Image path comes from `figure_reference.path`.
        *   Image caption comes from `figure_reference.caption`.
        *   **LAYOUT STRATEGY** (when no table is present):
            - **INTEGRATED LAYOUT**: Place content and figure in the SAME frame for better flow
            - **TWO-COLUMN APPROACH**: Use `\begin{{columns}}` environment for side-by-side layout when appropriate
            - **BOTTOM PLACEMENT**: Place figure below content when vertical space allows
        *   **ADAPTIVE IMAGE SIZING WITH OVERFLOW PROTECTION**: Use intelligent image sizing based on TOTAL content density and caption length:
            - **High content slides** (>4 total items including sub-bullets): `width=0.6\textwidth, height=0.25\textheight, keepaspectratio`
            - **Medium content slides** (3-4 total items): `width=0.65\textwidth, height=0.3\textheight, keepaspectratio`
            - **Low content slides** (≤2 total items): `width=0.7\textwidth, height=0.4\textheight, keepaspectratio`
            - **CAPTION LENGTH FACTOR**: If caption >40 characters, reduce height by 0.05\textheight
            - **CRITICAL**: Count ALL bullet points including nested sub-items when determining content density
            - **SAFETY MARGIN**: Always reserve bottom 0.15\textheight for caption + safe layout
    *   **Tables**: If `includes_table` is `true`: Convert the content of `table_reference.markdown_content` to LaTeX tables.
        *   **Conversion Logic**:
            1.  Create a `\begin{{table}}` environment within `\begin{{frame}}`.
            2.  Place `\centering` immediately after `\begin{{table}}`.
            3.  Place `\caption{{...}}` with content from `table_reference.caption` after `\centering` but before tabular.

            4.  To ensure appropriate table size, wrap the `tabular` environment with `\begin{{adjustbox}}{{width=\\textwidth,center}}`.
            5.  Close with `\end{{adjustbox}}` and `\end{{table}}`.
            6.  **CRITICAL TABLE STRUCTURE PRESERVATION**:
                *   **MANDATORY**: Convert the `markdown_content` EXACTLY as provided, preserving ALL rows, columns, and structure
                *   **ROW-BY-ROW CONVERSION**: Process each markdown table row individually and convert to LaTeX format
                *   **NO OMISSIONS**: Every single row from the markdown table MUST appear in the LaTeX output
                *   **ROW COUNT VERIFICATION**: Count the data rows in the markdown input and ensure your LaTeX output has EXACTLY the same number of data rows
                *   **ANTI-TRUNCATION**: Never stop processing rows - continue until ALL markdown rows are converted to LaTeX
                *   **HEADER STRUCTURE**: If the markdown has multiple header rows or grouped headers, preserve them using appropriate LaTeX commands like `\multicolumn` and `\multirow`
                *   **COLUMN COUNT**: Count total columns from the markdown and ensure LaTeX `tabular` has the same number of columns
                *   **DATA INTEGRITY**: Every cell's content must be preserved in its exact position
                *   **SEPARATOR LINES**: Convert markdown separator lines (`|---|---|`) to appropriate LaTeX rules (`\midrule`, `\cmidrule`)
                *   Use `\toprule`, `\midrule`, `\bottomrule` for professional appearance
                *   Column definitions: `{{l|c|c|...}}` where first column is left-aligned, others center-aligned
        *   **TABLE FORMATTING ENHANCEMENTS**:
            1.  **Bold Headers**: Make all table headers bold using `\textbf{{header}}` format.
            2.  **Special Characters**: Apply character conversion rules to table content (e.g., θ → `$\theta$`, φ → `$\phi$`, ↑ → `$\uparrow$`, ↓ → `$\downarrow$`).
            3.  **ADAPTIVE TABLE SPACING**: Use responsive spacing based on table size:
               - **Small tables** (<5 rows): `\\renewcommand{{\\arraystretch}}{{1.3}}` for readability
               - **Medium tables** (5-8 rows): `\\renewcommand{{\\arraystretch}}{{1.15}}` for balance
               - **Large tables** (>8 rows): `\\renewcommand{{\\arraystretch}}{{1.05}}` + `\\footnotesize` for compactness
            4.  **Column Group Headers**: For tables with grouped columns (like multiple datasets), use `\multicolumn{{3}}{{c|}}{{Dataset Name}}` to span multiple columns for group headers.
            5.  **Smart Performance Highlighting**:
               - For metrics with ↑ (higher is better): bold the highest value in each column
               - For metrics with ↓ (lower is better): bold the lowest value in each column
               - Do NOT automatically bold all "Ours" values - analyze each metric independently
            6.  **Centering**: Ensure proper centering with both `\centering` and adjustbox wrapper.
    *   **Formulas/Code**: If `includes_equation` or `includes_code` is `true`, properly place the corresponding content in mathematical environments or code listing environments.

3.4. **FIGURE-TEXT LAYOUT GUIDELINES**:
    **PREFERRED: Vertical Layout** (use this for ALL figure slides unless content is very lengthy):
    ```
    [Content items here]
    \\vspace{{0.2em}}
    \\begin{{figure}}
    \\centering
    \\includegraphics[width=0.7\\textwidth, height=0.4\\textheight, keepaspectratio]{{images/figure.jpg}}
    \\caption{{Caption text}}
    \\end{{figure}}
    ```

    **ALTERNATIVE: Two Column Layout** (ONLY when content is very lengthy and cannot fit with figure):
    ```
    \\begin{{columns}}
    \\begin{{column}}{{0.55\\textwidth}}
    [Content items here]
    \\end{{column}}
    \\begin{{column}}{{0.45\\textwidth}}
    \\begin{{figure}}
    \\centering
    \\includegraphics[width=\\textwidth]{{images/figure.jpg}}
    \\caption{{Caption text}}
    \\end{{figure}}
    \\end{{column}}
    \\end{{columns}}
    ```

    **OPTION 3 - Safe Layout** (for high content + figure):
    ```
    [Limited content items - max 3 points]
    \\vspace{{0.2em}}
    \\begin{{figure}}
    \\centering
    \\includegraphics[width=0.6\\textwidth, height=0.3\\textheight, keepaspectratio]{{images/figure.jpg}}
    \\caption{{Caption text}}
    \\end{{figure}}
    ```

3.5. **Section Grouping**:
    *   If each object in `plan.slides_plan` contains a `section` field, insert `\\section{{<section>}}` once when sections change; multiple slides under the same section do not need repeated insertion.

**CONTENT OVERFLOW PREVENTION STRATEGIES**:
*   **Automatic Size Adjustment**: For content-heavy slides, automatically apply:
    - Smaller image dimensions (0.65x instead of 0.8x textwidth, max height 0.35textheight)
    - Reduced itemsep (0.3em instead of 0.5em)
    - Compact table formatting with \\footnotesize when needed
*   **Figure Overflow Detection**: If a slide has >4 content items + figure + caption:
    - **Option 1**: Use minimal figure size (width=0.5\\textwidth, height=0.25\\textheight)
    - **Option 2**: Split into separate slides: content slide + dedicated figure slide
    - **Choose Option 2** if the figure is complex or central to understanding
    - **MANDATORY**: If total estimated content height > 0.8\\textheight, automatically choose Option 2
*   **Smart Layout Decisions**:
    - If slide has >4 bullets + figure: Use smaller figure size
    - If slide has table + >3 bullets: Consider reducing bullet text or using \\small font
    - If caption is long (>10 words): Use concise version
*   **Emergency Measures**: For extremely dense content:
    - Apply \\small font size to entire slide content
    - Use \\setlength{{\\itemsep}}{{0.2em}} for minimal spacing
    - Consider splitting content across two slides with clear continuation

**Output Requirements**:
*   Output only complete, directly compilable LaTeX code.
*   Do not include any explanations, comments, or Markdown formatting.
*   Ensure code cleanliness and professionalism.
*   **MANDATORY**: Prevent content overflow by intelligently adapting sizing and spacing based on content density.

**TITLE AND AUTHOR TRUNCATION RULES**:
*   **Title Truncation**: If title exceeds 40 characters, create short version:
    - Keep first meaningful part + "..."
    - Example: `\title[Neural Radiance Fields...]{{NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis}}`
*   **Author Truncation**: If author list has more than 3 authors, use "et al." format:
    - Keep first author + "et al."
    - Example: `\author[Mildenhall et al.]{{Ben Mildenhall, Pratul P. Srinivasan, Matthew Tancik, Jonathan T. Barron, Ravi Ramamoorthi, Ren Ng}}`
*   **Institute Truncation**: If institution list is too long, use primary institution:
    - Example: `\institute[UC Berkeley]{{UC Berkeley, Google Research, UC San Diego}}`
*   **Purpose**: Ensure footer displays properly while keeping title page complete

**SPECIAL CHARACTER HANDLING**:
*   **Unicode Characters**: For Greek letters like θ (theta), φ (phi), use LaTeX math mode: `$\theta$`, `$\phi$`, etc.
*   **Checkmarks and Symbols**: For ✓ use `\checkmark` (requires amssymb package), for ✗ use `\times`
*   **Mathematical Symbols**: Use appropriate LaTeX commands: `\pm` for ±, `\approx` for ≈, `\leq` for ≤, `\geq` for ≥
*   **When in doubt**: Wrap Unicode characters in math mode: `$character$`
*   **Character Conversion Map**:
    - ✓ → `\checkmark` or `$\checkmark$`
    - ✗ → `$\times$`
    - θ → `$\theta$`
    - φ → `$\phi$` or `$\varphi$`
    - α → `$\alpha$`, β → `$\beta$`, γ → `$\gamma$`, etc.
    - ± → `$\pm$`
    - ≈ → `$\approx$`
    - ≤ → `$\leq$`, ≥ → `$\geq$`
    - → → `$\rightarrow$`
    - ↑ → `$\uparrow$` (commonly used in tables for "higher is better")
    - ↓ → `$\downarrow$` (commonly used in tables for "lower is better")
    - ← → `$\leftarrow$`, ↔ → `$\leftrightarrow$`

**TABLE EXAMPLE with Group Headers and Smart Highlighting**:
For a comparison table with multiple datasets, structure it like this:
```latex
\\begin{{tabular}}{{l|c|c|c|c|c|c|c|c|c}}
\\toprule
\\multirow{{2}}{{*}}{{Method}} & \\multicolumn{{3}}{{c|}}{{Dataset A}} & \\multicolumn{{3}}{{c|}}{{Dataset B}} & \\multicolumn{{3}}{{c}}{{Dataset C}} \\\\
\\cmidrule(lr){{2-4}} \\cmidrule(lr){{5-7}} \\cmidrule(lr){{8-10}}
& PSNR$\\uparrow$ & SSIM$\\uparrow$ & LPIPS$\\downarrow$ & PSNR$\\uparrow$ & SSIM$\\uparrow$ & LPIPS$\\downarrow$ & PSNR$\\uparrow$ & SSIM$\\uparrow$ & LPIPS$\\downarrow$ \\\\
\\midrule
Method 1 & 33.20 & 0.963 & 0.073 & 22.26 & 0.846 & 0.170 & 22.84 & 0.668 & 0.378 \\\\
Method 2 & 29.62 & 0.929 & 0.099 & 26.05 & 0.893 & 0.160 & - & - & - \\\\
Ours & \\textbf{{40.15}} & \\textbf{{0.991}} & \\textbf{{0.023}} & \\textbf{{31.01}} & \\textbf{{0.947}} & \\textbf{{0.081}} & \\textbf{{26.50}} & \\textbf{{0.811}} & 0.250 \\\\
Best Method & 34.38 & 0.985 & 0.048 & 24.88 & 0.911 & 0.114 & 24.13 & 0.798 & \\textbf{{0.212}} \\\\
\\bottomrule
\\end{{tabular}}
```
**Note**: In the above example, bold values represent the best performance for each metric in each dataset column.

**Presentation Plan (JSON)**:
```json
{plan}
```

Please start generating code now.
"""
