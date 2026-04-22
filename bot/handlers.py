import os
import logging
import uuid
from datetime import date
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from config import ALLOWED_USER_ID, OUTPUT_DIR, PHOTO_DIR
from database.db import save_report
from reports.daily_pdf import generate_daily_pdf
from bot.states import *

logger = logging.getLogger(__name__)

HARI_MAP = {
    0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
    4: "Jumat", 5: "Sabtu", 6: "Minggu",
}

KB_DIVISI = [["Operational Technology", "Precision Agriculture"], ["Lainnya"]]
KB_LOKASI = [["Office Sermayam", "Site Lapangan"], ["Lainnya"]]
KB_CUACA = [["Cerah", "Mendung"], ["Hujan", "Cerah Berawan"]]
KB_KONDISI = [["Baik", "Basah"], ["Berlumpur", "Lainnya"]]
KB_STATUS = [["Selesai", "Dalam Proses"], ["Belum Mulai"]]
KB_YA_TIDAK = [["Ya", "Tidak"]]
KB_LANJUT_SELESAI = [["Tambah Lagi", "Selesai"]]
KB_LEWATI = [["Lewati"]]


def _guard(update: Update) -> bool:
    return update.effective_user.id == ALLOWED_USER_ID


def _kb(layout):
    return ReplyKeyboardMarkup(layout, one_time_keyboard=True, resize_keyboard=True)


def _init_data(ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.setdefault("ringkasan", [])
    ctx.user_data.setdefault("detail_kegiatan", [])
    ctx.user_data.setdefault("kendala", [])
    ctx.user_data.setdefault("koordinasi", [])
    ctx.user_data.setdefault("rencana_besok", [])
    ctx.user_data.setdefault("_tmp", {})


async def _save_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE, label: str) -> str:
    """Download photo from Telegram, save to disk, return path."""
    os.makedirs(PHOTO_DIR, exist_ok=True)
    photo = update.message.photo[-1]
    file = await ctx.bot.get_file(photo.file_id)
    filename = f"{date.today().isoformat()}_{label}_{uuid.uuid4().hex[:8]}.jpg"
    path = os.path.join(PHOTO_DIR, filename)
    await file.download_to_drive(path)
    return path


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        await update.message.reply_text(
            f"Maaf, Anda tidak punya akses ke bot ini.\n\n"
            f"(User ID Anda: `{update.effective_user.id}`)",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    ctx.user_data.clear()
    _init_data(ctx)

    today = date.today()
    ctx.user_data["tanggal"] = today.isoformat()
    ctx.user_data["hari"] = HARI_MAP[today.weekday()]

    await update.message.reply_text(
        f"Halo! Saya akan membantu mengisi laporan harian.\n"
        f"Tanggal hari ini: *{today.strftime('%d/%m/%Y')}* ({ctx.user_data['hari']})\n\n"
        f"Siapa nama PIC / Pelapor hari ini?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_NAMA


async def ask_nama(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["nama_pic"] = update.message.text.strip()
    await update.message.reply_text("Divisi?", reply_markup=_kb(KB_DIVISI))
    return ASK_DIVISI


async def ask_divisi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["divisi"] = update.message.text.strip()
    await update.message.reply_text("Lokasi / Site?", reply_markup=_kb(KB_LOKASI))
    return ASK_LOKASI


async def ask_lokasi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "Lainnya":
        await update.message.reply_text(
            "Ketik nama lokasi / site:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_LOKASI_CUSTOM
    ctx.user_data["lokasi"] = text
    await update.message.reply_text(
        "Shift / Jam Kerja? (ketik `-` jika tidak ada)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_SHIFT


async def ask_lokasi_custom(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["lokasi"] = update.message.text.strip()
    await update.message.reply_text(
        "Shift / Jam Kerja? (ketik `-` jika tidak ada)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_SHIFT


async def ask_shift(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["shift"] = update.message.text.strip()
    await update.message.reply_text("Cuaca hari ini?", reply_markup=_kb(KB_CUACA))
    return ASK_CUACA


async def ask_cuaca(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["cuaca"] = update.message.text.strip()
    await update.message.reply_text("Kondisi lapangan?", reply_markup=_kb(KB_KONDISI))
    return ASK_KONDISI


async def ask_kondisi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["kondisi_lapangan"] = update.message.text.strip()
    await update.message.reply_text(
        "Ketik *ringkasan kegiatan* pertama hari ini:\n(contoh: Melakukan pembersihan Automatic Rain Gauge)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_RINGKASAN


async def ask_ringkasan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["ringkasan"].append(update.message.text.strip())
    await update.message.reply_text(
        f"✅ Ringkasan ke-{len(ctx.user_data['ringkasan'])} tersimpan.\nIngin tambah ringkasan lagi?",
        reply_markup=_kb(KB_LANJUT_SELESAI),
    )
    return ASK_RINGKASAN_LAGI


async def ask_ringkasan_lagi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Tambah Lagi":
        await update.message.reply_text(
            f"Ketik ringkasan ke-{len(ctx.user_data['ringkasan']) + 1}:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_RINGKASAN
    await update.message.reply_text(
        "Sekarang masuk ke *Detail Kegiatan*.\n\nJam mulai kegiatan pertama? (contoh: `13.30`)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_DETAIL_JAM_MULAI


async def ask_detail_jam_mulai(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["jam_mulai"] = update.message.text.strip()
    await update.message.reply_text("Jam selesai? (contoh: `14.30`)", reply_markup=ReplyKeyboardRemove())
    return ASK_DETAIL_JAM_SELESAI


async def ask_detail_jam_selesai(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["jam_selesai"] = update.message.text.strip()
    await update.message.reply_text("Aktivitas / kegiatan yang dilakukan?", reply_markup=ReplyKeyboardRemove())
    return ASK_DETAIL_AKTIVITAS


async def ask_detail_aktivitas(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["aktivitas"] = update.message.text.strip()
    await update.message.reply_text("Lokasi kegiatan ini?", reply_markup=_kb(KB_LOKASI))
    return ASK_DETAIL_LOKASI


async def ask_detail_lokasi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "Lainnya":
        await update.message.reply_text("Ketik nama lokasi:", reply_markup=ReplyKeyboardRemove())
        return ASK_DETAIL_LOKASI_CUSTOM
    ctx.user_data["_tmp"]["lokasi"] = text
    await update.message.reply_text("Status kegiatan?", reply_markup=_kb(KB_STATUS))
    return ASK_DETAIL_STATUS


async def ask_detail_lokasi_custom(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["lokasi"] = update.message.text.strip()
    await update.message.reply_text("Status kegiatan?", reply_markup=_kb(KB_STATUS))
    return ASK_DETAIL_STATUS


async def ask_detail_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["status"] = update.message.text.strip()
    await update.message.reply_text(
        "📷 Kirim *foto kegiatan* (atau ketik `Lewati`):",
        parse_mode="Markdown",
        reply_markup=_kb(KB_LEWATI),
    )
    return ASK_DETAIL_FOTO


async def ask_detail_foto_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    path = await _save_photo(update, ctx, "detail")
    ctx.user_data["_tmp"]["foto"] = path
    return await _finish_detail(update, ctx)


async def ask_detail_foto_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["foto"] = ""
    return await _finish_detail(update, ctx)


async def _finish_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tmp = ctx.user_data["_tmp"]
    ctx.user_data["detail_kegiatan"].append({
        "jam_mulai": tmp["jam_mulai"],
        "jam_selesai": tmp.get("jam_selesai", ""),
        "aktivitas": tmp["aktivitas"],
        "lokasi": tmp["lokasi"],
        "status": tmp["status"],
        "foto": tmp.get("foto", ""),
    })
    ctx.user_data["_tmp"] = {}
    n = len(ctx.user_data["detail_kegiatan"])
    await update.message.reply_text(
        f"✅ Kegiatan ke-{n} tersimpan.\nIngin tambah kegiatan lain?",
        reply_markup=_kb(KB_LANJUT_SELESAI),
    )
    return ASK_DETAIL_LAGI


async def ask_detail_lagi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Tambah Lagi":
        await update.message.reply_text(
            f"Jam mulai kegiatan ke-{len(ctx.user_data['detail_kegiatan']) + 1}?",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_DETAIL_JAM_MULAI
    await update.message.reply_text("Ada *kendala* hari ini?", parse_mode="Markdown", reply_markup=_kb(KB_YA_TIDAK))
    return ASK_KENDALA_ADA


async def ask_kendala_ada(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Ya":
        await update.message.reply_text("Apa kendala / hambatannya?", reply_markup=ReplyKeyboardRemove())
        return ASK_KENDALA_ISI
    await update.message.reply_text("Ada *koordinasi lintas divisi* hari ini?", parse_mode="Markdown", reply_markup=_kb(KB_YA_TIDAK))
    return ASK_KOORDINASI_ADA


async def ask_kendala_isi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["kendala"] = update.message.text.strip()
    await update.message.reply_text("Apa dampaknya?", reply_markup=ReplyKeyboardRemove())
    return ASK_KENDALA_DAMPAK


async def ask_kendala_dampak(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["dampak"] = update.message.text.strip()
    await update.message.reply_text("Tindakan mitigasi yang dilakukan?", reply_markup=ReplyKeyboardRemove())
    return ASK_KENDALA_MITIGASI


async def ask_kendala_mitigasi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["mitigasi"] = update.message.text.strip()
    await update.message.reply_text(
        "📷 Kirim *foto SEBELUM maintenance* (atau ketik `Lewati`):",
        parse_mode="Markdown",
        reply_markup=_kb(KB_LEWATI),
    )
    return ASK_KENDALA_FOTO_BEFORE


async def ask_kendala_foto_before_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    path = await _save_photo(update, ctx, "kendala_before")
    ctx.user_data["_tmp"]["foto_before"] = path
    await update.message.reply_text(
        "📷 Kirim *foto SETELAH maintenance* (atau ketik `Lewati`):",
        parse_mode="Markdown",
        reply_markup=_kb(KB_LEWATI),
    )
    return ASK_KENDALA_FOTO_AFTER


async def ask_kendala_foto_before_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["foto_before"] = ""
    await update.message.reply_text(
        "📷 Kirim *foto SETELAH maintenance* (atau ketik `Lewati`):",
        parse_mode="Markdown",
        reply_markup=_kb(KB_LEWATI),
    )
    return ASK_KENDALA_FOTO_AFTER


async def ask_kendala_foto_after_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    path = await _save_photo(update, ctx, "kendala_after")
    ctx.user_data["_tmp"]["foto_after"] = path
    return await _finish_kendala(update, ctx)


async def ask_kendala_foto_after_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["foto_after"] = ""
    return await _finish_kendala(update, ctx)


async def _finish_kendala(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tmp = ctx.user_data["_tmp"]
    ctx.user_data["kendala"].append({
        "kendala": tmp["kendala"],
        "dampak": tmp["dampak"],
        "mitigasi": tmp["mitigasi"],
        "foto_before": tmp.get("foto_before", ""),
        "foto_after": tmp.get("foto_after", ""),
    })
    ctx.user_data["_tmp"] = {}
    await update.message.reply_text(
        f"✅ Kendala ke-{len(ctx.user_data['kendala'])} tersimpan.\nIngin tambah kendala lain?",
        reply_markup=_kb(KB_LANJUT_SELESAI),
    )
    return ASK_KENDALA_LAGI


async def ask_kendala_lagi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Tambah Lagi":
        await update.message.reply_text("Kendala berikutnya?", reply_markup=ReplyKeyboardRemove())
        return ASK_KENDALA_ISI
    await update.message.reply_text("Ada *koordinasi lintas divisi* hari ini?", parse_mode="Markdown", reply_markup=_kb(KB_YA_TIDAK))
    return ASK_KOORDINASI_ADA


async def ask_koordinasi_ada(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Ya":
        await update.message.reply_text("Divisi terkait koordinasi?", reply_markup=ReplyKeyboardRemove())
        return ASK_KOORDINASI_DIVISI
    await update.message.reply_text(
        "Sekarang *Rencana Kegiatan Besok*.\n\nRencana kegiatan pertama?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_RENCANA


async def ask_koordinasi_divisi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["divisi"] = update.message.text.strip()
    await update.message.reply_text("Topik koordinasi?", reply_markup=ReplyKeyboardRemove())
    return ASK_KOORDINASI_TOPIK


async def ask_koordinasi_topik(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["topik"] = update.message.text.strip()
    await update.message.reply_text("Tindak lanjut?", reply_markup=ReplyKeyboardRemove())
    return ASK_KOORDINASI_TINDAK


async def ask_koordinasi_tindak(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["tindak_lanjut"] = update.message.text.strip()
    await update.message.reply_text("Status koordinasi?", reply_markup=_kb(KB_STATUS))
    return ASK_KOORDINASI_STATUS


async def ask_koordinasi_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tmp = ctx.user_data["_tmp"]
    ctx.user_data["koordinasi"].append({
        "divisi": tmp["divisi"],
        "topik": tmp["topik"],
        "tindak_lanjut": tmp["tindak_lanjut"],
        "status": update.message.text.strip(),
    })
    ctx.user_data["_tmp"] = {}
    await update.message.reply_text(
        f"✅ Koordinasi ke-{len(ctx.user_data['koordinasi'])} tersimpan.\nIngin tambah koordinasi lain?",
        reply_markup=_kb(KB_LANJUT_SELESAI),
    )
    return ASK_KOORDINASI_LAGI


async def ask_koordinasi_lagi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Tambah Lagi":
        await update.message.reply_text("Divisi terkait berikutnya?", reply_markup=ReplyKeyboardRemove())
        return ASK_KOORDINASI_DIVISI
    await update.message.reply_text(
        "Sekarang *Rencana Kegiatan Besok*.\n\nRencana kegiatan pertama?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_RENCANA


async def ask_rencana(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["rencana"] = update.message.text.strip()
    await update.message.reply_text("Target / output dari rencana ini?", reply_markup=ReplyKeyboardRemove())
    return ASK_RENCANA_TARGET


async def ask_rencana_target(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["_tmp"]["target"] = update.message.text.strip()
    await update.message.reply_text("PIC untuk rencana ini?", reply_markup=ReplyKeyboardRemove())
    return ASK_RENCANA_PIC


async def ask_rencana_pic(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tmp = ctx.user_data["_tmp"]
    ctx.user_data["rencana_besok"].append({
        "rencana": tmp["rencana"],
        "target": tmp["target"],
        "pic": update.message.text.strip(),
    })
    ctx.user_data["_tmp"] = {}
    n = len(ctx.user_data["rencana_besok"])
    lanjut = n < 5
    msg = f"✅ Rencana ke-{n} tersimpan."
    if lanjut:
        msg += "\nIngin tambah rencana lain?"
        await update.message.reply_text(msg, reply_markup=_kb(KB_LANJUT_SELESAI))
        return ASK_RENCANA_LAGI
    await update.message.reply_text(
        msg + "\n\nTerakhir, *catatan tambahan*? (ketik `-` jika tidak ada)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_CATATAN


async def ask_rencana_lagi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Tambah Lagi":
        await update.message.reply_text(
            f"Rencana kegiatan ke-{len(ctx.user_data['rencana_besok']) + 1}?",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_RENCANA
    await update.message.reply_text(
        "Terakhir, *catatan tambahan*? (ketik `-` jika tidak ada)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_CATATAN


async def ask_catatan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["catatan_tambahan"] = update.message.text.strip()

    await update.message.reply_text(
        "Sedang memproses dan membuat PDF... Mohon tunggu sebentar.",
        reply_markup=ReplyKeyboardRemove(),
    )

    data = {k: v for k, v in ctx.user_data.items() if not k.startswith("_")}

    save_report(data)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_path = generate_daily_pdf(data, OUTPUT_DIR)

    with open(pdf_path, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=os.path.basename(pdf_path),
            caption=f"Laporan Harian {data['tanggal']} sudah selesai!",
        )

    ctx.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Laporan dibatalkan.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def build_conversation_handler() -> ConversationHandler:
    T = lambda f: MessageHandler(filters.TEXT & ~filters.COMMAND, f)
    P = lambda f: MessageHandler(filters.PHOTO, f)

    return ConversationHandler(
        entry_points=[CommandHandler("laporan", start), CommandHandler("start", start)],
        states={
            ASK_NAMA: [T(ask_nama)],
            ASK_DIVISI: [T(ask_divisi)],
            ASK_LOKASI: [T(ask_lokasi)],
            ASK_LOKASI_CUSTOM: [T(ask_lokasi_custom)],
            ASK_SHIFT: [T(ask_shift)],
            ASK_CUACA: [T(ask_cuaca)],
            ASK_KONDISI: [T(ask_kondisi)],
            ASK_RINGKASAN: [T(ask_ringkasan)],
            ASK_RINGKASAN_LAGI: [T(ask_ringkasan_lagi)],
            ASK_DETAIL_JAM_MULAI: [T(ask_detail_jam_mulai)],
            ASK_DETAIL_JAM_SELESAI: [T(ask_detail_jam_selesai)],
            ASK_DETAIL_AKTIVITAS: [T(ask_detail_aktivitas)],
            ASK_DETAIL_LOKASI: [T(ask_detail_lokasi)],
            ASK_DETAIL_LOKASI_CUSTOM: [T(ask_detail_lokasi_custom)],
            ASK_DETAIL_STATUS: [T(ask_detail_status)],
            ASK_DETAIL_FOTO: [P(ask_detail_foto_photo), T(ask_detail_foto_skip)],
            ASK_DETAIL_LAGI: [T(ask_detail_lagi)],
            ASK_KENDALA_ADA: [T(ask_kendala_ada)],
            ASK_KENDALA_ISI: [T(ask_kendala_isi)],
            ASK_KENDALA_DAMPAK: [T(ask_kendala_dampak)],
            ASK_KENDALA_MITIGASI: [T(ask_kendala_mitigasi)],
            ASK_KENDALA_FOTO_BEFORE: [P(ask_kendala_foto_before_photo), T(ask_kendala_foto_before_skip)],
            ASK_KENDALA_FOTO_AFTER: [P(ask_kendala_foto_after_photo), T(ask_kendala_foto_after_skip)],
            ASK_KENDALA_LAGI: [T(ask_kendala_lagi)],
            ASK_KOORDINASI_ADA: [T(ask_koordinasi_ada)],
            ASK_KOORDINASI_DIVISI: [T(ask_koordinasi_divisi)],
            ASK_KOORDINASI_TOPIK: [T(ask_koordinasi_topik)],
            ASK_KOORDINASI_TINDAK: [T(ask_koordinasi_tindak)],
            ASK_KOORDINASI_STATUS: [T(ask_koordinasi_status)],
            ASK_KOORDINASI_LAGI: [T(ask_koordinasi_lagi)],
            ASK_RENCANA: [T(ask_rencana)],
            ASK_RENCANA_TARGET: [T(ask_rencana_target)],
            ASK_RENCANA_PIC: [T(ask_rencana_pic)],
            ASK_RENCANA_LAGI: [T(ask_rencana_lagi)],
            ASK_CATATAN: [T(ask_catatan)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
