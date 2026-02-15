import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("8260023440:AAFBieaxbdSgdxeeJ48q_epB1EZ_G2HjWEQ")
REMOVE_BG_API = os.getenv("9t4eVTPnsEc8ncdJnwfPnM11")

async def remove_bg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    photo_path = "input.jpg"
    await file.download_to_drive(photo_path)

    await update.message.reply_text("⏳ Processing...")

    with open(photo_path, "rb") as img:
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": img},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVE_BG_API},
        )

    if response.status_code == 200:
        with open("output.png", "wb") as out:
            out.write(response.content)
        await update.message.reply_photo(photo=open("output.png", "rb"))
    else:
        await update.message.reply_text("❌ Error removing background.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, remove_bg))

print("Bot Running...")
app.run_polling()
