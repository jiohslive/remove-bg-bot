import io
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================== CONFIG ==================
BOT_TOKEN = "8260023440:AAFBieaxbdSgdxeeJ48q_epB1EZ_G2HjWEQ"
REMOVE_BG_API_KEY = "9t4eVTPnsEc8ncdJnwfPnM11"
ADMIN_ID = 7982420411  # Tujha Telegram user ID je admin sathi
# ===========================================

# Logging setup
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(username)s - %(message)s'
)

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello 👋\n\nSend me an image and I will remove its background."
    )

# ================== PHOTO HANDLER ==================
async def remove_background(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or user.first_name

    logging.info(f"{username} sent a photo.")

    # Notify user
    await update.message.reply_text("Processing your image... ⏳")

    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()

        # Remove.bg API call
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": image_bytes},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVE_BG_API_KEY},
        )

        if response.status_code == 200:
            bio = io.BytesIO(response.content)
            bio.name = "background_removed.png"

            # Send processed photo as file
            await update.message.reply_document(
                document=bio,
                filename="background_removed.png"
            )

            await update.message.reply_text("✅ Your image is ready!")
            logging.info(f"{username}'s photo processed successfully.")

        else:
            await update.message.reply_text("❌ Error removing background.")
            logging.error(f"{username} - Remove.bg API Error: {response.status_code} {response.text}")
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"{username} - Remove.bg API Error: {response.status_code}")

    except Exception as e:
        logging.error(f"Error processing photo from {username}: {str(e)}")
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"Error processing photo from {username}: {str(e)}")
        await update.message.reply_text("❌ Something went wrong while processing your image.")

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handler
    app.add_handler(CommandHandler("start", start))
    
    # Photo handler
    app.add_handler(MessageHandler(filters.PHOTO, remove_background))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
