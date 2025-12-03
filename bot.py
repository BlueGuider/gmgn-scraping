"""
GMGN Scraping Bot - core logic + entrypoint.

This file now contains:
- The framework-agnostic `GMGNBot` class (all GMGN-specific logic/formatting)
- A small `__main__` entrypoint which delegates to:
  - `discord_bot.run_discord_bot`
  - `telegram_bot.run_telegram_bot`
"""

import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from gmgn_client import GMGNClient


class GMGNBot:
    """Bot interface for GMGN commands"""
    
    def __init__(self, cookies=None):
        # Try to load cookies and device IDs from config if not provided
        device_id = None
        fp_did = None
        
        if cookies is None:
            try:
                from config import COOKIES, DEVICE_ID, FP_DID
                cookies = COOKIES if COOKIES else None
                device_id = DEVICE_ID
                fp_did = FP_DID
            except (ImportError, AttributeError):
                pass
        self.client = GMGNClient(cookies=cookies, device_id=device_id, fp_did=fp_did)
    
    def parse_period(self, period: str) -> str:
        """Parse period string to API format"""
        period = period.lower().strip()
        if period in ['1d', '1', 'day', 'daily']:
            return '1d'
        elif period in ['7d', '7', 'week', 'weekly']:
            return '7d'
        elif period in ['30d', '30', 'month', 'monthly']:
            return '30d'
        return '7d'  # default
    
    def format_address(self, address: str) -> Optional[str]:
        """Validate and format wallet/token address"""
        address = address.strip()
        # Basic validation for BSC addresses (0x followed by 40 hex chars)
        if re.match(r'^0x[a-fA-F0-9]{40}$', address):
            return address
        return None
    
    def format_response(self, data: Dict, command: str, period: str = "7d") -> str:
        """Format API response for display"""
        if 'error' in data:
            return f"❌ Error: {data['error']}"
        
        # Check API response structure: {code, msg, data: {rank: [...]}}
        if not data or 'data' not in data:
            return "⚠️ No data available"
        
        api_data = data.get('data', {})
        
        # Handle rank endpoint response (data.rank is array)
        if 'rank' in api_data and isinstance(api_data['rank'], list):
            return self._format_wallet_list(api_data['rank'], command, period)
        
        # Handle other response structures
        return self._format_data(api_data, command)
    
    def _format_data(self, data: Any, command: str) -> str:
        """Generic fallback formatter (used when we don't have a special list format)."""
        if isinstance(data, list):
            if len(data) == 0:
                return "📭 No results found"
            result = []
            for i, item in enumerate(data[:10], 1):
                if isinstance(item, dict):
                    formatted = self._format_item(item, command)
                    result.append(f"{i}. {formatted}")
            return "\n".join(result) if result else "📭 No results found"

        if isinstance(data, dict):
            return self._format_item(data, command)

        return str(data)
    
    def _format_wallet_list(self, wallets: list, command: str, period: str = "7d") -> str:
        """Format wallet list with beautiful Telegram-style formatting"""
        if not wallets or len(wallets) == 0:
            return "📭 No wallets found"
        
        # Limit to top 10
        wallets = wallets[:10]
        
        # Period display names
        period_names = {
            '1d': '1 Day',
            '7d': '7 Days',
            '30d': '30 Days'
        }
        period_display = period_names.get(period, period)
        
        # Command-specific headers
        headers = {
            'mpro': (f'💰 Most Profitable Wallets Over the Last {period_display}', 
                    f'📈 Below is a list of the most profitable wallets based on their transaction activity and earnings during this period. These wallets have shown strong performance and smart trading behavior that contributed to significant gains. Dive into the details to see who\'s leading the profit charts! 🚀💼'),
            'hvol': (f'💰 High Volume Wallets Over the Last {period_display}',
                    "📈 Below is a list of high volume wallets based on their transaction activity and earnings during this period. These wallets have shown strong performance and smart trading behavior that contributed to significant gains. Dive into the details to see who's leading the profit charts! 🚀💼"),
            'hact': (f'💰 High Transaction Wallets Over the Last {period_display}',
                    "📈 Below is a list of high transaction wallets based on their transaction activity and earnings during this period. These wallets have shown strong performance and smart trading behavior that contributed to significant gains. Dive into the details to see who\'s leading the profit charts! 🚀💼"),
            'pro': ('💎 Profitable Wallets',
                    f'✨ These wallets have shown profitability in their trading activities over the last {period_display}.'),
            'fbuy': ('🎯 First Buy Wallets',
                    f'🏆 These wallets were among the first to buy this token. Early adopters often have significant advantages!'),
        }
        
        header_title, header_desc = headers.get(command, (f'📋 Wallet Rankings ({period})', f'Top wallets for the last {period}'))
        
        lines = [f"{header_title}", "", header_desc, ""]

        # Format each wallet
        for i, wallet in enumerate(wallets, 1):
            if command == "fbuy":
                body = self._format_first_buy_wallet_item(wallet)
            elif command == "hact":
                body = self._format_high_activity_wallet_item(wallet, period)
            elif command == "hvol":
                body = self._format_high_volume_wallet_item(wallet, period)
            else:
                body = self._format_wallet_item(wallet, period)
            lines.append(f"{i}. {body}")
            if i < len(wallets):
                lines.append("")  # Empty line between wallets
        
        return "\n".join(lines)
    
    def _format_wallet_item(self, wallet: Dict, period: str = "7d") -> str:
        """Format individual wallet item with beautiful formatting"""
        parts = []
        
        # Wallet address (full address, formatted as code for easy copying)
        address = wallet.get('address') or wallet.get('wallet_address') or wallet.get('wallet', 'N/A')
        if address and address != 'N/A':
            # Use HTML <code> tag so it's copiable in Telegram (parse_mode=HTML)
            parts.append(f"   <code>{address}</code>")
        
        # Profit (realized profit) - format like example
        profit_fields = {
            '1d': 'realized_profit_1d',
            '7d': 'realized_profit_7d',
            '30d': 'realized_profit_30d'
        }
        profit_field = profit_fields.get(period, 'realized_profit_7d')
        profit = wallet.get(profit_field) or wallet.get('realized_profit') or wallet.get('profit')
        if profit is not None:
            # Convert to float if string
            try:
                if isinstance(profit, str):
                    profit = float(profit)
            except (ValueError, TypeError):
                pass
            
            if isinstance(profit, (int, float)):
                # Format like example: $101.6M, $6.8M, etc.
                abs_profit = abs(profit)
                if abs_profit >= 1000000:
                    profit_str = f"${abs_profit/1000000:.1f}M"
                elif abs_profit >= 1000:
                    profit_str = f"${abs_profit/1000:.1f}K"
                else:
                    profit_str = f"${profit:,.2f}"
            else:
                profit_str = str(profit)
            parts.append(f"   💵 Profit: {profit_str}")
        else:
            parts.append(f"   💵 Profit: $0.00")
        
        # Unrealized profit (always show, default to $0.00)
        # Note: API might not have unrealized_profit, so we show $0.00
        unrealized = wallet.get('unrealized_profit')
        if unrealized is not None and unrealized != 0:
            if isinstance(unrealized, (int, float)):
                unrealized_str = f"${unrealized:,.2f}"
            else:
                unrealized_str = str(unrealized)
            parts.append(f"   💎 Unrealized Profit: {unrealized_str}")
        else:
            parts.append(f"   💎 Unrealized Profit: $0.00")
        
        # Win rate with wins/losses
        winrate_field = f'winrate_{period}' if period in ['1d', '7d', '30d'] else 'winrate_7d'
        winrate = wallet.get(winrate_field) or wallet.get('winrate')
        
        # Get buy/sell counts for period
        buy_field = f'buy_{period}' if period in ['1d', '7d', '30d'] else 'buy_30d'
        sell_field = f'sell_{period}' if period in ['1d', '7d', '30d'] else 'sell_30d'
        buy = wallet.get(buy_field) or wallet.get('buy', 0)
        sell = wallet.get(sell_field) or wallet.get('sell', 0)
        
        if winrate is not None:
            # Convert to percentage: if <= 1, it's decimal (0.785 = 78.5%), if > 1 it's already percentage
            try:
                winrate_float = float(winrate)
                if winrate_float <= 1.0:
                    # Decimal format (0.0 to 1.0) - convert to percentage
                    winrate_pct = winrate_float * 100
                else:
                    # Already percentage format
                    winrate_pct = winrate_float
            except (ValueError, TypeError):
                winrate_pct = winrate
            
            # Calculate wins and losses from winrate and total trades
            total_trades = buy + sell if (buy and sell) else (wallet.get('txs') or wallet.get(f'txs_{period}') or wallet.get('txs_30d', 0))
            if total_trades and winrate:
                # Use decimal winrate for calculation
                winrate_decimal = float(winrate) if float(winrate) <= 1.0 else float(winrate) / 100
                wins = int(total_trades * winrate_decimal)
                losses = total_trades - wins
                # Use period-specific label
                period_label = {
                    '1d': '1 Day',
                    '7d': '7 Days',
                    '30d': '30 Days'
                }.get(period, '7 Days')
                parts.append(f"   📊 7 Days Win Rate: {winrate_pct:.1f}% ({wins}W/{losses}L)")
            else:
                period_label = {
                    '1d': '1 Day',
                    '7d': '7 Days',
                    '30d': '30 Days'
                }.get(period, '7 Days')
                parts.append(f"   📊 7 Days Win Rate: {winrate_pct:.1f}%")
        else:
            # No winrate available
            period_label = {
                '1d': '1 Day',
                '7d': '7 Days',
                '30d': '30 Days'
            }.get(period, '7 Days')
            parts.append(f"   📊 7 Days Win Rate: N/A")
        
        # Trades (Buy/Sell) - format like example
        if buy and sell:
            total = buy + sell
            parts.append(f"   🔄 Trades: {total} (B: {buy} / S: {sell})")
        else:
            total_trades = wallet.get('txs') or wallet.get(f'txs_{period}') or wallet.get('txs_30d', 0)
            if total_trades:
                parts.append(f"   🔄 Trades: {total_trades}")
            else:
                parts.append(f"   🔄 Trades: 0")
        
        # Average hold time - use avg_holding_period_{period} (in seconds)
        period_suffix = {
            '1d': '1d',
            '7d': '7d',
            '30d': '30d'
        }.get(period, '7d')
        
        hold_time_seconds = (
            wallet.get(f'avg_holding_period_{period_suffix}') or
            wallet.get('avg_holding_period') or
            wallet.get('avg_hold_time') or
            0
        )
        
        # Format as "X days Y hours Z minutes"
        def format_hold_time(seconds):
            if seconds is None or seconds == 0:
                return "N/A"
            try:
                secs = float(seconds)
                if secs < 0:
                    return "N/A"
                
                days = int(secs // 86400)
                hours = int((secs % 86400) // 3600)
                minutes = int((secs % 3600) // 60)
                
                parts_list = []
                if days > 0:
                    parts_list.append(f"{days} day{'s' if days != 1 else ''}")
                if hours > 0:
                    parts_list.append(f"{hours} hour{'s' if hours != 1 else ''}")
                if minutes > 0:
                    parts_list.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
                
                if parts_list:
                    return " ".join(parts_list)
                else:
                    return "Less than 1 minute"
            except (ValueError, TypeError):
                return "N/A"
        
        hold_time_str = format_hold_time(hold_time_seconds)
        parts.append(f"   ⏱️ Avg Hold Time: {hold_time_str}")
        
        return "\n".join(parts)

    def _format_high_activity_wallet_item(self, wallet: Dict, period: str = "7d") -> str:
        """
        Format a high-activity wallet entry for /hact in the requested style.

        Example:
        1. 0x...
           🔄 Trades: 443,299
           ⏱️ Avg Daily Trades: 443,299.0
           💵 Volume: $30.69M
           ⏱️ Avg Trade Size: $69.23
           🕒 Last Trade: 2025-08-30 06:59:56 UTC
           💎 Profit: $2.4M
           🔶 Unrealized Profit: $0.00
           📊 1 Day Win Rate: 50.0% (10W/10L)
        """
        parts: list[str] = []

        # Wallet address (full, copiable)
        addr = wallet.get("address") or wallet.get("wallet_address") or wallet.get("wallet") or "N/A"
        parts.append(f"{addr}")

        # Helpers
        def fmt_money(val, default="$0.00"):
            if val is None:
                return default
            try:
                v = float(val)
                abs_v = abs(v)
                if abs_v >= 1_000_000:
                    return f"${abs_v/1_000_000:.2f}M"
                elif abs_v >= 1_000:
                    return f"${abs_v/1_000:.2f}K"
                else:
                    return f"${v:,.2f}"
            except (ValueError, TypeError):
                return str(val) if val else default

        def fmt_timestamp(ts, default="N/A"):
            if ts is None or ts == 0:
                return default
            try:
                if isinstance(ts, str):
                    ts = ts.rstrip(".0")
                ts_val = float(ts)
                if ts_val > 0:
                    dt = datetime.fromtimestamp(ts_val, timezone.utc)
                    # Explicit UTC suffix as in example
                    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                return default
            except (ValueError, TypeError, OSError):
                return default

        # Map period to suffix and days
        period_suffix = {
            "1d": ("1d", 1),
            "7d": ("7d", 7),
            "30d": ("30d", 30),
        }.get(period, ("7d", 7))
        suf, days = period_suffix

        # 🔄 Trades: total transactions over period
        total_txs = wallet.get(f"txs_{suf}") or wallet.get("txs") or 0
        try:
            total_txs_int = int(total_txs)
        except (ValueError, TypeError):
            total_txs_int = 0
        parts.append(f"   🔄 Trades: {total_txs_int:,}")

        # ⏱️ Avg Daily Trades
        if days > 0:
            avg_daily = total_txs_int / days
        else:
            avg_daily = 0.0
        parts.append(f"   ⏱️ Avg Daily Trades: {avg_daily:,.1f}")

        # 💵 Volume: use volume_{period} if available
        volume = wallet.get(f"volume_{suf}") or wallet.get("volume") or 0
        parts.append(f"   💵 Volume: {fmt_money(volume)}")

        # ⏱️ Avg Trade Size: volume / trades
        try:
            vol_val = float(volume or 0)
            avg_trade = vol_val / total_txs_int if total_txs_int > 0 else 0.0
        except (ValueError, TypeError):
            avg_trade = 0.0
        parts.append(f"   ⏱️ Avg Trade Size: {fmt_money(avg_trade)}")

        # 🕒 Last Trade: last_active or last_active_timestamp
        last_ts = wallet.get("last_active") or wallet.get("last_active_timestamp") or 0
        parts.append(f"   🕒 Last Trade: {fmt_timestamp(last_ts)}")

        # 💎 Profit: realized profit over period
        realized = wallet.get(f"realized_profit_{suf}") or wallet.get("realized_profit") or 0
        parts.append(f"   💎 Profit: {fmt_money(realized)}")

        # 🔶 Unrealized Profit
        unrealized = wallet.get("unrealized_profit") or 0
        parts.append(f"   🔶 Unrealized Profit: {fmt_money(unrealized)}")

        # 📊 Win Rate: X% (W/L)
        winrate = wallet.get(f"winrate_{suf}") or wallet.get("winrate") or 0
        try:
            wr_val = float(winrate)
            if wr_val <= 1.0:
                wr_pct = wr_val * 100
                wr_dec = wr_val
            else:
                wr_pct = wr_val
                wr_dec = wr_val / 100.0
        except (ValueError, TypeError):
            wr_pct = 0.0
            wr_dec = 0.0

        wins = int(total_txs_int * wr_dec)
        losses = max(total_txs_int - wins, 0)

        period_label = {
            "1d": "1 Day",
            "7d": "7 Days",
            "30d": "30 Days",
        }.get(period, "7 Days")

        parts.append(f"   📊 {period_label} Win Rate: {wr_pct:.1f}% ({wins}W/{losses}L)")
        
        return "\n".join(parts)

    def _format_high_volume_wallet_item(self, wallet: Dict, period: str = "7d") -> str:
        """
        Format a high-volume wallet entry for /hvol in the requested style.

        Example:
        1. BMnT51N4iSNhWU5PyFFgWwFvN1jgaiiDr9ZHgnkm3iLJ
           💵 Volume: $718.03M
           🔄 Trades: 248,077
           ⏱️ Avg Trade Size: $2.89K
           💵 Profit: $77.3K
           💎 Unrealized Profit: $0.00
           📊 7 Days Win Rate: 100.0% (1W/0L)
           🕒 Last Trade: 2025-08-30 06:59:47.000 UTC
        """
        parts: list[str] = []

        # Wallet address (full, copiable)
        addr = wallet.get("address") or wallet.get("wallet_address") or wallet.get("wallet") or "N/A"
        parts.append(f"   <code>{addr}</code>")

        # Helpers
        def fmt_money(val, default="$0.00"):
            if val is None:
                return default
            try:
                v = float(val)
                abs_v = abs(v)
                if abs_v >= 1_000_000:
                    return f"${abs_v/1_000_000:.2f}M"
                elif abs_v >= 1_000:
                    return f"${abs_v/1_000:.2f}K"
                else:
                    return f"${v:,.2f}"
            except (ValueError, TypeError):
                return str(val) if val else default

        def fmt_timestamp(ts, default="N/A"):
            if ts is None or ts == 0:
                return default
            try:
                if isinstance(ts, str):
                    ts = ts.rstrip(".0")
                ts_val = float(ts)
                if ts_val > 0:
                    dt = datetime.fromtimestamp(ts_val, timezone.utc)
                    # Explicit UTC suffix with milliseconds as in example
                    return dt.strftime("%Y-%m-%d %H:%M:%S.000 UTC")
                return default
            except (ValueError, TypeError, OSError):
                return default

        # Map period to suffix
        period_suffix = {
            "1d": "1d",
            "7d": "7d",
            "30d": "30d",
        }.get(period, "7d")
        suf = period_suffix

        # 💵 Volume: calculate as avg_cost * txs (this is the key metric for high volume)
        avg_cost = wallet.get(f"avg_cost_{suf}") or wallet.get("avg_cost") or 0
        txs = wallet.get(f"txs_{suf}") or wallet.get("txs") or 0
        try:
            avg_cost_val = float(avg_cost) if avg_cost else 0.0
            txs_val = int(txs) if txs else 0
            calculated_volume = avg_cost_val * txs_val
        except (ValueError, TypeError):
            calculated_volume = wallet.get("_calculated_volume") or wallet.get(f"volume_{suf}") or wallet.get("volume") or 0
        
        parts.append(f"   💵 Volume: {fmt_money(calculated_volume)}")

        # 🔄 Trades: total transactions over period
        total_txs = wallet.get(f"txs_{suf}") or wallet.get("txs") or 0
        try:
            total_txs_int = int(total_txs)
        except (ValueError, TypeError):
            total_txs_int = 0
        parts.append(f"   🔄 Trades: {total_txs_int:,}")

        # ⏱️ Avg Trade Size: calculated_volume / trades (or use avg_cost directly)
        try:
            avg_trade = calculated_volume / total_txs_int if total_txs_int > 0 else avg_cost_val
        except (ValueError, TypeError, ZeroDivisionError):
            avg_trade = 0.0
        parts.append(f"   ⏱️ Avg Trade Size: {fmt_money(avg_trade)}")

        # 💵 Profit: realized profit over period
        realized = wallet.get(f"realized_profit_{suf}") or wallet.get("realized_profit") or 0
        parts.append(f"   💵 Profit: {fmt_money(realized)}")

        # 💎 Unrealized Profit
        unrealized = wallet.get("unrealized_profit") or 0
        parts.append(f"   💎 Unrealized Profit: {fmt_money(unrealized)}")

        # 📊 Win Rate: X% (W/L)
        winrate = wallet.get(f"winrate_{suf}") or wallet.get("winrate") or 0
        try:
            wr_val = float(winrate)
            if wr_val <= 1.0:
                wr_pct = wr_val * 100
                wr_dec = wr_val
            else:
                wr_pct = wr_val
                wr_dec = wr_val / 100.0
        except (ValueError, TypeError):
            wr_pct = 0.0
            wr_dec = 0.0

        wins = int(total_txs_int * wr_dec)
        losses = max(total_txs_int - wins, 0)

        period_label = {
            "1d": "1 Day",
            "7d": "7 Days",
            "30d": "30 Days",
        }.get(period, "7 Days")

        parts.append(f"   📊 {period_label} Win Rate: {wr_pct:.1f}% ({wins}W/{losses}L)")

        # 🕒 Last Trade: last_active or last_active_timestamp
        last_ts = wallet.get("last_active") or wallet.get("last_active_timestamp") or 0
        parts.append(f"   🕒 Last Trade: {fmt_timestamp(last_ts)}")
        
        return "\n".join(parts)

    def _format_high_volume_wallets_response(self, wallets: list, period: str) -> str:
        """Format high volume wallets response with header"""
        if not wallets or len(wallets) == 0:
            return "📭 No high volume wallets found"
        
        # Period display names
        period_names = {
            '1d': '1 Day',
            '7d': '7 Days',
            '30d': '30 Days'
        }
        period_display = period_names.get(period, period)
        
        lines = [
            f"💰 High Volume Wallets Over the Last {period_display}",
            "",
            "📈 Below is a list of high volume wallets based on their transaction activity and earnings during this period. These wallets have shown strong performance and smart trading behavior that contributed to significant gains. Dive into the details to see who's leading the profit charts! 🚀💼",
            ""
        ]
        
        # Format each wallet
        for i, wallet in enumerate(wallets, 1):
            lines.append(f"{i}. {self._format_high_volume_wallet_item(wallet, period)}")
            if i < len(wallets):
                lines.append("")  # Empty line between wallets
        
        return "\n".join(lines)

    def _format_fbuy_response(self, wallets: list, token_address: str, token_name: str, token_symbol: str, 
                              deployer_address: str = None, deploy_timestamp: int = None, deploy_tx_hash: str = None) -> str:
        """Format the complete /fbuy response with header and enriched wallet data"""
        lines = []
        
        # Header
        lines.append(f"🛒 First Buyers Analysis for {token_name} ({token_symbol})")
        lines.append("")
        lines.append(f"📝 {token_address}")
        lines.append("")
        
        # Deployer section
        if deployer_address:
            lines.append("👨‍💻 Deployer:")
            lines.append(f"• 💼 {deployer_address}")
            
            # Deploy time
            if deploy_timestamp:
                try:
                    # Handle both string and numeric timestamps
                    if isinstance(deploy_timestamp, str):
                        deploy_timestamp = deploy_timestamp.rstrip('.0').strip()
                    ts_val = float(deploy_timestamp)
                    if ts_val > 0:
                        dt = datetime.fromtimestamp(ts_val, timezone.utc)
                        deploy_time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        lines.append(f"• 📅 {deploy_time_str}")
                    else:
                        lines.append("• 📅 N/A")
                except (ValueError, TypeError, OSError) as e:
                    lines.append(f"• 📅 N/A")
            else:
                lines.append("• 📅 N/A")
            
            # Deploy transaction hash (clickable link to BSCScan)
            if deploy_tx_hash:
                if len(deploy_tx_hash) > 20:
                    tx_short = f"{deploy_tx_hash[:10]}...{deploy_tx_hash[-10:]}"
                else:
                    tx_short = deploy_tx_hash
                # Create clickable link to BSCScan token page
                bscscan_url = f"https://bscscan.com/token/{token_address}"
                lines.append(f'• 📡 <a href="{bscscan_url}">{tx_short}</a>')
            else:
                # Even without tx hash, link to token page
                bscscan_url = f"https://bscscan.com/token/{token_address}"
                lines.append(f'• 📡 <a href="{bscscan_url}">View on BSCScan</a>')
            
            lines.append("")
        
        lines.append("🔍 First Buyers:")
        lines.append("")
        
        # Format each wallet
        for i, wallet in enumerate(wallets, 1):
            lines.append(f"{i}. {self._format_first_buy_wallet_item(wallet)}")
            if i < len(wallets):
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_first_buy_wallet_item(self, item: Dict) -> str:
        """
        Format a first-buy wallet entry for /fbuy in the exact style requested.
        
        Format:
        1. 0x...
           🛒 Buy Amount: 8.4B | $68.36
           🕒 Buy Time: 2025-05-10 14:27:47
           📊 Trades: 2 (B: 1 / S: 1)
           📈 Profit: $6.5K (R: $125.99 / U: $6.4K)
           🏆 Win Rate: 0.0%
           ⏱️ Last Active: 2025-05-10 15:13:47
        """
        parts: list[str] = []

        # Wallet address (plain, no code tags)
        addr = item.get("address") or item.get("wallet") or "N/A"
        if addr and addr != "N/A":
            parts.append(f"   {addr}")

        # Helper function to format money
        def format_money(val, default="N/A"):
            if val is None:
                return default
            try:
                v = float(val)
                abs_v = abs(v)
                if abs_v >= 1_000_000:
                    return f"${abs_v/1_000_000:.1f}M"
                elif abs_v >= 1_000:
                    return f"${abs_v/1_000:.1f}K"
                else:
                    return f"${v:,.2f}"
            except (ValueError, TypeError):
                return str(val) if val else default

        # Helper function to format amount
        def format_amount(val, default="N/A"):
            if val is None:
                return default
            try:
                a = float(val)
                abs_a = abs(a)
                if abs_a >= 1_000_000_000:
                    return f"{abs_a/1_000_000_000:.1f}B"
                elif abs_a >= 1_000_000:
                    return f"{abs_a/1_000_000:.1f}M"
                elif abs_a >= 1_000:
                    return f"{abs_a/1_000:.1f}K"
                else:
                    return f"{a:,.2f}"
            except (ValueError, TypeError):
                return str(val) if val else default

        # Helper function to format timestamp
        def format_timestamp(ts, default="N/A"):
            if ts is None or ts == 0:
                return default
            try:
                if isinstance(ts, str):
                    ts = ts.rstrip('.0')
                ts_val = float(ts)
                if ts_val > 0:
                    dt = datetime.fromtimestamp(ts_val, timezone.utc)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                return default
            except (ValueError, TypeError, OSError):
                return str(ts) if ts else default

        # 🛒 Buy Amount: 8.4B | $68.36
        # Use history_bought_amount and history_bought_cost from holding stats if available
        # Otherwise fall back to first buy amount/value
        buy_amount = item.get("history_bought_amount") or item.get("amount")
        buy_cost = item.get("history_bought_cost") or item.get("value_usd")
        if buy_amount and buy_cost:
            amt_str = format_amount(buy_amount)
            cost_str = format_money(buy_cost)
            parts.append(f"   🛒 Buy Amount: {amt_str} | {cost_str}")
        elif buy_amount:
            amt_str = format_amount(buy_amount)
            parts.append(f"   🛒 Buy Amount: {amt_str}")
        elif buy_cost:
            cost_str = format_money(buy_cost)
            parts.append(f"   🛒 Buy Amount: N/A | {cost_str}")
        else:
            parts.append("   🛒 Buy Amount: N/A")

        # 🕒 Buy Time: 2025-05-10 14:27:47 (YYYY-MM-DD HH:MM:SS format)
        buy_time = item.get("timestamp")
        if buy_time:
            time_str = format_timestamp(buy_time)
            parts.append(f"   🕒 Buy Time: {time_str}")
        else:
            parts.append("   🕒 Buy Time: N/A")

        # 📊 Trades: 2 (B: 1 / S: 1)
        buys = item.get("history_total_buys", 0)
        sells = item.get("history_total_sells", 0)
        total_trades = buys + sells
        if total_trades > 0:
            parts.append(f"   📊 Trades: {total_trades} (B: {buys} / S: {sells})")
        else:
            parts.append("   📊 Trades: 0")

        # 📈 Profit: $6.5K (R: $125.99 / U: $6.4K)
        realized = item.get("realized_profit", 0)
        unrealized = item.get("unrealized_profit", 0)
        total_profit = item.get("total_profit")
        if total_profit is None:
            try:
                total_profit = float(realized or 0) + float(unrealized or 0)
            except (ValueError, TypeError):
                total_profit = 0
        
        if total_profit or realized or unrealized:
            total_str = format_money(total_profit, "$0.00")
            r_str = format_money(realized, "$0.00")
            u_str = format_money(unrealized, "$0.00")
            parts.append(f"   📈 Profit: {total_str} (R: {r_str} / U: {u_str})")
        else:
            parts.append("   📈 Profit: $0.00 (R: $0.00 / U: $0.00)")

        # 🏆 Win Rate: 0.0%
        # Calculate win rate from buys/sells if available
        winrate = item.get("winrate") or item.get("winrate_7d")
        if winrate is not None:
            try:
                wr_val = float(winrate)
                if wr_val <= 1.0:
                    wr_pct = wr_val * 100
                else:
                    wr_pct = wr_val
                parts.append(f"   🏆 Win Rate: {wr_pct:.1f}%")
            except (ValueError, TypeError):
                parts.append("   🏆 Win Rate: 0.0%")
        else:
            # Default to 0.0% if no winrate available
            parts.append("   🏆 Win Rate: 0.0%")

        # ⏱️ Last Active: 2025-05-10 15:13:47
        last_active = item.get("last_active_timestamp")
        if last_active:
            active_str = format_timestamp(last_active)
            parts.append(f"   ⏱️ Last Active: {active_str}")
        else:
            parts.append("   ⏱️ Last Active: N/A")

        return "\n".join(parts)
    
    def _format_profitable_wallets_response(self, wallets: list, token_address: str, token_name: str, token_symbol: str) -> str:
        """Format profitable wallets response with header"""
        if not wallets or len(wallets) == 0:
            return "📭 No profitable wallets found"
        
        # Limit to top 10
        wallets = wallets[:10]
        
        lines = [
            f"💰 Most Profitable Wallets for {token_name} ({token_symbol})",
            "",
            f"📝 Contract: <code>{token_address}</code>",
            ""
        ]
        
        # Format each wallet
        for i, wallet in enumerate(wallets, 1):
            lines.append(f"{i}. {self._format_profitable_wallet_item(wallet)}")
            if i < len(wallets):
                lines.append("")  # Empty line between wallets
        
        return "\n".join(lines)
    
    def _format_profitable_wallet_item(self, item: Dict) -> str:
        """Format individual profitable wallet item"""
        parts = []
        
        # Helper functions (same as in _format_first_buy_wallet_item)
        def format_money(val, default="$0.00"):
            if val is None:
                return default
            try:
                v = float(val)
                abs_v = abs(v)
                if abs_v >= 1_000_000:
                    return f"${abs_v/1_000_000:.1f}M"
                elif abs_v >= 1_000:
                    return f"${abs_v/1_000:.1f}K"
                else:
                    return f"${v:,.2f}"
            except (ValueError, TypeError):
                return str(val) if val else default
        
        def format_amount(val, default="0"):
            if val is None:
                return default
            try:
                a = float(val)
                abs_a = abs(a)
                if abs_a >= 1_000_000_000:
                    return f"{abs_a/1_000_000_000:.1f}B tokens"
                elif abs_a >= 1_000_000:
                    return f"{abs_a/1_000_000:.1f}M tokens"
                elif abs_a >= 1_000:
                    return f"{abs_a/1_000:.1f}K tokens"
                else:
                    return f"{a:,.2f} tokens"
            except (ValueError, TypeError):
                return str(val) if val else default
        
        def format_timestamp(ts, default="N/A"):
            if ts is None or ts == 0:
                return default
            try:
                if isinstance(ts, str):
                    ts = ts.rstrip('.0')
                ts_val = float(ts)
                if ts_val > 0:
                    dt = datetime.fromtimestamp(ts_val, timezone.utc)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                return default
            except (ValueError, TypeError, OSError):
                return str(ts) if ts else default
        
        # Wallet address (copiable)
        wallet_addr = item.get('address') or item.get('wallet_address') or item.get('wallet')
        if wallet_addr:
            parts.append(f"<code>{wallet_addr}</code>")
        
        # 🔄 Total Trades: 177 (B: 79 / S: 98)
        buy_count = item.get('buy_tx_count_cur', 0)
        sell_count = item.get('sell_tx_count_cur', 0)
        total_trades = buy_count + sell_count
        if total_trades > 0:
            parts.append(f"   🔄 Total Trades: {total_trades} (B: {buy_count} / S: {sell_count})")
        else:
            parts.append("   🔄 Total Trades: 0")
        
        # 💵 Buy Volume: $16.6K
        buy_volume = item.get('buy_volume_cur', 0)
        parts.append(f"   💵 Buy Volume: {format_money(buy_volume)}")
        
        # 💸 Sell Volume: $27.0K
        sell_volume = item.get('sell_volume_cur', 0)
        parts.append(f"   💸 Sell Volume: {format_money(sell_volume)}")
        
        # 🟢 Buy Amount: 8.7B tokens
        buy_amount = item.get('buy_amount_cur', 0)
        parts.append(f"   🟢 Buy Amount: {format_amount(buy_amount)}")
        
        # 🔴 Sell Amount: 8.1B tokens
        sell_amount = item.get('sell_amount_cur', 0)
        parts.append(f"   🔴 Sell Amount: {format_amount(sell_amount)}")
        
        # 📈 Realized Profit: $11.3K
        realized_profit = item.get('realized_profit', 0)
        parts.append(f"   📈 Realized Profit: {format_money(realized_profit)}")
        
        # 📊 Unrealized Profit: -$582.76
        unrealized_profit = item.get('unrealized_profit', 0)
        parts.append(f"   📊 Unrealized Profit: {format_money(unrealized_profit)}")
        
        # 💰 Total Profit: $10.7K
        total_profit = item.get('profit', 0)
        if not total_profit:
            # Calculate from realized + unrealized if not provided
            try:
                total_profit = float(realized_profit or 0) + float(unrealized_profit or 0)
            except (ValueError, TypeError):
                total_profit = 0
        parts.append(f"   💰 Total Profit: {format_money(total_profit)}")
        
        # 🏷️ Token Source: 🛒 Purchased
        # Check if token was transferred in (not purchased)
        transfer_in = item.get('transfer_in', False)
        token_transfer = item.get('token_transfer', {})
        if transfer_in or token_transfer.get('type') == 'transfer_in':
            parts.append("   🏷️ Token Source: 📥 Transferred")
        else:
            parts.append("   🏷️ Token Source: 🛒 Purchased")
        
        # ⏱️ Last Active: 2025-04-08 04:34:47
        last_active = item.get('last_active_timestamp', 0)
        if last_active:
            active_str = format_timestamp(last_active)
            parts.append(f"   ⏱️ Last Active: {active_str}")
        else:
            parts.append("   ⏱️ Last Active: N/A")
        
        return "\n".join(parts)
    
    def _format_hold_time_response_from_trades(self, trades: list, token_address: str) -> str:
        """Format hold time statistics for a token from trades data"""
        if not trades or len(trades) == 0:
            return "📭 No trading data found"
        
        # Helper function to format time duration
        def format_duration(seconds, default="N/A"):
            if seconds is None or seconds == 0:
                return default
            try:
                secs = float(seconds)
                if secs < 0:
                    return default
                
                if secs < 60:
                    return f"{int(secs)} sec"
                elif secs < 3600:
                    mins = secs / 60
                    return f"{mins:.1f} mins"
                elif secs < 86400:
                    hours = secs / 3600
                    return f"{hours:.1f} hours"
                else:
                    days = secs / 86400
                    return f"{days:.1f} days"
            except (ValueError, TypeError):
                return default
        
        # Helper function to format timestamp
        def format_timestamp(ts, default="N/A"):
            if ts is None or ts == 0:
                return default
            try:
                if isinstance(ts, str):
                    ts = ts.rstrip('.0')
                ts_val = float(ts)
                if ts_val > 0:
                    dt = datetime.fromtimestamp(ts_val, timezone.utc)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                return default
            except (ValueError, TypeError, OSError):
                return str(ts) if ts else default
        
        # Helper to get timestamp from trade
        def get_trade_timestamp(trade: Dict) -> float:
            for key in ("timestamp", "ts", "time", "block_time", "created_at"):
                if key in trade:
                    try:
                        val = trade[key]
                        if isinstance(val, (int, float)):
                            return float(val)
                        return float(val)
                    except (ValueError, TypeError):
                        continue
            return 0.0
        
        # Helper to determine if trade is buy or sell
        def is_buy_trade(trade: Dict) -> bool:
            side = trade.get("event") or trade.get("side") or trade.get("trade_type") or trade.get("direction")
            if side:
                return str(side).lower() in ("buy", "b", "1", "true")
            # Check maker_token_tags for creator/deployer (skip these)
            tags = trade.get("maker_token_tags", []) + trade.get("maker_event_tags", [])
            if any(tag in ("creator", "deployer", "owner") for tag in [str(t).lower() for t in tags]):
                return False
            # Default: assume buy if we can't determine
            return True
        
        # Group trades by wallet and separate buys/sells
        wallet_trades: Dict[str, Dict[str, list]] = {}  # {wallet: {"buys": [], "sells": []}}
        total_buy_trades = 0
        total_sell_trades = 0
        last_active_times = []
        
        for trade in trades:
            if not isinstance(trade, dict):
                continue
            
            # Get wallet address
            wallet = trade.get("maker") or trade.get("address") or trade.get("wallet") or trade.get("wallet_address")
            if not wallet:
                continue
            
            # Skip dev/creator trades
            tags = trade.get("maker_token_tags", []) + trade.get("maker_event_tags", [])
            if any(tag in ("creator", "deployer", "owner") for tag in [str(t).lower() for t in tags]):
                continue
            
            if wallet not in wallet_trades:
                wallet_trades[wallet] = {"buys": [], "sells": []}
            
            timestamp = get_trade_timestamp(trade)
            if timestamp > 0:
                last_active_times.append(timestamp)
            
            if is_buy_trade(trade):
                wallet_trades[wallet]["buys"].append((timestamp, trade))
                total_buy_trades += 1
            else:
                wallet_trades[wallet]["sells"].append((timestamp, trade))
                total_sell_trades += 1
        
        # Calculate hold times by matching buy-sell pairs
        hold_times = []
        for wallet, trade_lists in wallet_trades.items():
            buys = sorted(trade_lists["buys"], key=lambda x: x[0])  # Sort by timestamp
            sells = sorted(trade_lists["sells"], key=lambda x: x[0])  # Sort by timestamp
            
            # Match each sell with the most recent buy before it
            for sell_ts, sell_trade in sells:
                if sell_ts <= 0:
                    continue
                
                # Find the most recent buy before this sell
                for buy_ts, buy_trade in reversed(buys):
                    if buy_ts > 0 and buy_ts < sell_ts:
                        hold_time_seconds = sell_ts - buy_ts
                        if hold_time_seconds > 0 and hold_time_seconds < 31536000 * 10:  # Less than 10 years
                            hold_times.append(hold_time_seconds)
                        break  # Match one buy per sell
        
        # Calculate statistics
        total_trades = total_buy_trades + total_sell_trades
        
        # Find shortest, longest, and average hold times
        shortest_hold = None
        longest_hold = None
        avg_hold = None
        
        if hold_times:
            shortest_hold = min(hold_times)
            longest_hold = max(hold_times)
            avg_hold = sum(hold_times) / len(hold_times)
        
        # Find most recent last active time
        last_active_str = "N/A"
        if last_active_times:
            most_recent = max(last_active_times)
            last_active_str = format_timestamp(most_recent)
        
        # Get token name/symbol from first trade
        token_name = "Unknown Token"
        token_symbol = "UNKNOWN"
        
        if trades:
            first_trade = trades[0] if isinstance(trades[0], dict) else None
            if first_trade:
                # Try to get from trade data
                token_name = first_trade.get('token_name') or first_trade.get('name') or token_name
                token_symbol = first_trade.get('token_symbol') or first_trade.get('symbol') or token_symbol
                
                # If not found, try to get from first wallet's holding stats
                if (token_name == "Unknown Token" or token_symbol == "UNKNOWN") and wallet_trades:
                    first_wallet = list(wallet_trades.keys())[0]
                    holding_stats = self.client.get_wallet_holding_stats(first_wallet, token_address)
                    if 'error' not in holding_stats and holding_stats.get('data'):
                        token_info = holding_stats['data'].get('token', {})
                        if token_info:
                            token_name = token_info.get('name', token_name)
                            token_symbol = token_info.get('symbol', token_symbol)
        
        # Format response
        lines = [
            f"⏱️ How long wallets hold {token_name} ({token_symbol})",
            "",
            f"📝 Contract: <code>{token_address}</code>",
            "",
            f"🔄 Total Trades (B: {total_buy_trades} / S: {total_sell_trades})",
        ]
        
        if shortest_hold is not None:
            lines.append(f"⌛️ Shortest hold time: {format_duration(shortest_hold)}")
        else:
            lines.append("⌛️ Shortest hold time: N/A")
        
        if longest_hold is not None:
            lines.append(f"⏳ Longest hold time: {format_duration(longest_hold)}")
        else:
            lines.append("⏳ Longest hold time: N/A")
        
        if avg_hold is not None:
            lines.append(f"⏲️ Average hold time: {format_duration(avg_hold)}")
        else:
            lines.append("⏲️ Average hold time: N/A")
        
        lines.append(f"⏱️ Last Active: {last_active_str}")
        
        return "\n".join(lines)
    
    def _format_wallet_profit_stat_response(self, data: Dict, wallet_address: str, period: str) -> str:
        """Format wallet profit statistics response with avg cost/sold and realized profits"""
        # Helper function to format money values
        def format_money(val, default="$0.00"):
            if val is None:
                return default
            try:
                v = float(val)
                abs_v = abs(v)
                if abs_v >= 1_000_000:
                    return f"${abs_v/1_000_000:.1f}M"
                elif abs_v >= 1_000:
                    return f"${abs_v/1_000:.1f}K"
                else:
                    return f"${v:,.2f}"
            except (ValueError, TypeError):
                return str(val) if val else default
        
        # Helper function to format timestamp
        def format_timestamp(ts, default="N/A"):
            if ts is None or ts == 0:
                return default
            try:
                if isinstance(ts, str):
                    ts = ts.rstrip('.0')
                ts_val = float(ts)
                if ts_val > 0:
                    dt = datetime.fromtimestamp(ts_val, timezone.utc)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                return default
            except (ValueError, TypeError, OSError):
                return str(ts) if ts else default
        
        # Helper function to format duration (seconds to days/hours/mins)
        def format_duration(seconds, default="N/A"):
            if seconds is None or seconds == 0:
                return default
            try:
                secs = float(seconds)
                if secs < 0:
                    return default
                
                if secs < 60:
                    return f"{int(secs)} sec"
                elif secs < 3600:
                    mins = secs / 60
                    return f"{mins:.1f} mins"
                elif secs < 86400:
                    hours = secs / 3600
                    return f"{hours:.1f} hours"
                else:
                    days = secs / 86400
                    return f"{days:.1f} days"
            except (ValueError, TypeError):
                return default
        
        lines = [
            "",
            f"💰 {period} Wallet Profit Statistics",
            ""
        ]
        
        # Wallet address
        lines.append(f"💼 <code>{wallet_address}</code>")
        # lines.append("")
        
        # Total Trades
        buy_count = data.get('buy', 0)
        sell_count = data.get('sell', 0)
        lines.append(f"🔄 Total Trades (B: {buy_count} S: {sell_count})")
        # lines.append("")
        
        # Avg Cost / Avg Sold
        # Calculate from total_bought_cost / buy_count and total_sold_income / sell_count
        total_bought_cost = (data.get('total_bought_cost') or 0)
        total_sold_income = (data.get('total_sold_income') or 0)
        
        # Calculate avg_cost = total_bought_cost / buy_count
        avg_cost = 0
        if buy_count > 0 and total_bought_cost:
            try:
                avg_cost = float(total_bought_cost) / float(buy_count)
            except (ValueError, TypeError, ZeroDivisionError):
                avg_cost = 0
        
        # Calculate avg_sold = total_sold_income / sell_count
        avg_sold = 0
        if sell_count > 0 and total_sold_income:
            try:
                avg_sold = float(total_sold_income) / float(sell_count)
            except (ValueError, TypeError, ZeroDivisionError):
                avg_sold = 0
        
        avg_cost_str = format_money(avg_cost, "$0.00")
        avg_sold_str = format_money(avg_sold, "$0.00")
        lines.append(f"💵 {period} Avg Cost / Avg Sold: {avg_cost_str} / {avg_sold_str}")
        # lines.append(f"   ")
        # lines.append("")
        
        # Avg Realized Profits
        realized_profit = (data.get('realized_profit') or 0)
        
        # Format with + sign for positive values
        try:
            realized_profit_val = float(realized_profit) if realized_profit else 0
        except (ValueError, TypeError):
            realized_profit_val = 0
        
        realized_profit_str = format_money(realized_profit_val, "$0.00")
        if realized_profit_val > 0:
            realized_profit_str = f"+{realized_profit_str}"
        
        lines.append(f"📈 {period} Realized Profits: {realized_profit_str}")
        # lines.append(f"   ")
        # lines.append("")
        
        # Average hold time
        avg_holding_period = data.get('avg_holding_period')
        if avg_holding_period:
            hold_time_str = format_duration(float(avg_holding_period))
            lines.append(f"⏲️ Average hold time: {hold_time_str}")
        else:
            lines.append("⏲️ Average hold time: N/A")
        
        # Last Active
        last_active = data.get('last_active_timestamp', 0)
        if last_active:
            active_str = format_timestamp(last_active)
            lines.append(f"⏱️ Last Active: {active_str}")
        else:
            lines.append("⏱️ Last Active: N/A")
        
        return "\n".join(lines)
    
    def _format_profitable_tokens_response(self, tokens: list, period: str, period_display: str) -> str:
        """Format profitable tokens response"""
        if not tokens or len(tokens) == 0:
            return "📭 No tokens found"
        
        # Limit to top 10
        tokens = tokens[:10]
        
        # Helper function to format money values
        def format_money(val, default="$0.00"):
            if val is None:
                return default
            try:
                v = float(val)
                abs_v = abs(v)
                if abs_v >= 1_000_000:
                    return f"${abs_v/1_000_000:.1f}M"
                elif abs_v >= 1_000:
                    return f"${abs_v/1_000:.1f}K"
                else:
                    return f"${v:,.2f}"
            except (ValueError, TypeError):
                return str(val) if val else default
        
        # Helper function to format timestamp
        def format_timestamp(ts, default="N/A"):
            if ts is None or ts == 0:
                return default
            try:
                if isinstance(ts, str):
                    ts = ts.rstrip('.0')
                ts_val = float(ts)
                if ts_val > 0:
                    dt = datetime.fromtimestamp(ts_val, timezone.utc)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                return default
            except (ValueError, TypeError, OSError):
                return str(ts) if ts else default
        
        # Helper function to calculate age with appropriate units
        def calculate_age(creation_timestamp, default="N/A"):
            if creation_timestamp is None or creation_timestamp == 0:
                return default
            try:
                if isinstance(creation_timestamp, str):
                    creation_timestamp = creation_timestamp.rstrip('.0')
                ts_val = float(creation_timestamp)
                if ts_val > 0:
                    import time
                    current_time = time.time()
                    age_seconds = current_time - ts_val
                    
                    if age_seconds < 0:
                        return default
                    
                    # Format based on duration
                    if age_seconds < 60:
                        return f"{int(age_seconds)} sec"
                    elif age_seconds < 3600:
                        mins = int(age_seconds / 60)
                        return f"{mins} min" if mins == 1 else f"{mins} mins"
                    elif age_seconds < 86400:
                        hours = age_seconds / 3600
                        if hours < 2:
                            return f"{hours:.1f} hour" if hours == 1.0 else f"{hours:.1f} hours"
                        return f"{int(hours)} hours"
                    else:
                        days = age_seconds / 86400
                        if days < 2:
                            return f"{days:.1f} day" if days == 1.0 else f"{days:.1f} days"
                        return f"{int(days)} days"
                return default
            except (ValueError, TypeError, OSError):
                return default
        
        lines = [
            f"🚀 Most profitable tokens in BSC chain in {period_display}:",
            ""
        ]
        
        # Format each token
        for i, token in enumerate(tokens, 1):
            lines.append(f"{i}. {self._format_profitable_token_item(token, format_money, format_timestamp, calculate_age)}")
            if i < len(tokens):
                lines.append("")  # Empty line between tokens
        
        return "\n".join(lines)
    
    def _format_profitable_token_item(self, token: Dict, format_money, format_timestamp, calculate_age) -> str:
        """Format individual profitable token item"""
        parts = []
        
        # 👨‍💻 Deployer Wallet
        creator = token.get('creator') or token.get('deployer') or "N/A"
        if creator and creator != "N/A":
            parts.append(f"👨‍💻 Deployer Wallet: <code>{creator}</code>")
        else:
            parts.append("👨‍💻 Deployer Wallet: N/A")
        
        # 💼 Token name
        token_name = token.get('name') or "N/A"
        parts.append(f"💼 Token name: {token_name}")
        
        # 📝 Contract
        contract_address = token.get('address') or "N/A"
        if contract_address != "N/A":
            parts.append(f"📝 Contract: <code>{contract_address}</code>")
        else:
            parts.append("📝 Contract: N/A")
        
        # 💰 Starting Market Cap (initial_liquidity or calculate from initial data)
        initial_liquidity = token.get('initial_liquidity') or 0
        starting_mcap = format_money(initial_liquidity, "$0.00")
        parts.append(f"💰 Starting Market Cap: {starting_mcap}")
        
        # 💵 Current Market Cap
        market_cap = token.get('market_cap') or 0
        current_mcap = format_money(market_cap, "$0.00")
        parts.append(f"💵 Current Market Cap: {current_mcap}")
        
        # 🚀 ATH Market Cap
        ath_mcap = token.get('history_highest_market_cap') or 0
        ath_mcap_str = format_money(ath_mcap, "$0.00")
        parts.append(f"🚀 ATH Market Cap: {ath_mcap_str}")
        
        # # 📅 ATH Date - check for ATH timestamp fields
        # ath_timestamp = (token.get('history_highest_market_cap_timestamp') or 
        #                 token.get('ath_timestamp') or 
        #                 token.get('highest_market_cap_timestamp') or 
        #                 token.get('ath_date') or 
        #                 token.get('history_highest_market_cap_time') or 0)
        
        # if ath_timestamp and ath_timestamp != 0:
        #     ath_date_str = format_timestamp(ath_timestamp, "N/A")
        #     parts.append(f"📅 ATH Date: {ath_date_str}")
        # else:
        #     # If current market cap equals ATH (within 1% tolerance), use current time as ATH date
        #     current_mcap_val = float(market_cap) if market_cap else 0
        #     ath_mcap_val = float(ath_mcap) if ath_mcap else 0
        #     if current_mcap_val > 0 and ath_mcap_val > 0:
        #         # Check if current is very close to ATH (within 1%)
        #         diff_percent = abs((current_mcap_val - ath_mcap_val) / ath_mcap_val) * 100
        #         if diff_percent < 1.0:
        #             # Current is at or very close to ATH, show current time
        #             import time
        #             ath_date_str = format_timestamp(time.time(), "N/A")
        #             parts.append(f"📅 ATH Date: {ath_date_str}")
        #         else:
        #             # ATH date not available in API response
        #             parts.append("📅 ATH Date: N/A")
        #     else:
        #         parts.append("📅 ATH Date: N/A")
        
        # 🕰 Deployment Date
        creation_timestamp = token.get('creation_timestamp') or token.get('open_timestamp') or 0
        deployment_date = format_timestamp(creation_timestamp, "N/A")
        parts.append(f"🕰 Deployment Date: {deployment_date}")
        
        # ⏲️ Age (in days)
        age = calculate_age(creation_timestamp, "N/A")
        parts.append(f"⏲️ Age: {age}")
        
        return "\n".join(parts)
    
    def _format_wallet_holdings_response(self, holdings: list, wallet_address: str) -> str:
        """Format wallet holdings response"""
        if not holdings or len(holdings) == 0:
            return f"📭 No token holdings found for wallet <code>{wallet_address}</code>"
        
        # Limit to top 10 holdings to avoid message length issues
        holdings = holdings[:10]
        
        # Helper functions
        def format_money(val, default="$0.00"):
            if val is None:
                return default
            try:
                v = float(val)
                abs_v = abs(v)
                if abs_v >= 1_000_000:
                    return f"${abs_v/1_000_000:.1f}M"
                elif abs_v >= 1_000:
                    return f"${abs_v/1_000:.1f}K"
                else:
                    return f"${v:,.2f}"
            except (ValueError, TypeError):
                return str(val) if val else default
        
        def format_amount(val, default="0"):
            if val is None:
                return default
            try:
                a = float(val)
                abs_a = abs(a)
                if abs_a >= 1_000_000_000:
                    return f"{abs_a/1_000_000_000:.2f}B"
                elif abs_a >= 1_000_000:
                    return f"{abs_a/1_000_000:.2f}M"
                elif abs_a >= 1_000:
                    return f"{abs_a/1_000:.2f}K"
                else:
                    return f"{a:,.2f}"
            except (ValueError, TypeError):
                return str(val) if val else default
        
        def format_timestamp(ts, default="N/A"):
            if ts is None or ts == 0:
                return default
            try:
                if isinstance(ts, str):
                    ts = ts.rstrip('.0')
                ts_val = float(ts)
                if ts_val > 0:
                    dt = datetime.fromtimestamp(ts_val, timezone.utc)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                return default
            except (ValueError, TypeError, OSError):
                return str(ts) if ts else default
        
        lines = [
            f"💼 Wallet Holdings",
            "",
            f"📝 Wallet: <code>{wallet_address}</code>",
            "",
        ]
        
        # Format each holding
        for i, holding in enumerate(holdings, 1):
            token_info = holding.get('token', {})
            token_symbol = token_info.get('symbol', 'N/A')
            token_name = token_info.get('name', 'N/A')
            token_address = token_info.get('token_address', 'N/A')
            
            # Balance and USD value
            balance = holding.get('balance', '0')
            usd_value = holding.get('usd_value', '0')
            
            # Profit information
            realized_profit = holding.get('realized_profit', '0')
            unrealized_profit = holding.get('unrealized_profit', '0')
            total_profit = holding.get('total_profit', '0')
            realized_profit_pnl = holding.get('realized_profit_pnl')
            total_profit_pnl = holding.get('total_profit_pnl')
            
            # Trading stats
            history_total_buys = holding.get('history_total_buys', 0)
            history_total_sells = holding.get('history_total_sells', 0)
            history_bought_amount = holding.get('history_bought_amount', '0')
            history_bought_cost = holding.get('history_bought_cost', '0')
            history_sold_amount = holding.get('history_sold_amount', '0')
            history_sold_income = holding.get('history_sold_income', '0')
            
            # Last active
            last_active = holding.get('last_active_timestamp', 0)
            
            # Wallet tags
            wallet_token_tags = holding.get('wallet_token_tags', [])
            
            # Compact format: Token name and symbol on one line
            lines.append(f"{i}. {token_name} ({token_symbol})")
            
            # Balance and profit on one line if possible
            balance_str = format_amount(balance) if float(balance or 0) > 0 else "0"
            usd_value_str = format_money(usd_value)
            
            if float(balance or 0) > 0:
                lines.append(f"   💰 {balance_str} | {usd_value_str}")
            else:
                lines.append(f"   💰 Sold out")
            
            # Profit (compact)
            if float(total_profit or 0) != 0:
                total_profit_str = format_money(total_profit)
                pnl_str = ""
                if total_profit_pnl is not None:
                    try:
                        pnl_val = float(total_profit_pnl) * 100
                        pnl_str = f" ({pnl_val:+.1f}%)"
                    except:
                        pass
                lines.append(f"   📈 {total_profit_str}{pnl_str}")
            
            # Trading activity (compact)
            if history_total_buys > 0 or history_total_sells > 0:
                total_trades = history_total_buys + history_total_sells
                lines.append(f"   🔄 {total_trades} trades (B:{history_total_buys}/S:{history_total_sells})")
            
            # Tags (compact)
            if wallet_token_tags:
                tags_str = ", ".join([str(tag) for tag in wallet_token_tags[:3]])  # Limit tags
                if len(wallet_token_tags) > 3:
                    tags_str += "..."
                lines.append(f"   🏷️ {tags_str}")
            
            if i < len(holdings):
                lines.append("")  # Empty line between holdings
        
        return "\n".join(lines)
    
    def _format_item(self, item: Dict, command: str) -> str:
        """Format individual item"""
        parts = []
        
        # Wallet address
        addr = item.get('address') or item.get('wallet_address') or item.get('wallet')
        if addr:
            parts.append(f"`{addr[:6]}...{addr[-4:]}`")
        
        # PNL (check multiple fields)
        pnl = item.get('pnl') or item.get('pnl_1d') or item.get('pnl_7d') or item.get('pnl_30d')
        if pnl is not None:
            if isinstance(pnl, (int, float)):
                pnl_pct = f"{pnl*100:.2f}%" if abs(pnl) < 1 else f"{pnl:.2f}"
                parts.append(f"PNL: {pnl_pct}")
            else:
                parts.append(f"PNL: {pnl}")
        
        # Realized profit
        profit = item.get('realized_profit') or item.get('realized_profit_1d') or item.get('realized_profit_7d') or item.get('realized_profit_30d')
        if profit:
            profit_str = f"${profit:,.2f}" if isinstance(profit, (int, float)) else str(profit)
            parts.append(f"Profit: {profit_str}")
        
        # Trades
        buy = item.get('buy') or item.get('buy_30d', 0)
        sell = item.get('sell') or item.get('sell_30d', 0)
        if buy or sell:
            parts.append(f"Buy: {buy} | Sell: {sell}")
        
        # Twitter/Name
        name = item.get('name') or item.get('twitter_name') or item.get('twitter_username')
        if name:
            parts.append(f"@{name}")
        
        # Win rate
        winrate = item.get('winrate_7d') or item.get('winrate')
        if winrate is not None:
            parts.append(f"Win: {winrate*100:.1f}%")
        
        return " | ".join(parts) if parts else str(item)
    
    # Command handlers
    
    async def handle_fbuy(self, address: str, period: str = "7d") -> str:
        """Handle /fbuy command"""
        addr = self.format_address(address)
        if not addr:
            return "❌ Invalid address format. Use BSC address (0x...)"
        
        period = self.parse_period(period)
        data = self.client.get_first_buy_wallets(addr, period)
        
        # For /fbuy, we need to enrich each wallet with holding stats
        if 'error' in data:
            return f"❌ Error: {data['error']}"
        
        if not data or 'data' not in data:
            return "⚠️ No data available"
        
        api_data = data.get('data', {})
        wallets = api_data.get('rank', [])
        
        if not wallets:
            return "📭 No first-buy wallets found"
        
        # Get token metadata
        token_name = api_data.get('token_name') or 'Unknown'
        token_symbol = api_data.get('token_symbol') or 'Unknown'
        token_address = api_data.get('token_address') or addr
        
        # Get deployer info from token info endpoint
        deployer_address = api_data.get('deployer_address')
        deploy_timestamp = api_data.get('deploy_timestamp')
        deploy_tx_hash = api_data.get('deploy_tx_hash')
        
        # Always try token info endpoint to get accurate deployer info
        token_info = self.client.get_token_info(token_address)
        if 'error' not in token_info and token_info.get('data') and isinstance(token_info['data'], list) and len(token_info['data']) > 0:
            token_data = token_info['data'][0]
            dev_info = token_data.get('dev', {})
            # Get deployer address from token info (most reliable source)
            if dev_info.get('creator_address'):
                deployer_address = dev_info.get('creator_address')
            # Get creation timestamp (this is the deploy time) - always prioritize this
            ts_candidate = token_data.get('creation_timestamp')
            if not ts_candidate or ts_candidate == 0:
                ts_candidate = token_data.get('pool', {}).get('creation_timestamp')
            if ts_candidate and ts_candidate != 0:
                deploy_timestamp = ts_candidate
            # Get deploy tx from first trade with creator tag (already in api_data if available)
            if not deploy_tx_hash:
                deploy_tx_hash = api_data.get('deploy_tx_hash')
            # Also update token name/symbol if we got better data
            if token_data.get('name'):
                token_name = token_data.get('name', token_name)
            if token_data.get('symbol'):
                token_symbol = token_data.get('symbol', token_symbol)
        
        # Get creation timestamp from first wallet's holding stats (which includes token metadata)
        # This is more reliable than the token_info endpoint which may return 400
        if wallets:
            first_wallet_addr = wallets[0].get('wallet') or wallets[0].get('address')
            if first_wallet_addr:
                holding_stats = self.client.get_wallet_holding_stats(first_wallet_addr, token_address)
                if 'error' not in holding_stats and holding_stats.get('data'):
                    stats_data = holding_stats['data']
                    token_info_from_holding = stats_data.get('token', {})
                    if token_info_from_holding:
                        # Get creation timestamp from holding stats token info (this is reliable!)
                        ts_from_holding = token_info_from_holding.get('creation_timestamp')
                        if ts_from_holding and ts_from_holding != 0:
                            deploy_timestamp = ts_from_holding
                        # Update token name/symbol if we got better data
                        if not token_name or token_name == 'Unknown':
                            token_name = token_info_from_holding.get('name', token_name)
                        if not token_symbol or token_symbol == 'Unknown':
                            token_symbol = token_info_from_holding.get('symbol', token_symbol)
        
        # Enrich each wallet with holding stats (limit to top 10 for performance)
        enriched_wallets = []
        for wallet in wallets[:10]:
            wallet_addr = wallet.get('wallet') or wallet.get('address')
            if not wallet_addr:
                continue
            
            # Fetch holding stats for this wallet
            holding_stats = self.client.get_wallet_holding_stats(wallet_addr, token_address)
            if 'error' not in holding_stats and holding_stats.get('data'):
                stats_data = holding_stats['data']
                # Merge holding stats into wallet dict
                wallet.update({
                    'history_total_buys': stats_data.get('history_total_buys', 0),
                    'history_total_sells': stats_data.get('history_total_sells', 0),
                    'realized_profit': stats_data.get('realized_profit', 0),
                    'unrealized_profit': stats_data.get('unrealized_profit', 0),
                    'total_profit': stats_data.get('total_profit', 0),
                    'last_active_timestamp': stats_data.get('last_active_timestamp', 0),
                    'history_bought_amount': stats_data.get('history_bought_amount', 0),
                    'history_bought_cost': stats_data.get('history_bought_cost', 0),
                })
                # Get token info from holding stats if available
                token_info = stats_data.get('token', {})
                if token_info:
                    # Update token name/symbol
                    if not token_name or token_name == 'Unknown':
                        token_name = token_info.get('name', token_name)
                    if not token_symbol or token_symbol == 'Unknown':
                        token_symbol = token_info.get('symbol', token_symbol)
                    # Get creation timestamp from holding stats (this is reliable!)
                    if not deploy_timestamp or deploy_timestamp == 0:
                        ts_from_token = token_info.get('creation_timestamp')
                        if ts_from_token and ts_from_token != 0:
                            deploy_timestamp = ts_from_token
            
            enriched_wallets.append(wallet)
        
        # Format with enriched data
        return self._format_fbuy_response(enriched_wallets, token_address, token_name, token_symbol,
                                          deployer_address, deploy_timestamp, deploy_tx_hash)
    
    async def handle_pro(self, address: str, period: str = "7d") -> str:
        """Handle /pro command - Profitable wallets for a specific token"""
        token_address = self.format_address(address)
        if not token_address:
            return "❌ Invalid address format. Use BSC address (0x...)"
        
        # Get profitable wallets
        data = self.client.get_profitable_wallets(token_address, period)
        if 'error' in data:
            return f"❌ Error: {data['error']}"
        
        # Extract wallets list from response
        if not data or 'data' not in data:
            return "⚠️ No data available"
        
        api_data = data.get('data', {})
        wallets = api_data.get('list', [])
        
        if not wallets or len(wallets) == 0:
            return "📭 No profitable wallets found"
        
        # Filter out contract addresses and wallets with no trading activity
        filtered_wallets = []
        for wallet in wallets:
            wallet_addr = wallet.get('address') or wallet.get('wallet_address') or wallet.get('wallet')
            if not wallet_addr:
                continue
            
            # Skip wallets with no trades (likely contracts or transfer-only addresses)
            buy_count = wallet.get('buy_tx_count_cur', 0)
            sell_count = wallet.get('sell_tx_count_cur', 0)
            total_trades = buy_count + sell_count
            
            # Filter out wallets with 0 trades
            if total_trades == 0:
                continue
            
            # Filter out wallets that only received tokens via transfer (no actual trading)
            transfer_in = wallet.get('transfer_in', False)
            if transfer_in and total_trades == 0:
                continue
            
            # Additional check: if buy_volume_cur and sell_volume_cur are both 0, skip
            buy_volume = wallet.get('buy_volume_cur', 0)
            sell_volume = wallet.get('sell_volume_cur', 0)
            if buy_volume == 0 and sell_volume == 0:
                continue
            
            filtered_wallets.append(wallet)
        
        if not filtered_wallets or len(filtered_wallets) == 0:
            return "📭 No profitable wallets found (after filtering contract addresses)"
        
        # Get token info (name, symbol) from first wallet's holding stats or token info
        token_name = "Unknown Token"
        token_symbol = "UNKNOWN"
        
        # Try to get token info from first wallet's holding stats
        if filtered_wallets:
            first_wallet_addr = filtered_wallets[0].get('address')
            if first_wallet_addr:
                holding_stats = self.client.get_wallet_holding_stats(first_wallet_addr, token_address)
                if 'error' not in holding_stats and holding_stats.get('data'):
                    token_info = holding_stats['data'].get('token', {})
                    if token_info:
                        token_name = token_info.get('name', token_name)
                        token_symbol = token_info.get('symbol', token_symbol)
        
        # Format response
        return self._format_profitable_wallets_response(filtered_wallets, token_address, token_name, token_symbol)
    
    async def handle_ht(self, address: str, period: str = "all") -> str:
        """Handle /ht command - How long wallet holds tokens (profit statistics)"""
        wallet_address = self.format_address(address)
        if not wallet_address:
            return "❌ Invalid address format. Use BSC address (0x...)"
        
        # Try "all" period first, fallback to "30d" if "all" doesn't work
        period = "all"
        
        # Get wallet profit statistics
        data = self.client.get_wallet_profit_stat(wallet_address, period)
        
        # If "all" period fails, try "30d" as fallback for all-time data
        if 'error' in data or (data and 'data' not in data):
            period = "30d"
            data = self.client.get_wallet_profit_stat(wallet_address, period)
        
        if 'error' in data:
            return f"❌ Error: {data['error']}"
        
        # Extract data from response
        if not data or 'data' not in data:
            return "⚠️ No data available"
        
        api_data = data.get('data', {})
        
        # Format profit statistics response with avg cost/sold and realized profits
        return self._format_wallet_profit_stat_response(api_data, wallet_address, period)
    
    async def handle_mpro(self, period: str = "7d") -> str:
        """Handle /mpro command"""
        period = self.parse_period(period)
        data = self.client.get_most_profitable_wallets(period)
        return self.format_response(data, 'mpro', period)
    
    async def handle_pd(self, period: str = "24h") -> str:
        """Handle /pd command - Most profitable tokens"""
        # Map period to API format (1h, 6h, 24h)
        period_map = {
            '1h': '1h',
            '6h': '6h',
            '24h': '24h',
            '1d': '24h',
        }
        api_period = period_map.get(period.lower(), '24h')
        
        data = self.client.get_profitable_deployers(api_period)
        if 'error' in data:
            return f"❌ Error: {data['error']}"
        
        # Extract data from response
        if not data or 'data' not in data:
            return "⚠️ No data available"
        
        rank_data = data.get('data', {}).get('rank', [])
        if not rank_data:
            return "⚠️ No tokens found"
        
        # Limit to top 10 for performance
        rank_data = rank_data[:10]
        
        # Fetch deployer addresses and ATH timestamps from token info endpoint
        import time
        for i, token in enumerate(rank_data):
            token_address = token.get('address')
            if not token_address:
                print(f"DEBUG: Token {i+1} - No address found")
                continue
                
            # print(f"DEBUG: Token {i+1} - Fetching info for {token_address}")
            # Always try to get deployer address from token_info_brief
            token_info = self.client.get_token_info(token_address)
            
            # Check for errors
            if 'error' in token_info:
                print(f"DEBUG: Token {i+1} - API error: {token_info.get('error')}")
                # API call failed, continue to next token
                if i < len(rank_data) - 1:
                    time.sleep(0.5)  # Small delay to avoid rate limiting
                continue
            
            # Check if we have data
            if not token_info.get('data'):
                print(f"DEBUG: Token {i+1} - No data in response")
                if i < len(rank_data) - 1:
                    time.sleep(0.5)
                continue
            
            # mutil_window_token_info returns data as a list
            # The response structure: data[0].dev.creator_address contains the deployer address
            data = token_info.get('data', [])
            # print(f"DEBUG: Token {i+1} - data: {data}")
            
            if not isinstance(data, list) or len(data) == 0:
                print(f"DEBUG: Token {i+1} - No tokens in response (data is not a list or is empty)")
                if i < len(rank_data) - 1:
                    time.sleep(0.5)
                continue
            
            # The first token in the response contains the creator's wallet address
            token_obj = data[0]
            if isinstance(token_obj, dict):
                dev_info = token_obj.get('dev', {})
                creator_address = dev_info.get('creator_address')
                # print(f"DEBUG: Token {i+1} - creator_address from mutil_window_token_info: {creator_address}")
                if creator_address and str(creator_address).strip() and str(creator_address).strip() != '':
                    token['creator'] = str(creator_address).strip()
                    token['deployer'] = str(creator_address).strip()
                    # print(f"DEBUG: Token {i+1} - SUCCESS! Set creator to: {creator_address}")
                else:
                    # print(f"DEBUG: Token {i+1} - creator_address is empty")
                    pass
            else:
                # print(f"DEBUG: Token {i+1} - token_obj is not a dict")
                pass
            
            # Small delay between API calls to avoid rate limiting
            if i < len(rank_data) - 1:
                time.sleep(0.5)
        
        # Format period display
        period_display = {
            '1h': '1 hour',
            '6h': '6 hours',
            '24h': '24 hours'
        }.get(api_period, api_period)
        
        return self._format_profitable_tokens_response(rank_data, api_period, period_display)
    
    async def handle_lowtxp(self, period: str = "7d", tx_min: int = 1, tx_max: int = 10) -> str:
        """
        Handle /lowtxp command - Profitable wallets with low number of transactions.

        Format:
        Profitable wallets with low number of transactions (1-100 total txns) in 7 days:

        1. 0x...
           🔄 Total Transactions:
           🟢 Buy Transactions:
           🔴 Sell Transactions:
           💰 Total Profit: $... (Realized: ... Unrealized: ...)
           📊 Win Rate: ...% (xW/yL)
           ⏱️ Avg Hold Time: ... days
        """
        # Normalize period
        period = self.parse_period(period)

        raw = self.client.get_low_tx_profitable_wallets(period, tx_min, tx_max)
        if "error" in raw:
            return f"❌ Error: {raw['error']}"

        data = raw.get("data") or {}
        wallets = data.get("rank") or []
        if not wallets:
            return "📭 No wallets found for the given transaction range."

        # Limit to top 10 for readability
        wallets = wallets[:10]

        # Helper: period display
        period_names = {"1d": "1 day", "7d": "7 days", "30d": "30 days"}
        period_display = period_names.get(period, period)

        header = f"Profitable wallets with low number of transactions ({tx_min}-{tx_max} total txns) in {period_display}:"

        lines = [header, ""]

        # Helper functions
        def fmt_money(val, default="$0.00"):
            if val is None:
                return default
            try:
                v = float(val)
                return f"${v:,.2f}"
            except (ValueError, TypeError):
                return str(val) if val else default

        def fmt_duration_days(seconds, default="0.0 days"):
            if seconds is None:
                return default
            try:
                secs = float(seconds)
                if secs <= 0:
                    return default
                days = secs / 86400
                return f"{days:.1f} days"
            except (ValueError, TypeError):
                return default

        def period_suffix(p: str) -> str:
            return {
                "1d": "1d",
                "7d": "7d",
                "30d": "30d",
            }.get(p, "7d")

        p_suf = period_suffix(period)

        for idx, w in enumerate(wallets, 1):
            addr = w.get("address") or w.get("wallet_address") or "N/A"

            # Transactions for period
            total_txs = w.get(f"txs_{p_suf}") or w.get("txs") or 0
            buy_txs = w.get(f"buy_{p_suf}") or w.get("buy") or 0
            sell_txs = w.get(f"sell_{p_suf}") or w.get("sell") or 0

            # Profit
            realized = w.get(f"realized_profit_{p_suf}") or w.get("realized_profit") or 0
            unrealized = w.get("unrealized_profit") or 0
            try:
                total_profit = float(realized or 0) + float(unrealized or 0)
            except (ValueError, TypeError):
                total_profit = realized

            # Win rate and W/L
            winrate = w.get(f"winrate_{p_suf}") or w.get("winrate") or 0
            try:
                wr_val = float(winrate)
                if wr_val <= 1.0:
                    wr_pct = wr_val * 100
                    wr_decimal = wr_val
                else:
                    wr_pct = wr_val
                    wr_decimal = wr_val / 100.0
            except (ValueError, TypeError):
                wr_pct = 0.0
                wr_decimal = 0.0

            try:
                total_for_wl = int(total_txs or 0)
                wins = int(total_for_wl * wr_decimal)
                losses = total_for_wl - wins
            except Exception:
                wins = 0
                losses = 0

            # Avg hold time
            avg_hold = (
                w.get(f"avg_holding_period_{p_suf}")
                or w.get(f"avg_hold_time_{p_suf}")
                or w.get("avg_hold_time")
                or 0
            )

            lines.append(f"{idx}. {addr}")
            lines.append(f"   🔄 Total Transactions: {total_txs}")
            lines.append(f"   🟢 Buy Transactions: {buy_txs}")
            lines.append(f"   🔴 Sell Transactions: {sell_txs}")
            lines.append(
                f"   💰 Total Profit: {fmt_money(total_profit)} "
                f"(Realized: {fmt_money(realized)} Unrealized: {fmt_money(unrealized)})"
            )
            lines.append(f"   📊 Win Rate: {wr_pct:.1f}% ({wins}W/{losses}L)")
            lines.append(f"   ⏱️ Avg Hold Time: {fmt_duration_days(avg_hold)}")

            if idx < len(wallets):
                lines.append("")

        return "\n".join(lines)
    
    async def handle_kol(self, kol_name: str, period: str = "7d") -> str:
        """
        Handle /kol command.

        Flow:
        1) Search KOL by name to find the wallet address (bsc chain)
        2) Fetch wallet profit statistics for that address and period
        3) Format similar to /ht, with extra KOL header
        """
        period = self.parse_period(period)  # normalize to 1d/7d/30d

        # Step 1: search for KOL wallet
        search = self.client.search_wallet_by_kol_name(kol_name)
        if "error" in search:
            return f"❌ Error searching KOL '{kol_name}': {search['error']}"

        data = search.get("data") or {}
        wallets = data.get("wallets") or []
        if not wallets:
            return f"📭 No wallet found for KOL '{kol_name}'"

        # Prefer first BSC wallet
        wallet = None
        for w in wallets:
            if isinstance(w, dict) and w.get("chain") == "bsc":
                wallet = w
                break
        if wallet is None and isinstance(wallets[0], dict):
            wallet = wallets[0]

        if not wallet:
            return f"📭 No valid wallet record for KOL '{kol_name}'"

        wallet_address = wallet.get("address")
        if not wallet_address:
            return f"📭 No wallet address found for KOL '{kol_name}'"

        twitter_name = wallet.get("twitter_name") or kol_name
        twitter_username = wallet.get("twitter_username")
        fans = wallet.get("twitter_fans_num")

        # Step 2: fetch wallet profit statistics (same endpoint as /ht)
        stats = self.client.get_wallet_profit_stat(wallet_address, period)
        if "error" in stats:
            return f"❌ Error fetching profitability for {twitter_name}: {stats['error']}"

        stats_data = stats.get("data")
        if not stats_data:
            return f"⚠️ No profitability data available for {twitter_name}"

        # Step 3: format using existing wallet profit formatter
        core_text = self._format_wallet_profit_stat_response(stats_data, wallet_address, period)

        header_lines = [
            f"🌟 KOL Profitability",
            "",
            f"👤 Name: {twitter_name}",
        ]
        if twitter_username:
            header_lines.append(f"X : @{twitter_username}")
        if fans:
            try:
                fans_int = int(fans)
                header_lines.append(f"👥 Followers: {fans_int:,}")
            except (ValueError, TypeError):
                pass
        # header_lines.append(f"⏱️ Period: {period}")
        # header_lines.append("")

        return "\n".join(header_lines + core_text.splitlines())
    
    async def handle_hvol(self, period: str = "7d") -> str:
        """
        Handle /hvol command - High Volume Wallets
        
        Calculates volume as: avg_cost_{period} * txs_{period}
        Then orders by this calculated volume.
        """
        period = self.parse_period(period)
        data = self.client.get_high_volume_wallets(period)
        
        if 'error' in data:
            return f"❌ Error: {data['error']}"
        
        if not data or 'data' not in data:
            return "⚠️ No data available"
        
        api_data = data.get('data', {})
        wallets = api_data.get('rank', [])
        
        if not wallets:
            return "📭 No wallets found"
        
        # Calculate volume for each wallet: avg_cost_{period} * txs_{period}
        period_suffix = {
            "1d": "1d",
            "7d": "7d",
            "30d": "30d",
        }.get(period, "7d")
        
        wallets_with_volume = []
        for wallet in wallets:
            avg_cost = wallet.get(f"avg_cost_{period_suffix}") or wallet.get("avg_cost") or 0
            txs = wallet.get(f"txs_{period_suffix}") or wallet.get("txs") or 0
            
            try:
                avg_cost_val = float(avg_cost) if avg_cost else 0.0
                txs_val = int(txs) if txs else 0
                calculated_volume = avg_cost_val * txs_val
            except (ValueError, TypeError):
                calculated_volume = 0.0
            
            # Store calculated volume in wallet dict for sorting
            wallet_copy = wallet.copy()
            wallet_copy['_calculated_volume'] = calculated_volume
            wallets_with_volume.append(wallet_copy)
        
        # Sort by calculated volume (descending)
        wallets_with_volume.sort(key=lambda w: w.get('_calculated_volume', 0), reverse=True)
        
        # Limit to top 10
        top_wallets = wallets_with_volume[:10]
        
        # Format response
        return self._format_high_volume_wallets_response(top_wallets, period)
    
    async def handle_hact(self, period: str = "7d") -> str:
        """Handle /hact command"""
        period = self.parse_period(period)
        data = self.client.get_high_activity_wallets(period)
        return self.format_response(data, 'hact', period)


# Discord bot implementation
try:
    import discord
    from discord.ext import commands
    
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='/', intents=intents)
    gmgn_bot = GMGNBot()
    
    @bot.event
    async def on_ready():
        print(f'✅ {bot.user} has connected to Discord!')
    
    @bot.command(name='fbuy')
    async def fbuy_command(ctx, address: str, period: str = "7d"):
        """First buy wallets of any token"""
        async with ctx.typing():
            response = await gmgn_bot.handle_fbuy(address, period)
            await ctx.send(response)
    
    @bot.command(name='pro')
    async def pro_command(ctx, address: str, period: str = "7d"):
        """Profitable wallets in any specific token"""
        async with ctx.typing():
            response = await gmgn_bot.handle_pro(address, period)
            await ctx.send(response)
    
    @bot.command(name='ht')
    async def ht_command(ctx, address: str, period: str = "7d"):
        """How long wallet holds tokens (profit statistics)"""
        async with ctx.typing():
            response = await gmgn_bot.handle_ht(address, period)
            await ctx.send(response)
    
    @bot.command(name='mpro')
    async def mpro_command(ctx, period: str = "7d"):
        """Most profitable wallets on BSC"""
        async with ctx.typing():
            response = await gmgn_bot.handle_mpro(period)
            await ctx.send(response)
    
    @bot.command(name='pd')
    async def pd_command(ctx, period: str = "7d"):
        """Most profitable token deployers in BSC chain"""
        async with ctx.typing():
            response = await gmgn_bot.handle_pd(period)
            await ctx.send(response)
    
    @bot.command(name='lowtxp')
    async def lowtxp_command(ctx, period: str = "7d", tx_min: int = 1, tx_max: int = 10):
        """Profitable wallets with low number of transactions"""
        async with ctx.typing():
            response = await gmgn_bot.handle_lowtxp(period, tx_min, tx_max)
            await ctx.send(response)
    
    @bot.command(name='kol')
    async def kol_command(ctx, kol_name: str, period: str = "7d"):
        """KOL wallet profitability"""
        async with ctx.typing():
            response = await gmgn_bot.handle_kol(kol_name, period)
            await ctx.send(response)
    
    @bot.command(name='hvol')
    async def hvol_command(ctx, period: str = "7d"):
        """High-volume wallets in BSC chain"""
        async with ctx.typing():
            response = await gmgn_bot.handle_hvol(period)
            await ctx.send(response)
    
    @bot.command(name='hact')
    async def hact_command(ctx, period: str = "7d"):
        """High-activity wallets in BSC chain"""
        async with ctx.typing():
            response = await gmgn_bot.handle_hact(period)
            await ctx.send(response)
    
    @bot.command(name='help_gmgn')
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

    def run_discord_bot(token: str):
        """Run Discord bot"""
        bot.run(token)

except ImportError:
    print("Discord.py not installed. Install with: pip install discord.py")
    bot = None


# Telegram bot implementation
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes, Defaults
    from telegram.constants import ParseMode
    
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('GMGN Scraping Bot is ready! Use /help_gmgn for commands.')
    
    async def help_gmgn(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    def setup_telegram_handlers(application: Application, gmgn_bot_instance: GMGNBot):
        """Setup Telegram command handlers"""
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help_gmgn", help_gmgn))
        
        async def fbuy(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if len(context.args) < 1:
                await update.message.reply_text("Usage: /fbuy [address] [period]")
                return
            address = context.args[0]
            period = context.args[1] if len(context.args) > 1 else "7d"
            response = await gmgn_bot_instance.handle_fbuy(address, period)
            await update.message.reply_text(response)
        
        async def pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if len(context.args) < 1:
                await update.message.reply_text("Usage: /pro [address] [period]")
                return
            address = context.args[0]
            period = context.args[1] if len(context.args) > 1 else "7d"
            response = await gmgn_bot_instance.handle_pro(address, period)
            await update.message.reply_text(response)
        
        async def ht(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if len(context.args) < 1:
                await update.message.reply_text("Usage: /ht [address] [period]")
                return
            address = context.args[0]
            period = context.args[1] if len(context.args) > 1 else "7d"
            response = await gmgn_bot_instance.handle_ht(address, period)
            await update.message.reply_text(response)
        
        async def mpro(update: Update, context: ContextTypes.DEFAULT_TYPE):
            period = context.args[0] if len(context.args) > 0 else "7d"
            response = await gmgn_bot_instance.handle_mpro(period)
            await update.message.reply_text(response)
        
        async def pd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            period = context.args[0] if len(context.args) > 0 else "7d"
            response = await gmgn_bot_instance.handle_pd(period)
            await update.message.reply_text(response)
        
        async def lowtxp(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if len(context.args) < 3:
                await update.message.reply_text("Usage: /lowtxp [period] [tx_min] [tx_max]")
                return
            period = context.args[0]
            tx_min = int(context.args[1])
            tx_max = int(context.args[2])
            response = await gmgn_bot_instance.handle_lowtxp(period, tx_min, tx_max)
            await update.message.reply_text(response)
        
        async def kol(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if len(context.args) < 1:
                await update.message.reply_text("Usage: /kol [kol_name] [period]")
                return
            kol_name = context.args[0]
            period = context.args[1] if len(context.args) > 1 else "7d"
            response = await gmgn_bot_instance.handle_kol(kol_name, period)
            await update.message.reply_text(response)
        
        async def hvol(update: Update, context: ContextTypes.DEFAULT_TYPE):
            period = context.args[0] if len(context.args) > 0 else "7d"
            response = await gmgn_bot_instance.handle_hvol(period)
            await update.message.reply_text(response)
        
        async def hact(update: Update, context: ContextTypes.DEFAULT_TYPE):
            period = context.args[0] if len(context.args) > 0 else "7d"
            response = await gmgn_bot_instance.handle_hact(period)
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
    
    def run_telegram_bot(token: str, gmgn_bot_instance: GMGNBot):
        """Run Telegram bot"""
        # Use HTML parse mode so we can wrap addresses in <code>...</code> cleanly
        defaults = Defaults(parse_mode=ParseMode.HTML)
        application = Application.builder().token(token).defaults(defaults).build()
        setup_telegram_handlers(application, gmgn_bot_instance)
        application.run_polling()

except ImportError:
    print("python-telegram-bot not installed. Install with: pip install python-telegram-bot")
    run_telegram_bot = None


if __name__ == "__main__":
    import sys
    import os
    
    # Check for config
    if os.path.exists("config.py"):
        from config import DISCORD_TOKEN, TELEGRAM_TOKEN, BOT_TYPE
    else:
        print("⚠️  config.py not found. Please create it with your bot tokens.")
        sys.exit(1)
    
    gmgn_bot = GMGNBot()
    
    # Prefer the new split modules if available
    try:
        from discord_bot import run_discord_bot as _run_discord  # type: ignore[import]
    except ImportError:
        _run_discord = None  # type: ignore[assignment]

    try:
        from telegram_bot import run_telegram_bot as _run_telegram  # type: ignore[import]
    except ImportError:
        _run_telegram = None  # type: ignore[assignment]

    if BOT_TYPE == "discord" and _run_discord:
        print("🚀 Starting Discord bot (modular)...")
        _run_discord(DISCORD_TOKEN, gmgn_bot)
    elif BOT_TYPE == "telegram" and _run_telegram:
        print("🚀 Starting Telegram bot (modular)...")
        _run_telegram(TELEGRAM_TOKEN, gmgn_bot)
    else:
        print("❌ Invalid BOT_TYPE or required library not installed")
        sys.exit(1)