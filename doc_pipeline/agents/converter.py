"""Agent 4: 格式转换 — pptx→md, docx→pdf, ipynb→py。"""
import html
import os
import time

from utils import iter_ipynb_cells, iter_pptx_content, save_manifest, setup_logging


class ConverterAgent:
    def __init__(self, output_dir, formats=None):
        self.output_dir = output_dir
        self.formats = formats or ["md", "pdf", "py"]
        self.logger = setup_logging(output_dir)
        self.convert_dir = os.path.join(output_dir, "converted")
        os.makedirs(self.convert_dir, exist_ok=True)

    def run(self, manifest):
        self.logger.info("=" * 50)
        self.logger.info("[CONVERTER] 开始格式转换: %s", ", ".join(self.formats))
        t0 = time.time()
        converted = 0

        for f in manifest.get("files", []):
            if f.get("is_duplicate"):
                continue
            f.setdefault("conversions", [])
            if "md" in self.formats and f["ext"] == ".pptx":
                result = self._pptx_to_md(f)
                if result:
                    f["conversions"].append(result)
                    converted += 1
            if "pdf" in self.formats and f["ext"] == ".docx":
                result = self._docx_to_pdf(f)
                if result:
                    f["conversions"].append(result)
                    converted += 1
            if "py" in self.formats and f["ext"] == ".ipynb":
                result = self._ipynb_to_py(f)
                if result:
                    f["conversions"].append(result)
                    converted += 1

        manifest["files"] = manifest.get("files", [])
        manifest["stats"]["conversions"] = converted
        save_manifest(manifest, self.output_dir)
        manifest["stats"]["converter_time"] = round(time.time() - t0, 2)
        self.logger.info("[CONVERTER] 完成 — %d 次转换", converted)
        return manifest

    def _pptx_to_md(self, f):
        try:
            base = os.path.splitext(f["filename"])[0]
            out_path = os.path.join(self.convert_dir, base + ".md")
            lines = [f"# {base}\n"]
            for i, paragraphs, table_rows in iter_pptx_content(f["path"]):
                lines.append(f"## Slide {i}\n")
                for t in paragraphs:
                    lines.append(t)
                if table_rows:
                    lines.append("")
                    for row in table_rows:
                        lines.append("| " + " | ".join(row) + " |")
                    lines.append("")
                lines.append("---\n")
            with open(out_path, "w", encoding="utf-8") as fout:
                fout.write("\n".join(lines))
            return {"format": "md", "output_path": out_path, "ok": True}
        except Exception as e:
            self.logger.warning("[CONVERTER] pptx→md FAIL: %s — %s", f["filename"], e)
            return {"format": "md", "output_path": None, "ok": False, "error": str(e)}

    def _docx_to_pdf(self, f):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Paragraph
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            font_registered = False
            for font_path in [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simsun.ttc",
                "C:/Windows/Fonts/simhei.ttf",
            ]:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
                        font_registered = True
                        break
                    except Exception:
                        continue

            base = os.path.splitext(f["filename"])[0]
            out_path = os.path.join(self.convert_dir, base + ".pdf")
            text = f.get("text_content", "") or ""
            lines = [l for l in text.split("\n") if l.strip()]
            if len(lines) > 500:
                self.logger.warning("[CONVERTER] 截断: %s (%d → 500 行)", f["filename"], len(lines))

            doc = SimpleDocTemplate(out_path, pagesize=A4,
                                    leftMargin=20 * mm, rightMargin=20 * mm,
                                    topMargin=15 * mm, bottomMargin=15 * mm)
            styles = getSampleStyleSheet()
            style = styles["Normal"]
            if font_registered:
                style.fontName = "ChineseFont"
            style.fontSize = 10
            style.leading = 14

            story = [Paragraph(html.escape(line), style) for line in lines[:500]]
            doc.build(story)
            return {"format": "pdf", "output_path": out_path, "ok": True}
        except Exception as e:
            self.logger.warning("[CONVERTER] docx→pdf FAIL: %s — %s", f["filename"], e)
            return {"format": "pdf", "output_path": None, "ok": False, "error": str(e)}

    def _ipynb_to_py(self, f):
        try:
            base = os.path.splitext(f["filename"])[0]
            out_path = os.path.join(self.convert_dir, base + ".py")
            lines = [f"# Converted from: {f['filename']}", ""]
            for i, cell_type, source in iter_ipynb_cells(f["path"]):
                if cell_type == "code":
                    lines.append(f"# In[{i + 1}]:")
                    lines.append(source)
                    lines.append("")
                elif cell_type == "markdown":
                    for ln in source.split("\n"):
                        lines.append(f"# {ln}")
                    lines.append("")
            with open(out_path, "w", encoding="utf-8") as fout:
                fout.write("\n".join(lines))
            return {"format": "py", "output_path": out_path, "ok": True}
        except Exception as e:
            self.logger.warning("[CONVERTER] ipynb→py FAIL: %s — %s", f["filename"], e)
            return {"format": "py", "output_path": None, "ok": False, "error": str(e)}
