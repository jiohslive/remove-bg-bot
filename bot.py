import io
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ------------------- CONFIG -------------------
BOT_TOKEN = "8260023440:AAFBieaxbdSgdxeeJ48q_epB1EZ_G2HjWEQ"
REMOVE_BG_API_KEY = "9t4eVTPnsEc8ncdJnwfPnM11"

# Admin IDs (for notifications only)
ADMIN_IDS = [7982420411]  # <-- replace with your Telegram ID(s)
# ------------------------------------------------

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello 👋\n\nSend me an image and I will remove its background."
    )

# Background removal handler
async def remove_background(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text("Processing your image... ⏳")

    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()
    except Exception:
        await update.message.reply_text("❌ Failed to download the image.")
        return

    try:
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": image_bytes},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVE_BG_API_KEY},
        )
    except Exception:
        await update.message.reply_text("❌ Error connecting to remove.bg API.")
        return

    if response.status_code == 200:
        bio = io.BytesIO(response.content)
        bio.name = "background_removed.png"

        await update.message.reply_document(
            document=bio,
            filename="background_removed.png"
        )

        # Notify admin(s)
        username = f"@{user.username}" if user.username else user.full_name
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"✅ {username} just removed a photo background."
            )

        await update.message.reply_text("✅ Your image is ready!")
    else:
        await update.message.reply_text("❌ Error removing background.")

# Main function
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, remove_background))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
