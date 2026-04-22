import os
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

W, H = A4
MARGIN = 1.8 * cm
CONTENT_W = W - 2 * MARGIN

DARK_BLUE = colors.HexColor("#1F3864")
HEADER_BG = colors.HexColor("#2E5FA3")
ROW_ALT = colors.HexColor("#F2F7FC")
WHITE = colors.white


def _styles():
    return {
        "title": ParagraphStyle("title", fontSize=16, fontName="Helvetica-Bold",
                                textColor=WHITE, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle", fontSize=10, fontName="Helvetica",
                                   textColor=WHITE, alignment=TA_CENTER),
        "section": ParagraphStyle("section", fontSize=10, fontName="Helvetica-Bold",
                                  textColor=WHITE),
        "normal": ParagraphStyle("normal", fontSize=9, fontName="Helvetica",
                                 textColor=colors.black, leading=13),
        "bold": ParagraphStyle("bold", fontSize=9, fontName="Helvetica-Bold",
                               textColor=colors.black),
        "small": ParagraphStyle("small", fontSize=8, fontName="Helvetica",
                                textColor=colors.black, leading=11),
        "center": ParagraphStyle("center", fontSize=8, fontName="Helvetica",
                                 alignment=TA_CENTER, textColor=colors.black),
    }


def _section_header(title: str, s) -> Table:
    tbl = Table([[Paragraph(f"  {title}", s["section"])]], colWidths=[CONTENT_W])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HEADER_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def generate_weekly_pdf(reports: list, output_dir: str) -> str:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    saturday = monday + timedelta(days=5)

    filename = f"Laporan_Mingguan_OT_{monday.strftime('%d%m%y')}_{saturday.strftime('%d%m%y')}.pdf"
    filepath = os.path.join(output_dir, filename)

    s = _styles()
    story = []

    # ── Header ──────────────────────────────────────────
    period = f"{monday.strftime('%d/%m/%Y')} s/d {saturday.strftime('%d/%m/%Y')}"
    header_data = [
        [Paragraph("LAPORAN MINGGUAN", s["title"])],
        [Paragraph("Divisi Operational Technology Engineer", s["subtitle"])],
        [Paragraph(f"Periode: {period}", s["subtitle"])],
    ]
    header_tbl = Table(header_data, colWidths=[CONTENT_W])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── Rekap per Hari ──────────────────────────────────
    story.append(_section_header("REKAP KEGIATAN MINGGUAN", s))
    story.append(Spacer(1, 0.15 * cm))

    headers = [
        Paragraph("Tanggal", s["bold"]),
        Paragraph("Hari", s["bold"]),
        Paragraph("PIC", s["bold"]),
        Paragraph("Ringkasan Kegiatan", s["bold"]),
        Paragraph("Kendala", s["bold"]),
        Paragraph("Rencana Besok", s["bold"]),
    ]
    cw = [
        CONTENT_W * 0.12, CONTENT_W * 0.10, CONTENT_W * 0.14,
        CONTENT_W * 0.28, CONTENT_W * 0.18, CONTENT_W * 0.18,
    ]
    rows = [headers]

    for i, r in enumerate(reports):
        ringkasan = "\n".join(f"• {x}" for x in r.get("ringkasan", []))
        kendala = "\n".join(
            f"{j+1}. {k.get('kendala', '')}" for j, k in enumerate(r.get("kendala", []))
        ) or "-"
        rencana = "\n".join(
            f"{j+1}. {rn.get('rencana', '')}" for j, rn in enumerate(r.get("rencana_besok", []))
        ) or "-"

        d = date.fromisoformat(r["tanggal"])
        rows.append([
            Paragraph(d.strftime("%d/%m/%Y"), s["small"]),
            Paragraph(r.get("hari", ""), s["small"]),
            Paragraph(r.get("nama_pic", ""), s["small"]),
            Paragraph(ringkasan or "-", s["small"]),
            Paragraph(kendala, s["small"]),
            Paragraph(rencana, s["small"]),
        ])

    if len(rows) == 1:
        rows.append([Paragraph("Belum ada laporan minggu ini", s["small"])] + [""] * 5)

    tbl = Table(rows, colWidths=cw)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(rows)):
        bg = ROW_ALT if (i - 1) % 2 == 0 else WHITE
        style.append(("BACKGROUND", (0, i), (-1, i), bg))
    tbl.setStyle(TableStyle(style))
    story.append(tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── Ringkasan Statistik ─────────────────────────────
    story.append(_section_header("STATISTIK MINGGU INI", s))
    story.append(Spacer(1, 0.15 * cm))

    total_kegiatan = sum(len(r.get("detail_kegiatan", [])) for r in reports)
    total_kendala = sum(len(r.get("kendala", [])) for r in reports)
    total_hari = len(reports)

    stat_rows = [
        [Paragraph("Total Hari Laporan", s["bold"]), Paragraph(str(total_hari), s["normal"])],
        [Paragraph("Total Kegiatan", s["bold"]), Paragraph(str(total_kegiatan), s["normal"])],
        [Paragraph("Total Kendala", s["bold"]), Paragraph(str(total_kendala), s["normal"])],
    ]
    stat_tbl = Table(stat_rows, colWidths=[CONTENT_W * 0.4, CONTENT_W * 0.6])
    stat_tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#BDD7EE")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(stat_tbl)

    def make_canvas(filename, **kwargs):
        from reports.daily_pdf import _FooterCanvas as FC

        class WeeklyCanvas(FC):
            def _draw_footer(self, page_num, total):
                from reportlab.lib.pagesizes import A4
                c = self._canvas
                c.saveState()
                c.setFont("Helvetica", 7.5)
                c.setFillColor(colors.HexColor("#666666"))
                text = f"Laporan Mingguan - Divisi Operational Technology | PT. Global Papua Abadi      Hal. {page_num} / {total}"
                c.drawCentredString(W / 2, 1.1 * cm, text)
                c.restoreState()

        return WeeklyCanvas(filename, **kwargs)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=1.8 * cm,
    )
    doc.build(story, canvasmaker=make_canvas)
    return filepath
