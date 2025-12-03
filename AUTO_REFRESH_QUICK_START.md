# Quick Start: Automated Cookie Refresh

## ✅ Dependencies Installed!

All required packages are installed. You're ready to go!

## 🚀 Quick Test

Test the automated refresh (visible browser to see it work):

```bash
python test_auto_refresh.py
```

This will:
- Open Chrome browser
- Visit GMGN.ai
- Wait for Cloudflare challenge
- Extract cookies
- Save them automatically

## 🔄 Run Automatic Refresh Service

Run this to automatically refresh cookies every 2 hours:

```bash
python cookie_refresh_service.py
```

This runs continuously in the background and:
- Refreshes cookies every 2 hours
- Saves to `cookies.txt` and `config.py`
- Verifies cookies work after refresh

**Press Ctrl+C to stop**

## 📋 Three Ways to Use

### 1. One-Time Refresh
```bash
python auto_refresh_cookies.py
```
Refreshes cookies once and saves them.

### 2. Background Service (Recommended)
```bash
python cookie_refresh_service.py
```
Runs continuously, refreshes every 2 hours.

### 3. Windows Task Scheduler
1. Create `refresh_cookies.bat`:
   ```batch
   @echo off
   cd /d "E:\Projects\gmgn scraping"
   python auto_refresh_cookies.py
   ```
2. Schedule it to run every 2 hours in Task Scheduler

## ⚙️ Configuration

### Adjust Wait Time

If Cloudflare challenge doesn't pass, increase wait time:

```python
refresher = AutoCookieRefresher(headless=True, wait_time=30)  # 30 seconds
```

### Run Visible Browser (for debugging)

```python
refresher = AutoCookieRefresher(headless=False, wait_time=20)
```

## 🎯 Integration with Bot

The bot will automatically use refreshed cookies from `cookies.txt` or `config.py`. No need to restart the bot - just refresh cookies and the bot will use them on the next request.

## ✅ That's It!

You now have fully automated cookie refresh! No more manual copying cookies every 2-4 hours.

## 📝 Notes

- **First run**: May take longer (ChromeDriver download if using webdriver-manager)
- **Headless mode**: Runs in background (no browser window)
- **Wait time**: 20 seconds default (increase if Cloudflare challenge takes longer)
- **Frequency**: Every 2 hours recommended (before 4-hour cookie expiry)

## 🐛 Troubleshooting

**ChromeDriver issues?**
- Already handled by `webdriver-manager` - it auto-downloads!

**Cloudflare not passing?**
- Increase `wait_time` to 30-60 seconds
- Run with `headless=False` to see what's happening

**Cookies missing `cf_clearance`?**
- Cloudflare challenge didn't pass
- Increase wait time or check if GMGN.ai is accessible

See `setup_auto_refresh.md` for detailed troubleshooting.








