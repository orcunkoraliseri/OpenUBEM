"""Script to convert Markdown documents to publication-quality PDFs.
Uses Pandoc for Markdown-to-HTML conversion and headless Chrome for high-fidelity PDF rendering.
"""
import html
import os
import re
import subprocess
from pathlib import Path

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PANDOC_EXE = r"C:\Users\o_iseri\AppData\Local\Pandoc\pandoc.exe"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<!-- MathJax for KaTeX/LaTeX Math -->
<script>
window.MathJax = {{
  tex: {{
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
  }},
  svg: {{
    fontCache: 'global'
  }}
}};
</script>
<script type="text/javascript" id="MathJax-script" async
  src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js">
</script>

<!-- Mermaid JS for Flowcharts & Diagrams -->
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
mermaid.initialize({{
  startOnLoad: true,
  theme: 'neutral',
  securityLevel: 'loose',
  flowchart: {{
    useMaxWidth: true,
    htmlLabels: true,
    curve: 'basis'
  }}
}});
</script>

<style>
@page {{
  size: A4;
  margin: 16mm 14mm 16mm 14mm;
  @bottom-right {{
    content: "Page " counter(page);
    font-size: 8pt;
    color: #6e7781;
  }}
}}

*, *::before, *::after {{
  box-sizing: border-box;
}}

body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
  font-size: 9.5pt;
  line-height: 1.5;
  color: #1f2328;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
}}

h1, h2, h3, h4, h5, h6 {{
  color: #1f2328;
  font-weight: 600;
  margin-top: 1.4em;
  margin-bottom: 0.5em;
  page-break-after: avoid;
  break-after: avoid;
}}

h1 {{
  font-size: 17pt;
  border-bottom: 2px solid #0969da;
  padding-bottom: 0.25em;
  margin-top: 0.2em;
  color: #0969da;
}}

h2 {{
  font-size: 13pt;
  border-bottom: 1px solid #d0d7de;
  padding-bottom: 0.2em;
  margin-top: 1.3em;
}}

h3 {{
  font-size: 11pt;
  margin-top: 1.1em;
}}

h4 {{
  font-size: 10pt;
}}

p, ul, ol {{
  margin-top: 0.4em;
  margin-bottom: 0.7em;
}}

li {{
  margin-bottom: 0.25em;
}}

li > p {{
  margin-top: 0.2em;
  margin-bottom: 0.2em;
}}

hr {{
  border: 0;
  height: 1px;
  background-color: #d0d7de;
  margin: 1.5em 0;
}}

blockquote {{
  margin: 0.8em 0;
  padding: 0.4em 0.8em;
  color: #57606a;
  border-left: 3.5px solid #0969da;
  background-color: #f6f8fa;
  border-radius: 0 4px 4px 0;
}}

table {{
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
  font-size: 8.5pt;
  page-break-inside: avoid;
  break-inside: avoid;
}}

th, td {{
  border: 1px solid #d0d7de;
  padding: 5px 8px;
  vertical-align: top;
}}

th {{
  background-color: #f6f8fa;
  font-weight: 600;
  text-align: left;
}}

tr:nth-child(even) td {{
  background-color: #fcfcfc;
}}

code {{
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
  font-size: 8.5pt;
  background-color: #f6f8fa;
  padding: 0.15em 0.35em;
  border-radius: 4px;
  border: 1px solid #eaeef2;
}}

pre {{
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
  font-size: 8pt;
  background-color: #f6f8fa;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 8px 12px;
  overflow-x: auto;
  line-height: 1.4;
  page-break-inside: avoid;
  break-inside: avoid;
}}

pre code {{
  background-color: transparent;
  padding: 0;
  border: 0;
  font-size: inherit;
}}

.mermaid {{
  text-align: center;
  margin: 1.2em 0;
  background-color: #ffffff;
  page-break-inside: avoid;
  break-inside: avoid;
}}

.mermaid svg {{
  max-width: 100% !important;
  height: auto !important;
}}

mjx-container {{
  font-size: 105% !important;
}}

/* ASCII diagram boxes */
pre:has(code:contains("+--")) {{
  font-size: 7.5pt;
  line-height: 1.25;
}}
</style>
</head>
<body>
{body}
</body>
</html>
"""

def clean_mermaid_blocks(html_text: str) -> str:
    """Finds <pre class="mermaid"><code>...</code></pre> and cleans content for mermaid.js."""
    def replacer(match):
        raw_code = match.group(1)
        # Unescape HTML entities inside mermaid
        code_clean = html.unescape(raw_code)
        return f'<pre class="mermaid">\n{code_clean}\n</pre>'
    
    pattern = re.compile(r'<pre class="mermaid"><code>(.*?)</code></pre>', re.DOTALL)
    return pattern.sub(replacer, html_text)


def convert_md_to_pdf(md_path: Path, pdf_path: Path):
    print(f"[*] Processing: {md_path.name} -> {pdf_path.name}")
    
    # 1. Run Pandoc to get HTML fragment
    pandoc_cmd = [
        PANDOC_EXE,
        str(md_path),
        "-f", "markdown+pipe_tables+tex_math_dollars+fenced_code_blocks",
        "-t", "html",
        "--mathjax"
    ]
    res = subprocess.run(pandoc_cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"Pandoc failed: {res.stderr}")
    
    body_html = clean_mermaid_blocks(res.stdout)
    title = md_path.stem.replace("_", " ")
    
    full_html = HTML_TEMPLATE.format(title=title, body=body_html)
    
    temp_html_path = md_path.parent / f"{md_path.stem}_temp.html"
    temp_html_path.write_text(full_html, encoding="utf-8")
    
    try:
        # 2. Run Chrome headless to render HTML to PDF
        chrome_cmd = [
            CHROME_EXE,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=10000",
            f"--print-to-pdf={pdf_path.resolve()}",
            f"file:///{temp_html_path.resolve().as_posix()}"
        ]
        res_chrome = subprocess.run(chrome_cmd, capture_output=True, text=True)
        if not pdf_path.exists() or pdf_path.stat().st_size == 0:
            raise RuntimeError(f"Chrome PDF generation failed for {md_path.name}. Stderr: {res_chrome.stderr}")
        
        print(f"[+] Successfully generated: {pdf_path} ({pdf_path.stat().st_size / 1024:.1f} KB)")
    finally:
        if temp_html_path.exists():
            temp_html_path.unlink()


def main():
    target_dir = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations")
    files = [
        ("STATE_european_locations_v3.md", "STATE_european_locations_v3.pdf"),
        ("BRIEF_european_locations_v3.md", "BRIEF_european_locations_v3.pdf"),
        ("previous/STATE_european_locations_v2.md", "previous/STATE_european_locations_v2.pdf"),
        ("previous/MVP_european_locations.md", "previous/MVP_european_locations.pdf"),
        ("previous/WALKTHROUGH_european_locations.md", "previous/WALKTHROUGH_european_locations.pdf")
    ]
    
    for md_name, pdf_name in files:
        md_file = target_dir / md_name
        pdf_file = target_dir / pdf_name
        if not md_file.exists():
            print(f"[!] File not found: {md_file}")
            continue
        convert_md_to_pdf(md_file, pdf_file)


if __name__ == "__main__":
    main()
