import os
from datetime import date
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from config import ALLOWED_USER_ID
from database.db import (
    get_all_reports, get_report_by_id, delete_report, count_reports,
)


def _guard(update: Update) -> bool:
    return update.effective_user.id == ALLOWED_USER_ID


async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        return
    reports = get_all_reports(limit=50)
    total = count_reports()

    if not reports:
        await update.message.reply_text("Belum ada laporan yang tersimpan.")
        return

    lines = [f"📋 *Daftar Laporan* (total: {total})\n"]
    for r in reports:
        d = date.fromisoformat(r["tanggal"])
        ringkasan = r["ringkasan"][0] if r["ringkasan"] else "-"
        if len(ringkasan) > 45:
            ringkasan = ringkasan[:42] + "..."
        lines.append(
            f"*#{r['id']}* — {d.strftime('%d/%m/%Y')} ({r['hari']})\n"
            f"   👤 {r['nama_pic']}\n"
            f"   📝 {ringkasan}\n"
        )

    lines.append("\n_Hapus dengan:_ `/hapus <id>`\n_Contoh:_ `/hapus 3`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_hapus(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        return

    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Gunakan: `/hapus <id>`\n\nContoh: `/hapus 3`\n\nLihat daftar ID dengan `/list`.",
            parse_mode="Markdown",
        )
        return

    try:
        report_id = int(args[0])
    except ValueError:
        await update.message.reply_text("ID harus angka. Contoh: `/hapus 3`", parse_mode="Markdown")
        return

    report = get_report_by_id(report_id)
    if not report:
        await update.message.reply_text(f"❌ Laporan dengan ID *#{report_id}* tidak ditemukan.", parse_mode="Markdown")
        return

    photo_paths = []
    for item in report.get("detail_kegiatan", []):
        if item.get("foto"):
            photo_paths.append(item["foto"])
    for item in report.get("kendala", []):
        if item.get("foto_before"):
            photo_paths.append(item["foto_before"])
        if item.get("foto_after"):
            photo_paths.append(item["foto_after"])

    deleted = delete_report(report_id)
    if not deleted:
        await update.message.reply_text("Gagal menghapus laporan.")
        return

    removed_photos = 0
    for p in photo_paths:
        try:
            if os.path.exists(p):
                os.remove(p)
                removed_photos += 1
        except Exception:
            pass

    d = date.fromisoformat(report["tanggal"])
    await update.message.reply_text(
        f"✅ Laporan *#{report_id}* ({d.strftime('%d/%m/%Y')}) berhasil dihapus.\n"
        f"🖼️ {removed_photos} foto ikut terhapus.",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        return
    text = (
        "*📖 Perintah yang tersedia:*\n\n"
        "/laporan — Buat laporan harian baru\n"
        "/list — Lihat semua laporan yang tersimpan\n"
        "/export `<id>` — Unduh ulang PDF laporan berdasarkan ID\n"
        "/hapus `<id>` — Hapus laporan berdasarkan ID\n"
        "/weekly — Generate laporan mingguan sekarang\n"
        "/back — Kembali ke pertanyaan sebelumnya (saat mengisi laporan)\n"
        "/cancel — Batalkan laporan yang sedang diisi\n"
        "/help — Tampilkan bantuan ini"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Generate ulang PDF laporan berdasarkan ID."""
    if not _guard(update):
        return

    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Gunakan: `/export <id>`\n\nContoh: `/export 3`\n\nLihat daftar ID dengan `/list`.",
            parse_mode="Markdown",
        )
        return

    try:
        report_id = int(args[0])
    except ValueError:
        await update.message.reply_text("ID harus angka. Contoh: `/export 3`", parse_mode="Markdown")
        return

    report = get_report_by_id(report_id)
    if not report:
        await update.message.reply_text(
            f"❌ Laporan dengan ID *#{report_id}* tidak ditemukan.",
            parse_mode="Markdown",
        )
        return

    from config import OUTPUT_DIR
    from reports.daily_pdf import generate_daily_pdf

    await update.message.reply_text(f"Membuat ulang PDF untuk laporan *#{report_id}*...",
                                    parse_mode="Markdown")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = generate_daily_pdf(report, OUTPUT_DIR)

    d = date.fromisoformat(report["tanggal"])
    with open(path, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=os.path.basename(path),
            caption=f"Laporan Harian #{report_id} — {d.strftime('%d/%m/%Y')}",
        )


async def cmd_weekly(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Generate weekly report on-demand."""
    if not _guard(update):
        return
    from config import OUTPUT_DIR
    from database.db import get_current_week_reports
    from reports.weekly_pdf import generate_weekly_pdf

    reports = get_current_week_reports()
    if not reports:
        await update.message.reply_text("Belum ada laporan harian minggu ini.")
        return

    await update.message.reply_text(f"Membuat laporan mingguan dari {len(reports)} hari...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = generate_weekly_pdf(reports, OUTPUT_DIR)
    with open(path, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=os.path.basename(path),
            caption=f"Laporan Mingguan ({len(reports)} hari)",
        )


def register_commands(app):
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("hapus", cmd_hapus))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("weekly", cmd_weekly))
