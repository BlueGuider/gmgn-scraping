"""
Debug script: test gmgn_client.get_first_buy_wallets and inspect raw token_trades response.
Run with:
    python debug_first_buys.py
"""
import sys
import io
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from gmgn_client import GMGNClient
from cookie_helper import parse_cookie_string


def main() -> None:
    print("Debugging get_first_buy_wallets() ...")
    print("=" * 60)

    # Try to load cookies & device IDs from config.py
    cookies = None
    device_id = None
    fp_did = None
    try:
        from config import COOKIES, DEVICE_ID, FP_DID

        cookies = COOKIES
        device_id = DEVICE_ID
        fp_did = FP_DID
        print("[OK] Loaded cookies and device IDs from config.py")
    except Exception as e:
        print("[WARN] Could not load COOKIES/DEVICE_ID/FP_DID from config.py:", e)

    client = GMGNClient(cookies=cookies, device_id=device_id, fp_did=fp_did)

    # Token from your example
    token = "0x6a458b2028cdf296237de4556d78bb18cf804444"

    print(f"\nCalling get_first_buy_wallets({token}, '7d') ...")
    res = client.get_first_buy_wallets(token, "7d")

    print("\nTop-level keys:", list(res.keys()))
    print("msg:", res.get("msg"))
    print("error:", res.get("error"))

    data = res.get("data", {})
    rank = data.get("rank") or data.get("list") or []
    print("rank type:", type(rank), "len:", len(rank) if isinstance(rank, list) else "N/A")

    if isinstance(rank, list) and rank:
        print("\nFirst item keys:", list(rank[0].keys()))
        print("\nFirst item sample:")
        print(json.dumps(rank[0], indent=2)[:800])
    else:
        print("\nNo rank items. Full response (truncated):")
        print(json.dumps(res, indent=2)[:1200])


if __name__ == "__main__":
    main()









