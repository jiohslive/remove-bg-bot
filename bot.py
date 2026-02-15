import io
import requests
from telegram import Update, Chat
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ------------------- CONFIG -------------------
BOT_TOKEN = "8260023440:AAFBieaxbdSgdxeeJ48q_epB1EZ_G2HjWEQ"
REMOVE_BG_API_KEY = "9t4eVTPnsEc8ncdJnwfPnM11"

# Admin IDs (for notifications only)
ADMIN_IDS = [7982420411]  # Replace with your Telegram ID(s)

# Users list (in-memory; use DB for permanent storage)
USERS = set()
# ------------------------------------------------

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.add(user.id)

    await update.message.reply_text(
        "Hello 👋\n\nSend me an image and I will remove its background."
    )

    # Notify admin
    username = f"@{user.username}" if user.username else user.full_name
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"✅ {username} just started the bot."
        )

# Background removal handler
async def remove_background(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.add(user.id)

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

        # Notify admin
        username = f"@{user.username}" if user.username else user.full_name
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"✅ {username} just removed a photo background."
            )

        await update.message.reply_text("✅ Your image is ready!")
    else:
        await update.message.reply_text("❌ Error removing background.")

# Broadcast command
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    success_count = 0
    fail_count = 0

    for user_id in USERS:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            success_count += 1
        except:
            fail_count += 1

    await update.message.reply_text(
        f"Broadcast sent!\n✅ Success: {success_count}\n❌ Failed: {fail_count}"
    )

# Pin broadcast in a group/channel
async def pin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /pinbroadcast <chat_id> <message>")
        return

    chat_id = context.args[0]
    message_text = " ".join(context.args[1:])

    try:
        msg = await context.bot.send_message(chat_id=chat_id, text=message_text)
        await context.bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id, disable_notification=False)
        await update.message.reply_text("✅ Broadcast sent and pinned successfully!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to pin broadcast: {e}")

# Main function
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, remove_background))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("pinbroadcast", pin_broadcast))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
