import os
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    Image as RLImage,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

W, H = A4
MARGIN = 1.8 * cm
CONTENT_W = W - 2 * MARGIN

DARK_BLUE = colors.HexColor("#1F3864")
LIGHT_BLUE = colors.HexColor("#BDD7EE")
HEADER_BG = colors.HexColor("#2E5FA3")
ROW_ALT = colors.HexColor("#F2F7FC")
WHITE = colors.white
BLACK = colors.black


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", fontSize=16, fontName="Helvetica-Bold",
                                textColor=WHITE, alignment=TA_CENTER, spaceAfter=2),
        "subtitle": ParagraphStyle("subtitle", fontSize=10, fontName="Helvetica",
                                   textColor=WHITE, alignment=TA_CENTER),
        "section": ParagraphStyle("section", fontSize=10, fontName="Helvetica-Bold",
                                  textColor=WHITE),
        "normal": ParagraphStyle("normal", fontSize=9, fontName="Helvetica",
                                 textColor=BLACK, leading=13),
        "bold": ParagraphStyle("bold", fontSize=9, fontName="Helvetica-Bold",
                               textColor=BLACK),
        "small": ParagraphStyle("small", fontSize=8, fontName="Helvetica",
                                textColor=BLACK, leading=11),
        "center": ParagraphStyle("center", fontSize=9, fontName="Helvetica",
                                 alignment=TA_CENTER, textColor=BLACK),
        "footer": ParagraphStyle("footer", fontSize=7.5, fontName="Helvetica",
                                  textColor=colors.HexColor("#666666"), alignment=TA_CENTER),
    }


def _thumb(path: str, s, w=2.8 * cm, h=2.8 * cm):
    if path and os.path.exists(path):
        try:
            return RLImage(path, width=w, height=h, kind="proportional")
        except Exception:
            return Paragraph("-", s["center"])
    return Paragraph("-", s["center"])


def _section_header(title: str, s) -> Table:
    cell = Paragraph(f"  {title}", s["section"])
    tbl = Table([[cell]], colWidths=[CONTENT_W])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HEADER_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _identitas_table(data: dict, s) -> Table:
    d = date.fromisoformat(data["tanggal"])
    tanggal_str = d.strftime("%d/%m/%Y")

    rows = [
        [
            Paragraph("Tanggal", s["bold"]), Paragraph(tanggal_str, s["normal"]),
            Paragraph("Hari", s["bold"]), Paragraph(data["hari"], s["normal"]),
        ],
        [
            Paragraph("Nama PIC / Pelapor", s["bold"]), Paragraph(data["nama_pic"], s["normal"]),
            Paragraph("Divisi", s["bold"]), Paragraph(data["divisi"], s["normal"]),
        ],
        [
            Paragraph("Lokasi / Site", s["bold"]), Paragraph(data["lokasi"], s["normal"]),
            Paragraph("Shift / Jam Kerja", s["bold"]), Paragraph(data["shift"], s["normal"]),
        ],
        [
            Paragraph("Cuaca Hari Ini", s["bold"]), Paragraph(data["cuaca"], s["normal"]),
            Paragraph("Kondisi Lapangan", s["bold"]), Paragraph(data["kondisi_lapangan"], s["normal"]),
        ],
    ]

    cw = [CONTENT_W * 0.22, CONTENT_W * 0.28, CONTENT_W * 0.22, CONTENT_W * 0.28]
    tbl = Table(rows, colWidths=cw)
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_BLUE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _ringkasan_table(ringkasan: list, s) -> Table:
    rows = []
    for item in ringkasan:
        rows.append([Paragraph(f"\u2022  {item}", s["normal"])])
    if not rows:
        rows.append([Paragraph("-", s["normal"])])

    tbl = Table(rows, colWidths=[CONTENT_W])
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return tbl


def _detail_table(detail: list, s) -> Table:
    headers = [
        Paragraph("Jam Mulai", s["bold"]),
        Paragraph("Jam Selesai", s["bold"]),
        Paragraph("Aktivitas / Kegiatan Lapangan", s["bold"]),
        Paragraph("Lokasi", s["bold"]),
        Paragraph("Status", s["bold"]),
        Paragraph("Dokumentasi", s["bold"]),
    ]
    cw = [
        CONTENT_W * 0.09, CONTENT_W * 0.09, CONTENT_W * 0.32,
        CONTENT_W * 0.15, CONTENT_W * 0.11, CONTENT_W * 0.24,
    ]
    rows = [headers]
    for i, item in enumerate(detail):
        rows.append([
            Paragraph(item.get("jam_mulai", ""), s["small"]),
            Paragraph(item.get("jam_selesai", ""), s["small"]),
            Paragraph(item.get("aktivitas", ""), s["small"]),
            Paragraph(item.get("lokasi", ""), s["small"]),
            Paragraph(item.get("status", ""), s["small"]),
            _thumb(item.get("foto", ""), s),
        ])

    if len(rows) == 1:
        rows.append([Paragraph("-", s["small"]), Paragraph("", s["small"]),
                     Paragraph("", s["small"]), Paragraph("", s["small"]),
                     Paragraph("", s["small"]), Paragraph("-", s["center"])])

    tbl = Table(rows, colWidths=cw)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(rows)):
        bg = ROW_ALT if (i - 1) % 2 == 0 else WHITE
        style.append(("BACKGROUND", (0, i), (-1, i), bg))
    tbl.setStyle(TableStyle(style))
    return tbl


def _kendala_table(kendala: list, s) -> Table:
    headers = [
        Paragraph("No.", s["bold"]),
        Paragraph("Kendala / Hambatan", s["bold"]),
        Paragraph("Dampak", s["bold"]),
        Paragraph("Tindakan Mitigasi", s["bold"]),
        Paragraph("Dokumen Sebelum", s["bold"]),
        Paragraph("Dokumen Sesudah", s["bold"]),
    ]
    cw = [
        CONTENT_W * 0.05, CONTENT_W * 0.20, CONTENT_W * 0.16,
        CONTENT_W * 0.19, CONTENT_W * 0.20, CONTENT_W * 0.20,
    ]
    rows = [headers]
    for i, item in enumerate(kendala):
        rows.append([
            Paragraph(str(i + 1), s["center"]),
            Paragraph(item.get("kendala", ""), s["small"]),
            Paragraph(item.get("dampak", ""), s["small"]),
            Paragraph(item.get("mitigasi", ""), s["small"]),
            _thumb(item.get("foto_before", ""), s, w=2.3 * cm, h=2.3 * cm),
            _thumb(item.get("foto_after", ""), s, w=2.3 * cm, h=2.3 * cm),
        ])

    if len(rows) == 1:
        rows.append([Paragraph("1", s["center"]), Paragraph("-", s["small"]),
                     Paragraph("-", s["small"]), Paragraph("-", s["small"]),
                     Paragraph("-", s["center"]), Paragraph("-", s["center"])])

    tbl = Table(rows, colWidths=cw)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (4, 1), (5, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(rows)):
        bg = ROW_ALT if (i - 1) % 2 == 0 else WHITE
        style.append(("BACKGROUND", (0, i), (-1, i), bg))
    tbl.setStyle(TableStyle(style))
    return tbl


def _koordinasi_table(koordinasi: list, s) -> Table:
    headers = [
        Paragraph("Divisi Terkait", s["bold"]),
        Paragraph("Topik Koordinasi", s["bold"]),
        Paragraph("Tindak Lanjut", s["bold"]),
        Paragraph("Status", s["bold"]),
    ]
    cw = [CONTENT_W * 0.22, CONTENT_W * 0.30, CONTENT_W * 0.30, CONTENT_W * 0.18]
    rows = [headers]
    for i, item in enumerate(koordinasi):
        rows.append([
            Paragraph(item.get("divisi", ""), s["small"]),
            Paragraph(item.get("topik", ""), s["small"]),
            Paragraph(item.get("tindak_lanjut", ""), s["small"]),
            Paragraph(item.get("status", ""), s["small"]),
        ])

    if len(rows) == 1:
        rows.append([Paragraph("-", s["small"]), Paragraph("", s["small"]),
                     Paragraph("", s["small"]), Paragraph("", s["small"])])

    tbl = Table(rows, colWidths=cw)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(rows)):
        bg = ROW_ALT if (i - 1) % 2 == 0 else WHITE
        style.append(("BACKGROUND", (0, i), (-1, i), bg))
    tbl.setStyle(TableStyle(style))
    return tbl


def _rencana_table(rencana: list, s) -> Table:
    headers = [
        Paragraph("No.", s["bold"]),
        Paragraph("Rencana Kegiatan Besok", s["bold"]),
        Paragraph("Target / Output", s["bold"]),
        Paragraph("PIC", s["bold"]),
    ]
    cw = [CONTENT_W * 0.07, CONTENT_W * 0.43, CONTENT_W * 0.30, CONTENT_W * 0.20]
    rows = [headers]
    for i in range(5):
        if i < len(rencana):
            item = rencana[i]
            rows.append([
                Paragraph(str(i + 1), s["center"]),
                Paragraph(item.get("rencana", ""), s["small"]),
                Paragraph(item.get("target", ""), s["small"]),
                Paragraph(item.get("pic", ""), s["small"]),
            ])
        else:
            rows.append([Paragraph(str(i + 1), s["center"]),
                         Paragraph("", s["small"]), Paragraph("", s["small"]),
                         Paragraph("", s["small"])])

    tbl = Table(rows, colWidths=cw)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(rows)):
        bg = ROW_ALT if (i - 1) % 2 == 0 else WHITE
        style.append(("BACKGROUND", (0, i), (-1, i), bg))
    tbl.setStyle(TableStyle(style))
    return tbl


def _catatan_table(catatan: str, s) -> Table:
    text = catatan if catatan and catatan != "-" else "-"
    rows = [[Paragraph(text, s["normal"])]]
    tbl = Table(rows, colWidths=[CONTENT_W])
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 40),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return tbl


class _FooterCanvas:
    def __init__(self, filename, **kwargs):
        from reportlab.pdfgen.canvas import Canvas
        self._canvas = Canvas(filename, **kwargs)
        self._pages = []

    def __getattr__(self, name):
        return getattr(self._canvas, name)

    def showPage(self):
        self._pages.append(dict(self._canvas.__dict__))
        self._canvas._startPage()

    def save(self):
        total = len(self._pages) + 1
        for i, page in enumerate(self._pages, 1):
            self._canvas.__dict__.update(page)
            self._draw_footer(i, total)
            self._canvas.showPage()
        self._draw_footer(total, total)
        self._canvas.save()

    def _draw_footer(self, page_num, total):
        from reportlab.lib.styles import getSampleStyleSheet
        c = self._canvas
        c.saveState()
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#666666"))
        text = f"Laporan Harian - Divisi Operational Technology | PT. Global Papua Abadi      Hal. {page_num} / {total}"
        c.drawCentredString(W / 2, 1.1 * cm, text)
        c.restoreState()


def generate_daily_pdf(data: dict, output_dir: str) -> str:
    d = date.fromisoformat(data["tanggal"])
    filename = f"Laporan_Harian_OT_{d.strftime('%d%m%y')}.pdf"
    filepath = os.path.join(output_dir, filename)

    s = _styles()
    story = []

    # ── Header ──────────────────────────────────────────
    header_data = [[
        Paragraph("LAPORAN HARIAN", s["title"]),
    ], [
        Paragraph("Divisi Operational Technology Engineer", s["subtitle"]),
    ]]
    header_tbl = Table(header_data, colWidths=[CONTENT_W])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 0.3 * cm))

    # ── 1. Identitas ────────────────────────────────────
    story.append(_section_header("1. IDENTITAS LAPORAN", s))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_identitas_table(data, s))
    story.append(Spacer(1, 0.4 * cm))

    # ── 2. Ringkasan ────────────────────────────────────
    story.append(_section_header("2. RINGKASAN KEGIATAN LAPANGAN", s))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_ringkasan_table(data.get("ringkasan", []), s))
    story.append(Spacer(1, 0.4 * cm))

    # ── 3. Detail ───────────────────────────────────────
    story.append(_section_header("3. DETAIL KEGIATAN LAPANGAN", s))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_detail_table(data.get("detail_kegiatan", []), s))
    story.append(Spacer(1, 0.4 * cm))

    # ── 4. Kendala ──────────────────────────────────────
    story.append(_section_header("4. KENDALA, DAMPAK & MITIGASI", s))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_kendala_table(data.get("kendala", []), s))
    story.append(Spacer(1, 0.4 * cm))

    # ── 5. Koordinasi ───────────────────────────────────
    story.append(_section_header("5. KOORDINASI LINTAS DIVISI", s))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_koordinasi_table(data.get("koordinasi", []), s))
    story.append(Spacer(1, 0.4 * cm))

    # ── 6. Rencana Besok ────────────────────────────────
    story.append(_section_header("6. RENCANA KEGIATAN BESOK (H+1)", s))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_rencana_table(data.get("rencana_besok", []), s))
    story.append(Spacer(1, 0.4 * cm))

    # ── 7. Catatan ──────────────────────────────────────
    story.append(_section_header("7. CATATAN TAMBAHAN / NOTES", s))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_catatan_table(data.get("catatan_tambahan", ""), s))

    # ── Build ───────────────────────────────────────────
    def make_canvas(filename, **kwargs):
        return _FooterCanvas(filename, **kwargs)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=1.8 * cm,
    )
    doc.build(story, canvasmaker=make_canvas)
    return filepath
