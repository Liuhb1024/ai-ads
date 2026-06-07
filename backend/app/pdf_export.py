from __future__ import annotations


PRINT_CSS = """
@page {
  size: A4;
  margin: 18mm 17mm 20mm;
  @top-left {
    content: "AI-AD / EVIDENCE DESK";
    color: #9f3428;
    font-size: 8pt;
    letter-spacing: 0.12em;
  }
  @bottom-right {
    content: counter(page) " / " counter(pages);
    color: #776f65;
    font-size: 8pt;
  }
}
html { color: #211e1a; background: #f4f0e8; }
body {
  font-family: "Songti SC", "STSong", "STHeiti", "PingFang SC", serif;
  font-size: 10.5pt;
  line-height: 1.78;
  background: #fffdf8;
}
h1, h2, h3 { color: #211e1a; font-weight: 600; page-break-after: avoid; }
h1 {
  margin: 0 0 18mm;
  padding: 17mm 0 8mm;
  border-bottom: 1.5pt solid #211e1a;
  font-size: 26pt;
  line-height: 1.25;
  letter-spacing: -0.03em;
}
h2 {
  margin: 11mm 0 4mm;
  padding-top: 3mm;
  border-top: 0.8pt solid #cfc5b7;
  color: #9f3428;
  font-size: 16pt;
}
h3 { margin: 7mm 0 2mm; font-size: 12pt; }
p { margin: 0 0 3.5mm; orphans: 3; widows: 3; }
blockquote {
  margin: 6mm 0;
  padding: 4mm 5mm;
  border-left: 3pt solid #b33b2d;
  background: #f5eee4;
  color: #504940;
}
table {
  width: 100%;
  margin: 4mm 0 7mm;
  border-collapse: collapse;
  font-size: 8.5pt;
  page-break-inside: auto;
}
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th {
  padding: 2.5mm;
  background: #27231f;
  color: #fffdf8;
  text-align: left;
}
td { padding: 2.5mm; border-bottom: 0.5pt solid #d9d0c4; vertical-align: top; }
tbody tr:nth-child(even) { background: #f8f4ed; }
code {
  padding: 0.5mm 1.2mm;
  border-radius: 1mm;
  background: #eee7dc;
  color: #8f2d23;
  font-family: "SFMono-Regular", monospace;
  font-size: 8.5pt;
}
hr { margin: 8mm 0; border: 0; border-top: 0.8pt solid #cfc5b7; }
li { margin-bottom: 1.6mm; }
strong { color: #161310; }
"""


def render_markdown_pdf(markdown_content: str) -> bytes:
    try:
        import markdown as markdown_lib
        from weasyprint import CSS, HTML
    except ImportError as exc:
        raise RuntimeError("PDF 渲染依赖未安装，请安装 Markdown 与 WeasyPrint") from exc

    body = markdown_lib.markdown(
        markdown_content,
        extensions=["extra", "sane_lists", "tables"],
        output_format="html5",
    )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>AI-AD 广告创意研究报告</title>
</head>
<body>{body}</body>
</html>"""
    return HTML(string=html).write_pdf(stylesheets=[CSS(string=PRINT_CSS)])
