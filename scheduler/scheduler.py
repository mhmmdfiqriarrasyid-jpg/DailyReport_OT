import asyncio
import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import ALLOWED_USER_ID, OUTPUT_DIR, TIMEZONE
from database.db import get_current_week_reports
from reports.weekly_pdf import generate_weekly_pdf

logger = logging.getLogger(__name__)


def _send_weekly_report(app):
    async def _run():
        reports = get_current_week_reports()
        if not reports:
            await app.bot.send_message(
                chat_id=ALLOWED_USER_ID,
                text="Tidak ada laporan harian minggu ini untuk direkap.",
            )
            return

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        pdf_path = generate_weekly_pdf(reports, OUTPUT_DIR)

        with open(pdf_path, "rb") as f:
            await app.bot.send_document(
                chat_id=ALLOWED_USER_ID,
                document=f,
                filename=os.path.basename(pdf_path),
                caption=f"Laporan Mingguan otomatis sudah dibuat! ({len(reports)} hari laporan)",
            )
        logger.info("Weekly report berhasil dikirim.")

    asyncio.run(_run())


def start_scheduler(app):
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        _send_weekly_report,
        trigger=CronTrigger(day_of_week="sat", hour=15, minute=0, timezone=TIMEZONE),
        args=[app],
        id="weekly_report",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler aktif — weekly report setiap Sabtu 15.00 {TIMEZONE}")
    return scheduler
