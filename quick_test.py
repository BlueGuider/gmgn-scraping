"""Quick test of GMGN client"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from gmgn_client import GMGNClient
from cookie_helper import parse_cookie_string

# Load cookies
with open('cookies.txt', 'r') as f:
    cookies = parse_cookie_string(f.read().strip())

# Create client with exact device IDs
client = GMGNClient(
    cookies=cookies,
    device_id='f9166d17-1e90-4995-99b4-ee028bbd5675',
    fp_did='fa361a492c820f5a56b636b00743ed54'
)

# Test endpoint
print("Testing get_most_profitable_wallets('7d')...")
result = client.get_most_profitable_wallets('7d')

if 'data' in result and 'rank' in result.get('data', {}):
    rank = result['data']['rank']
    print(f"[SUCCESS] Got {len(rank)} wallets")
    if len(rank) > 0:
        print(f"First wallet: {rank[0].get('address', 'N/A')[:10]}...")
        print(f"PNL 1d: {rank[0].get('pnl_1d', 'N/A')}")
else:
    print(f"[ERROR] {result.get('error', 'Unknown error')}")

