"""Build technical-report.html and technical-report.pdf from technical-report.md.
Usage: python3 build_report.py   (needs the `markdown` package and Google Chrome for the PDF step)."""
import pathlib, re, subprocess, markdown

here = pathlib.Path(__file__).parent
src = (here / "technical-report.md").read_text()
src = re.sub(r"^---\n.*?\n---\n", "", src, count=1, flags=re.S)          # drop the metadata block
for fig in (here / "figures").glob("*.svg"):                                   # inline figures: {{figure:name}}
    src = src.replace("{{figure:" + fig.stem + "}}", "<div style=\"text-align:center;margin:8pt 0 2pt 0\">" + fig.read_text() + "</div>")
body = markdown.markdown(src, extensions=["tables", "smarty"])
CSS = """
@page { size: A4; margin: 22mm 20mm 24mm 20mm; }
body { font-family: "Charter", "Georgia", "Times New Roman", serif; font-size: 10.6pt; line-height: 1.42; color: #111;
       max-width: 168mm; margin: 0 auto; padding: 0 4mm; }
h1 { font-size: 17pt; line-height: 1.25; margin: 0 0 6pt 0; font-weight: 700; }
h2 { font-size: 12.5pt; margin: 18pt 0 6pt 0; border-bottom: 0.6pt solid #999; padding-bottom: 2pt; }
h3 { font-size: 11pt; margin: 12pt 0 4pt 0; }
p { margin: 0 0 7pt 0; text-align: justify; hyphens: auto; }
table { border-collapse: collapse; margin: 6pt auto 4pt auto; font-size: 9.3pt; width: 100%; }
th, td { border-top: 0.5pt solid #444; border-bottom: 0.5pt solid #444; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #f1f1f1; }
table + p { font-size: 9.3pt; color: #333; margin-top: 0; }
ul { margin: 0 0 7pt 18pt; padding: 0; } li { margin-bottom: 3pt; }
code { font-family: "Menlo", monospace; font-size: 9pt; }
strong { font-weight: 700; }
"""
html = f"<!doctype html><html><head><meta charset='utf-8'><title>Technical report</title><style>{CSS}</style></head><body>{body}</body></html>"
(here / "technical-report.html").write_text(html)
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={here / 'technical-report.pdf'}", str(here / "technical-report.html")],
               check=True, capture_output=True)
print("built", here / "technical-report.html", here / "technical-report.pdf")
