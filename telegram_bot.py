"""
Telegram integration for GMGNBot.

Keeps all python-telegram-bot setup and command wiring in a separate module.
"""

from typing import Any

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes, Defaults
    from telegram.constants import ParseMode
except ImportError:  # pragma: no cover - handled by caller
    Update = None
    Application = None
    CommandHandler = None
    ContextTypes = None
    Defaults = None
    ParseMode = None


async def _start(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    await update.message.reply_text("GMGN Scraping Bot is ready! Use /help_gmgn for commands.")


async def _help_gmgn(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    help_text = """
**GMGN Scraping Bot Commands:**

/fbuy [address] [period] - First buy wallets
/pro [address] [period] - Profitable wallets
/ht [address] [period] - How long wallet holds tokens
/mpro [period] - Most profitable wallets
/pd [period] - Profitable deployers
/lowtxp [period] [tx_min] [tx_max] - Low TX profitable wallets
/kol [kol_name] [period] - KOL profitability
/hvol [period] - High volume wallets
/hact [period] - High activity wallets

Periods: 1d, 7d, 30d
    """
    await update.message.reply_text(help_text)


def setup_telegram_handlers(application: "Application", gmgn_bot: Any) -> None:
    """Setup Telegram command handlers."""
    application.add_handler(CommandHandler("start", _start))
    application.add_handler(CommandHandler("help_gmgn", _help_gmgn))

    async def fbuy(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /fbuy [address] [period]")
            return
        address = context.args[0]
        period = context.args[1] if len(context.args) > 1 else "7d"
        response = await gmgn_bot.handle_fbuy(address, period)
        await update.message.reply_text(response)

    async def pro(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /pro [address] [period]")
            return
        address = context.args[0]
        period = context.args[1] if len(context.args) > 1 else "7d"
        response = await gmgn_bot.handle_pro(address, period)
        await update.message.reply_text(response)

    async def ht(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /ht [address] [period]")
            return
        address = context.args[0]
        period = context.args[1] if len(context.args) > 1 else "7d"
        response = await gmgn_bot.handle_ht(address, period)
        await update.message.reply_text(response)

    async def mpro(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        period = context.args[0] if len(context.args) > 0 else "7d"
        response = await gmgn_bot.handle_mpro(period)
        await update.message.reply_text(response)

    async def pd(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        period = context.args[0] if len(context.args) > 0 else "7d"
        response = await gmgn_bot.handle_pd(period)
        await update.message.reply_text(response)

    async def lowtxp(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        if len(context.args) < 3:
            await update.message.reply_text("Usage: /lowtxp [period] [tx_min] [tx_max]")
            return
        period = context.args[0]
        tx_min = int(context.args[1])
        tx_max = int(context.args[2])
        response = await gmgn_bot.handle_lowtxp(period, tx_min, tx_max)
        await update.message.reply_text(response)

    async def kol(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /kol [kol_name] [period]")
            return
        kol_name = context.args[0]
        period = context.args[1] if len(context.args) > 1 else "7d"
        response = await gmgn_bot.handle_kol(kol_name, period)
        await update.message.reply_text(response)

    async def hvol(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        period = context.args[0] if len(context.args) > 0 else "7d"
        response = await gmgn_bot.handle_hvol(period)
        await update.message.reply_text(response)

    async def hact(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        period = context.args[0] if len(context.args) > 0 else "7d"
        response = await gmgn_bot.handle_hact(period)
        await update.message.reply_text(response)

    application.add_handler(CommandHandler("fbuy", fbuy))
    application.add_handler(CommandHandler("pro", pro))
    application.add_handler(CommandHandler("ht", ht))
    application.add_handler(CommandHandler("mpro", mpro))
    application.add_handler(CommandHandler("pd", pd))
    application.add_handler(CommandHandler("lowtxp", lowtxp))
    application.add_handler(CommandHandler("kol", kol))
    application.add_handler(CommandHandler("hvol", hvol))
    application.add_handler(CommandHandler("hact", hact))


def run_telegram_bot(token: str, gmgn_bot: Any) -> None:
    """Run Telegram bot."""
    if Application is None:
        raise ImportError("python-telegram-bot not installed. Install with: pip install python-telegram-bot")

    defaults = Defaults(parse_mode=ParseMode.HTML)
    application = Application.builder().token(token).defaults(defaults).build()
    setup_telegram_handlers(application, gmgn_bot)
    application.run_polling()



