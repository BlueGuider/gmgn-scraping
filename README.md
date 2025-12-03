# GMGN Scraping Bot

A Discord/Telegram bot for scraping wallet and token data from GMGN.ai without requiring an API key.

## Features

The bot provides the following commands:

1. **`/fbuy [address] [period]`** - First buy wallets of any token on BSC + buy/sell volume, trades, and PNL in 1/7/30 days
2. **`/pro [address] [period]`** - Profitable wallets in any specific token on BSC
3. **`/ht [address] [period]`** - How long wallet holds tokens (profit statistics)
4. **`/mpro [period]`** - Most profitable wallets on BSC in 1/7/30 days
5. **`/pd [period]`** - Most profitable token deployers in BSC chain
6. **`/lowtxp [period] [tx_min] [tx_max]`** - Profitable wallets with low number of transactions
7. **`/kol [kol_name] [period]`** - KOL wallet profitability in 1/7/30 days
8. **`/hvol [period]`** - High-volume wallets in BSC chain in 1/7/30 days
9. **`/hact [period]`** - High-activity wallets in BSC chain in 1/7/30 days

**Periods:** `1d`, `7d`, `30d` (default: `7d`)

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration:**
   ```bash
   cp config.py.example config.py
   ```
   Then edit `config.py` and add your bot tokens:
   - For Discord: Get token from [Discord Developer Portal](https://discord.com/developers/applications)
   - For Telegram: Get token from [@BotFather](https://t.me/BotFather) on Telegram

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## Setup Instructions

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to "Bot" section and click "Add Bot"
4. Copy the bot token
5. Under "Privileged Gateway Intents", enable "Message Content Intent"
6. Go to "OAuth2" > "URL Generator"
7. Select "bot" scope and necessary permissions
8. Invite the bot to your server using the generated URL
9. Add the token to `config.py`

### Telegram Bot Setup

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided
5. Add the token to `config.py`

## How It Works

The bot scrapes data from GMGN.ai by:
- Mimicking browser requests with proper headers
- Using device IDs and fingerprinting to appear as a legitimate browser
- Making requests to GMGN's internal API endpoints
- Parsing and formatting the responses for easy reading

## API Endpoints

The bot uses GMGN's internal API endpoints:
- `/defi/quotation/v1/rank/bsc/wallets/{period}` - Wallet rankings
- `/defi/quotation/v1/token/{address}/...` - Token-specific data
- And more...

## Cookie Management

### How Often to Refresh

- **Cookies**: Every **2-4 hours** (especially `cf_clearance` and `__cf_bm`)
- **Device IDs**: **Never** - they can be reused indefinitely

### Quick Refresh

1. Run `python refresh_cookies.py`
2. Follow the prompts to paste new cookies
3. Or manually update `cookies.txt` or `config.py`

### Check Cookie Validity

```bash
python check_cookies.py
```

This will test if your cookies are still valid.

### When Cookies Expire

You'll get **403 Forbidden** errors. When this happens:
1. Open GMGN.ai in browser
2. Get fresh cookies (F12 > Network > Cookie header)
3. Update `cookies.txt` or `config.py`
4. Restart bot if needed

See `COOKIE_REFRESH_GUIDE.md` for detailed information.

## Troubleshooting

### 302 Redirect Errors

If you encounter 302 redirects (like in Postman), it's because:
- Missing required headers (User-Agent, Referer, etc.)
- Missing cookies (session, CSRF tokens)
- Missing device identifiers

The bot handles all of this automatically by:
- Setting proper browser headers
- Generating device IDs and fingerprints
- Using a persistent session

**If you still get 302 errors**, you may need to add cookies from your browser:

1. Open GMGN.ai in your browser
2. Press F12 > Network tab
3. Make a request on the site
4. Copy the `Cookie` header from any request
5. Use `cookie_helper.py` to parse cookies:
   ```python
   from cookie_helper import parse_cookie_string
   from gmgn_client import GMGNClient
   
   cookie_string = "your_cookie_string_here"
   cookies = parse_cookie_string(cookie_string)
   client = GMGNClient(cookies=cookies)
   ```

### Testing Endpoints

Use `test_gmgn.py` to test API endpoints:
```bash
python test_gmgn.py
```

This will help you discover which endpoints work and which need adjustment.

### Rate Limiting

GMGN may rate limit requests. If you see errors:
- Reduce request frequency
- Add delays between requests
- Use the bot responsibly

## Notes

- This bot is for educational purposes
- Respect GMGN.ai's terms of service
- Don't abuse the API with excessive requests
- Some endpoints may require additional parameters that need to be discovered

## License

This project is provided as-is for educational purposes.

