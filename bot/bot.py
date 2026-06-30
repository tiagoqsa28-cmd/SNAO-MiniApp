from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8533438456:AAF3B6_MhLoDnPXhi-YSDZT25p1bVMAp02k"

MINI_APP_URL = "https://snao-miniapp.onrender.com"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                text="🚀 Open SNAO Mini App",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🌊 Welcome to SNAO SYSTEM!\n\n"
        "Mine. Complete quests. Build the sardine movement.\n\n"
        "Tap the button below to open the Mini App.",
        reply_markup=reply_markup
    )


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("SNAO Telegram Bot running...")
    print("Mini App URL:", MINI_APP_URL)

    app.run_polling()


if __name__ == "__main__":
    main()
