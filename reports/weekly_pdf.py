import os
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

W, H = A4
MARGIN = 1.8 * cm
CONTENT_W = W - 2 * MARGIN

DARK_BLUE = colors.HexColor("#1F3864")
HEADER_BG = colors.HexColor("#2E5FA3")
LIGHT_BLUE = colors.HexColor("#BDD7EE")
ROW_ALT = colors.HexColor("#F2F7FC")
WHITE = colors.white
BLACK = colors.black


def _styles():
    return {
        "title": ParagraphStyle("title", fontSize=16, fontName="Helvetica-Bold",
                                textColor=WHITE, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle", fontSize=10, fontName="Helvetica",
                                   textColor=WHITE, alignment=TA_CENTER),
        "section": ParagraphStyle("section", fontSize=10, fontName="Helvetica-Bold",
                                  textColor=WHITE),
        "normal": ParagraphStyle("normal", fontSize=9, fontName="Helvetica",
                                 textColor=BLACK, leading=13),
        "bold": ParagraphStyle("bold", fontSize=9, fontName="Helvetica-Bold",
                               textColor=BLACK),
        "small": ParagraphStyle("small", fontSize=8, fontName="Helvetica",
                                textColor=BLACK, leading=12),
        "small_bold": ParagraphStyle("small_bold", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=BLACK, leading=12),
        "center": ParagraphStyle("center", fontSize=8, fontName="Helvetica",
                                 alignment=TA_CENTER, textColor=BLACK),
        "center_bold": ParagraphStyle("center_bold", fontSize=8, fontName="Helvetica-Bold",
                                      alignment=TA_CENTER, textColor=BLACK),
        "sign": ParagraphStyle("sign", fontSize=9, fontName="Helvetica",
                               alignment=TA_CENTER, textColor=BLACK, leading=14),
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

    # ── 1. Rekap per Hari ───────────────────────────────
    story.append(_section_header("1. REKAP KEGIATAN MINGGUAN", s))
    story.append(Spacer(1, 0.15 * cm))

    headers = [
        Paragraph("Tanggal", s["small_bold"]),
        Paragraph("Hari", s["small_bold"]),
        Paragraph("PIC", s["small_bold"]),
        Paragraph("Ringkasan Kegiatan", s["small_bold"]),
        Paragraph("Kendala", s["small_bold"]),
        Paragraph("Rencana Besok", s["small_bold"]),
    ]
    cw = [
        CONTENT_W * 0.12, CONTENT_W * 0.09, CONTENT_W * 0.13,
        CONTENT_W * 0.28, CONTENT_W * 0.19, CONTENT_W * 0.19,
    ]
    rows = [headers]

    for r in reports:
        # Gunakan <br/> agar bullet tampil vertikal ke bawah
        ringkasan = "<br/>".join(f"• {x}" for x in r.get("ringkasan", [])) or "-"
        kendala_list = r.get("kendala", [])
        kendala = "<br/>".join(
            f"{j+1}. {k.get('kendala', '')}" for j, k in enumerate(kendala_list)
        ) or "-"
        rencana = "<br/>".join(
            f"{j+1}. {rn.get('rencana', '')}" for j, rn in enumerate(r.get("rencana_besok", []))
        ) or "-"

        d = date.fromisoformat(r["tanggal"])
        rows.append([
            Paragraph(d.strftime("%d/%m/%Y"), s["small"]),
            Paragraph(r.get("hari", ""), s["small"]),
            Paragraph(r.get("nama_pic", ""), s["small"]),
            Paragraph(ringkasan, s["small"]),
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

    # ── 2. Rekap Kendala Aktif ──────────────────────────
    story.append(_section_header("2. REKAP KENDALA AKTIF MINGGU INI", s))
    story.append(Spacer(1, 0.15 * cm))

    all_kendala = []
    for r in reports:
        d = date.fromisoformat(r["tanggal"])
        for k in r.get("kendala", []):
            all_kendala.append((d.strftime("%d/%m/%Y"), k))

    if all_kendala:
        k_headers = [
            Paragraph("No.", s["small_bold"]),
            Paragraph("Tanggal", s["small_bold"]),
            Paragraph("Kendala / Hambatan", s["small_bold"]),
            Paragraph("Dampak", s["small_bold"]),
            Paragraph("Tindakan Mitigasi", s["small_bold"]),
        ]
        k_cw = [
            CONTENT_W * 0.05, CONTENT_W * 0.12,
            CONTENT_W * 0.27, CONTENT_W * 0.27, CONTENT_W * 0.29,
        ]
        k_rows = [k_headers]
        for idx, (tgl, k) in enumerate(all_kendala):
            k_rows.append([
                Paragraph(str(idx + 1), s["center"]),
                Paragraph(tgl, s["small"]),
                Paragraph(k.get("kendala", ""), s["small"]),
                Paragraph(k.get("dampak", ""), s["small"]),
                Paragraph(k.get("mitigasi", ""), s["small"]),
            ])
        k_tbl = Table(k_rows, colWidths=k_cw)
        k_style = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]
        for i in range(1, len(k_rows)):
            bg = ROW_ALT if (i - 1) % 2 == 0 else WHITE
            k_style.append(("BACKGROUND", (0, i), (-1, i), bg))
        k_tbl.setStyle(TableStyle(k_style))
        story.append(k_tbl)
    else:
        story.append(Paragraph("  ✅ Tidak ada kendala minggu ini.", s["normal"]))

    story.append(Spacer(1, 0.4 * cm))

    # ── 3. Statistik ────────────────────────────────────
    story.append(_section_header("3. STATISTIK MINGGU INI", s))
    story.append(Spacer(1, 0.15 * cm))

    total_hari = len(reports)
    total_kegiatan = sum(len(r.get("detail_kegiatan", [])) for r in reports)
    total_kendala_count = sum(len(r.get("kendala", [])) for r in reports)
    total_selesai = sum(
        1 for r in reports
        for d in r.get("detail_kegiatan", [])
        if d.get("status", "") == "Selesai"
    )
    total_proses = total_kegiatan - total_selesai

    stat_rows = [
        [Paragraph("Total Hari Laporan", s["bold"]),
         Paragraph(f"{total_hari} hari (dari 6 hari kerja)", s["normal"])],
        [Paragraph("Total Kegiatan", s["bold"]),
         Paragraph(str(total_kegiatan), s["normal"])],
        [Paragraph("  — Selesai", s["normal"]),
         Paragraph(str(total_selesai), s["normal"])],
        [Paragraph("  — Dalam Proses / Belum Mulai", s["normal"]),
         Paragraph(str(total_proses), s["normal"])],
        [Paragraph("Total Kendala", s["bold"]),
         Paragraph(str(total_kendala_count), s["normal"])],
    ]
    stat_tbl = Table(stat_rows, colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.55])
    stat_tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(stat_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── 4. Tanda Tangan ─────────────────────────────────
    story.append(_section_header("4. TANDA TANGAN & PERSETUJUAN", s))
    story.append(Spacer(1, 0.15 * cm))

    # Ambil nama PIC dari laporan terakhir
    last_pic = reports[-1].get("nama_pic", "...") if reports else "..."
    tgl_laporan = date.today().strftime("%d/%m/%Y")

    sign_rows = [[
        Paragraph(
            f"Dibuat oleh,<br/><br/><br/><br/>"
            f"___________________________<br/>"
            f"<b>{last_pic}</b><br/>"
            f"Divisi Operational Technology",
            s["sign"],
        ),
        Paragraph(
            f"Diketahui oleh,<br/><br/><br/><br/>"
            f"___________________________<br/>"
            f"<b>(...)</b><br/>"
            f"Manager / Atasan",
            s["sign"],
        ),
    ]]
    # Baris tanggal di atas
    date_rows = [[
        Paragraph(f"Sermayam, {tgl_laporan}", s["sign"]),
        Paragraph(f"Sermayam, {tgl_laporan}", s["sign"]),
    ]]

    sign_tbl = Table(date_rows + sign_rows, colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5])
    sign_tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sign_tbl)

    # ── Build ───────────────────────────────────────────
    def make_canvas(filename, **kwargs):
        from reports.daily_pdf import _FooterCanvas as FC

        class WeeklyCanvas(FC):
            def _draw_footer(self, page_num, total):
                c = self._canvas
                c.saveState()
                c.setFont("Helvetica", 7.5)
                c.setFillColor(colors.HexColor("#666666"))
                text = (f"Laporan Mingguan - Divisi Operational Technology | "
                        f"PT. Global Papua Abadi      Hal. {page_num} / {total}")
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
