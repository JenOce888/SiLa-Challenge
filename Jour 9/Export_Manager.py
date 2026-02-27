import csv
from database import Database


class ExportManager:
    def __init__(self, db: Database):
        self.db = db

    def to_csv(self, path: str):
        tasks = self.db.get_all_tasks()
        if not tasks:
            return

        fieldnames = ["id", "title", "description", "status", "priority", "tags", "due_date", "created_at", "updated_at"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for task in tasks:
                writer.writerow({k: task.get(k, "") for k in fieldnames})

    def to_pdf(self, path: str):
        """
        Generates a PDF using reportlab if available.
        Falls back to a styled HTML file otherwise.
        """
        tasks = self.db.get_all_tasks()

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.units import cm

            doc = SimpleDocTemplate(path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            elements = []

            title_style = ParagraphStyle(
                'Title', fontSize=18, spaceAfter=12,
                textColor=colors.HexColor('#1a1a2e'), fontName='Helvetica-Bold'
            )
            elements.append(Paragraph("Task Manager — Export", title_style))
            elements.append(Spacer(1, 0.5*cm))

            data = [["#", "Title", "Status", "Priority", "Tags", "Due Date"]]
            for t in tasks:
                data.append([
                    str(t["id"]),
                    t["title"][:40],
                    t["status"],
                    t["priority"],
                    (t["tags"] or "")[:30],
                    t.get("due_date") or "-"
                ])

            table = Table(data, colWidths=[1*cm, 6*cm, 3*cm, 3*cm, 4*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#89b4fa')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e1e2e')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f5f5f5'), colors.white]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
            doc.build(elements)

        except ImportError:
            # Fallback: generate a styled HTML file
            html_path = path.replace(".pdf", "_export.html")
            self._to_html(html_path, tasks)
            import shutil
            shutil.copy(html_path, path)

    def _to_html(self, path: str, tasks: list):
        rows = ""
        for t in tasks:
            priority_color = {
                "High": "#f38ba8",
                "Medium": "#fab387",
                "Low": "#a6e3a1"
            }.get(t["priority"], "#ccc")

            rows += f"""
            <tr>
                <td>{t['id']}</td>
                <td><b>{t['title']}</b><br><small style='color:#888'>{t.get('description','')[:60]}</small></td>
                <td>{t['status']}</td>
                <td><span style='background:{priority_color};padding:2px 8px;border-radius:4px;font-size:12px'>{t['priority']}</span></td>
                <td>{t.get('tags','')}</td>
                <td>{t.get('due_date') or '-'}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'>
<title>Task Export</title>
<style>
  body {{ font-family: Arial; background: #f0f0f0; padding: 20px; }}
  h1 {{ color: #1a1a2e; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }}
  th {{ background: #89b4fa; color: #1e1e2e; padding: 10px; text-align: left; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #eee; font-size: 13px; }}
  tr:hover {{ background: #f9f9f9; }}
</style></head>
<body>
  <h1>Task Manager — Export</h1>
  <table>
    <tr><th>#</th><th>Title</th><th>Status</th><th>Priority</th><th>Tags</th><th>Due Date</th></tr>
    {rows}
  </table>
</body></html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
