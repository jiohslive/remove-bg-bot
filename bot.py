import io
import requests
import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ------------------- CONFIG -------------------
BOT_TOKEN = "8260023440:AAFBieaxbdSgdxeeJ48q_epB1EZ_G2HjWEQ"
REMOVE_BG_API_KEY = "9t4eVTPnsEc8ncdJnwfPnM11"

# Admin IDs
ADMIN_IDS = [7982420411]  # <-- replace with your Telegram ID(s)

# Database file
DB_FILE = "bot_users.db"
# ------------------------------------------------

# ------------------- DATABASE -------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            photos_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users (user_id, username, full_name) 
        VALUES (?, ?, ?)
    ''', (user.id, user.username, user.full_name))
    conn.commit()
    conn.close()

def increment_user_photos(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE users
        SET photos_count = photos_count + 1
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

def get_user_photos_count(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT photos_count FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def get_all_user_ids():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]
# ------------------------------------------------

# ------------------- COMMANDS -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user)
    await update.message.reply_text(
        "Hello 👋\n\nSend me an image and I will remove its background."
    )

    # Notify Admins about new user start
    username = f"@{user.username}" if user.username else user.full_name
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🚀 {username} just started the bot."
            )
        except Exception:
            continue

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📌 *Bot Commands:*\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/stats - Show your usage stats\n"
        "/broadcast <message> - Admin only: Broadcast message to all users"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count = get_user_photos_count(user_id)
    await update.message.reply_text(f"📊 You have removed backgrounds from {count} images.")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("❌ Usage: /broadcast Your message here")
        return

    message = " ".join(context.args)
    all_users = get_all_user_ids()
    for uid in all_users:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 Broadcast from Admin:\n\n{message}")
        except Exception:
            continue

    await update.message.reply_text("✅ Broadcast sent!")

# ------------------- IMAGE HANDLER -------------------
async def remove_background(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user)
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

        # Increment user stats
        increment_user_photos(user.id)

        # Notify admin(s)
        username = f"@{user.username}" if user.username else user.full_name
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"✅ {username} just removed a photo background."
                )
            except Exception:
                continue

        await update.message.reply_text("✅ Your image is ready!")
    else:
        await update.message.reply_text("❌ Error removing background.")

# ------------------- MAIN -------------------
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))

    # Image handler
    app.add_handler(MessageHandler(filters.PHOTO, remove_background))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
