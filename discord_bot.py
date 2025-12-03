"""
Discord integration for GMGNBot.

Keeps all Discord-specific setup and command wiring in a separate module.
"""

from typing import Any

try:
    import discord
    from discord.ext import commands
except ImportError:  # pragma: no cover - handled by caller
    discord = None
    commands = None


def create_discord_bot(gmgn_bot: Any) -> "commands.Bot":
    """Create and configure the Discord bot instance."""
    if discord is None or commands is None:
        raise ImportError("discord.py not installed. Install with: pip install discord.py")

    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        print(f"✅ {bot.user} has connected to Discord!")

    @bot.command(name="fbuy")
    async def fbuy_command(ctx, address: str, period: str = "7d"):
        """First buy wallets of any token"""
        async with ctx.typing():
            response = await gmgn_bot.handle_fbuy(address, period)
            await ctx.send(response)

    @bot.command(name="pro")
    async def pro_command(ctx, address: str, period: str = "7d"):
        """Profitable wallets in any specific token"""
        async with ctx.typing():
            response = await gmgn_bot.handle_pro(address, period)
            await ctx.send(response)

    @bot.command(name="ht")
    async def ht_command(ctx, address: str, period: str = "7d"):
        """How long wallet holds tokens (profit statistics)"""
        async with ctx.typing():
            response = await gmgn_bot.handle_ht(address, period)
            await ctx.send(response)

    @bot.command(name="mpro")
    async def mpro_command(ctx, period: str = "7d"):
        """Most profitable wallets on BSC"""
        async with ctx.typing():
            response = await gmgn_bot.handle_mpro(period)
            await ctx.send(response)

    @bot.command(name="pd")
    async def pd_command(ctx, period: str = "7d"):
        """Most profitable token deployers in BSC chain"""
        async with ctx.typing():
       	    response = await gmgn_bot.handle_pd(period)
            await ctx.send(response)

    @bot.command(name="lowtxp")
    async def lowtxp_command(ctx, period: str = "7d", tx_min: int = 1, tx_max: int = 10):
        """Profitable wallets with low number of transactions"""
        async with ctx.typing():
            response = await gmgn_bot.handle_lowtxp(period, tx_min, tx_max)
            await ctx.send(response)

    @bot.command(name="kol")
    async def kol_command(ctx, kol_name: str, period: str = "7d"):
        """KOL wallet profitability"""
        async with ctx.typing():
            response = await gmgn_bot.handle_kol(kol_name, period)
            await ctx.send(response)

    @bot.command(name="hvol")
    async def hvol_command(ctx, period: str = "7d"):
        """High-volume wallets in BSC chain"""
        async with ctx.typing():
            response = await gmgn_bot.handle_hvol(period)
            await ctx.send(response)

    @bot.command(name="hact")
    async def hact_command(ctx, period: str = "7d"):
        """High-activity wallets in BSC chain"""
        async with ctx.typing():
            response = await gmgn_bot.handle_hact(period)
            await ctx.send(response)

    @bot.command(name="help_gmgn")
    async def help_command(ctx):
        """Show all available commands"""
        help_text = """
**GMGN Scraping Bot Commands:**

`/fbuy [address] [period]` - First buy wallets of any token on BSC
  Example: `/fbuy 0x1234...abcd 7d`

`/pro [address] [period]` - Profitable wallets in any specific token
  Example: `/pro 0x1234...abcd 7d`

`/ht [address] [period]` - How long wallet holds tokens (profit statistics)
  Example: `/ht 0x1234...abcd 7d`

`/mpro [period]` - Most profitable wallets on BSC
  Example: `/mpro 7d`

`/pd [period]` - Most profitable token deployers in BSC chain
  Example: `/pd 7d`

`/lowtxp [period] [tx_min] [tx_max]` - Profitable wallets with low transactions
  Example: `/lowtxp 7d 1 10`

`/kol [kol_name] [period]` - KOL wallet profitability
  Example: `/kol some_kol 7d`

`/hvol [period]` - High-volume wallets in BSC chain
  Example: `/hvol 7d`

`/hact [period]` - High-activity wallets in BSC chain
  Example: `/hact 7d`

**Periods:** 1d, 7d, 30d (default: 7d)
        """
        await ctx.send(help_text)

    return bot


def run_discord_bot(token: str, gmgn_bot: Any) -> None:
    """Run Discord bot with provided token and GMGNBot instance."""
    bot = create_discord_bot(gmgn_bot)
    bot.run(token)



