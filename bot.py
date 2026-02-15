import io
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ---------------- BOT CONFIG ----------------
BOT_TOKEN = "8260023440:AAFBieaxbdSgdxeeJ48q_epB1EZ_G2HjWEQ"
REMOVE_BG_API_KEY = "9t4eVTPnsEc8ncdJnwfPnM11"

# Admin ID list (replace with your Telegram numeric ID)
ADMIN_IDS = [7982420411]

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    await update.message.reply_text(
        "Hello Admin 👋\n\nSend me an image and I will remove its background."
    )

async def remove_background(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to process images.")
        return

    await update.message.reply_text("Processing your image... ⏳")

    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()

    response = requests.post(
        "https://api.remove.bg/v1.0/removebg",
        files={"image_file": image_bytes},
        data={"size": "auto"},
        headers={"X-Api-Key": REMOVE_BG_API_KEY},
    )

    if response.status_code == 200:
        bio = io.BytesIO(response.content)
        bio.name = "background_removed.png"

        await update.message.reply_document(
            document=bio,
            filename="background_removed.png"
        )

        await update.message.reply_text("✅ Your image is ready!")
    else:
        await update.message.reply_text("❌ Error removing background.")

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))

    # Photo handler
    app.add_handler(MessageHandler(filters.PHOTO, remove_background))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
