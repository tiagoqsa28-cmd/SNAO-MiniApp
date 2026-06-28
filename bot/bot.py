from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8533438456:AAHvKSKE4CpkT21VVi-ox5nasZTQaP0OmQI"

MINI_APP_URL = "https://batting-snap-swinger.ngrok-free.dev/index.html?v=flowmap98"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                text="🚀 Open SNAO Mini App",
                web_app=WebAppInfo(url="https://batting-snap-swinger.ngrok-free.dev/index.html?v=flowmap98")
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