import os
import threading
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set.")

app = Flask(__name__)

@app.get("/")
def health():
    return "DanloadchilnstaBot is running", 200

@app.get("/health")
def health_check():
    return "OK", 200

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "لینک عمومی پست یا ریلز اینستاگرام را بفرست تا تلاش کنم فایل را برایت دانلود کنم.\n\n"
        "نکته: فقط لینک‌های عمومی و محتوایی که اجازه دانلود/استفاده از آن را داری."
    )

async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = (update.message.text or "").strip()
    if "instagram.com" not in url:
        await update.message.reply_text("لطفاً یک لینک اینستاگرام بفرست.")
        return

    await update.message.reply_text("⏳ در حال دریافت لینک...")

    filename = None
    try:
        opts = {
            "outtmpl": "%(id)s.%(ext)s",
            "format": "best[ext=mp4]/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "restrictfilenames": True,
        }

        def do_download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filename = await asyncio.to_thread(do_download)

        if not os.path.exists(filename):
            await update.message.reply_text("❌ فایل دریافت نشد.")
            return

        size = os.path.getsize(filename)
        if size > 49 * 1024 * 1024:
            await update.message.reply_text(
                "❌ فایل بزرگ‌تر از حد مجاز ارسال ربات است."
            )
            return

        with open(filename, "rb") as f:
            await update.message.reply_video(video=f, caption="✅ آماده شد")

    except Exception as e:
        print("DOWNLOAD ERROR:", repr(e))
        await update.message.reply_text(
            "❌ دانلود انجام نشد.\n"
            "ممکن است لینک خصوصی باشد، اینستاگرام دسترسی را محدود کرده باشد، "
            "یا فرمت لینک پشتیبانی نشود."
        )
    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass

async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("Telegram bot started.")
    await asyncio.Event().wait()

def start_bot():
    asyncio.run(run_bot())

if __name__ == "__main__":
    threading.Thread(target=start_bot, daemon=True).start()
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
