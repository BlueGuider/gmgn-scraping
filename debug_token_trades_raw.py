"""
Debug script: call the raw token_trades endpoint for a token and inspect the JSON.
Run:
    python debug_token_trades_raw.py
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


def main() -> None:
    print("Debugging raw token_trades response ...")
    print("=" * 60)

    # Load cookies & device IDs from config.py if available
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

    chain = "bsc"
    token = "0x6a458b2028cdf296237de4556d78bb18cf804444"
    url = f"https://gmgn.ai/vas/api/v1/token_trades/{chain}/{token}"

    params = client._get_base_params()
    params.update(
        {
            "limit": 50,
            "maker": "",
            "revert": "true",
        }
    )

    print("\nRequest URL:", url)
    print("Params:", params)

    resp = client.session.get(url, params=params, timeout=30)
    print("\nStatus:", resp.status_code)
    print("Content-Type:", resp.headers.get("Content-Type"))

    try:
        raw = resp.json()
    except Exception as e:
        print("JSON parse error:", e)
        print("Text preview:", resp.text[:500])
        return

    print("\nTop-level type:", type(raw))
    if isinstance(raw, dict):
        print("Top-level keys:", list(raw.keys()))
        data = raw.get("data")
        print("data type:", type(data))
        if isinstance(data, dict):
            print("data keys:", list(data.keys()))
            for k, v in data.items():
                if isinstance(v, list):
                    print(f"Found list under data['{k}'] with length {len(v)}")
                    if v:
                        print("First item keys:", list(v[0].keys()))
                    break
        elif isinstance(data, list):
            print("data is list, length:", len(data))
            if data:
                print("First item keys:", list(data[0].keys()))
    elif isinstance(raw, list):
        print("Raw is list, length:", len(raw))
        if raw:
            print("First item keys:", list(raw[0].keys()))

    print("\nRaw JSON preview:")
    print(json.dumps(raw, indent=2)[:1200])


if __name__ == "__main__":
    main()









