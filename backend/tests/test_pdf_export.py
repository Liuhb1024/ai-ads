import unittest

from app.pdf_export import render_markdown_pdf


class PdfExportTests(unittest.TestCase):
    def test_renders_pdf_bytes_with_cjk_content(self):
        pdf = render_markdown_pdf(
            "# 广告创意研究报告\n\n> 可信度评分：88/100\n\n| 证据 | 内容 |\n|---|---|\n| E001 | 出现产品 |"
        )
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1000)


if __name__ == "__main__":
    unittest.main()
