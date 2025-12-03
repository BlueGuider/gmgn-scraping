"""
GMGN API Client for scraping wallet and token data
"""
import requests
import uuid
import time
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

# Try to use cloudscraper for Cloudflare bypass, fallback to requests
try:
    import cloudscraper
    USE_CLOUDSCRAPER = True
except ImportError:
    USE_CLOUDSCRAPER = False
    print("[WARNING] cloudscraper not installed. Install with: pip install cloudscraper")
    print("          This may cause 403 errors. Using requests library instead.")


class GMGNClient:
    """Client for interacting with GMGN API"""
    
    def __init__(self, cookies: Optional[Dict[str, str]] = None, use_cloudscraper: bool = True, 
                 device_id: Optional[str] = None, fp_did: Optional[str] = None):
        self.base_url = "https://gmgn.ai/defi/quotation/v1"
        
        # Use cloudscraper if available (bypasses Cloudflare)
        if use_cloudscraper and USE_CLOUDSCRAPER:
            # Create scraper with delay to handle Cloudflare challenges
            self.session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                },
                delay=10  # Wait 10 seconds for Cloudflare challenge
            )
        else:
            self.session = requests.Session()
        
        # Use provided device IDs or generate new ones
        # Note: Using the same device_id/fp_did from browser session works better
        self.device_id = device_id or str(uuid.uuid4())
        self.fp_did = fp_did or self._generate_fp_did()
        self.client_id = "gmgn_web_20251203-8272-425773e"
        self.app_ver = "20251203-8272-425773e"
        
        # Set default headers to mimic browser (exact match from working request)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://gmgn.ai/trade/iMPLjKQt?chain=bsc',
            'Origin': 'https://gmgn.ai',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=1, i',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        })
        
        # Set cookies if provided (required to avoid 403 Forbidden from Cloudflare)
        if cookies:
            # If cookies is a dict, update session cookies
            if isinstance(cookies, dict):
                for key, value in cookies.items():
                    self.session.cookies.set(key, value, domain='.gmgn.ai')
            # If cookies is a string (cookie header format), parse it
            elif isinstance(cookies, str):
                from cookie_helper import parse_cookie_string
                cookies_dict = parse_cookie_string(cookies)
                for key, value in cookies_dict.items():
                    self.session.cookies.set(key, value, domain='.gmgn.ai')
        
        # Make an initial request to establish session (helps with Cloudflare)
        try:
            self.session.get('https://gmgn.ai/', timeout=10)
        except:
            pass  # Ignore errors on initial request
    
    def _generate_fp_did(self) -> str:
        """Generate fingerprint device ID (32 char hex string)"""
        return uuid.uuid4().hex[:32]
    
    def _get_base_params(self, tz_name: str = "Europe/London", tz_offset: int = 0) -> Dict[str, Any]:
        """Get base query parameters for all requests"""
        return {
            'device_id': self.device_id,
            'fp_did': self.fp_did,
            'client_id': self.client_id,
            'from_app': 'gmgn',
            'app_ver': self.app_ver,
            'tz_name': tz_name,
            'tz_offset': tz_offset,
            'app_lang': 'en-US',
            'os': 'web',
            'worker': 0
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, method: str = "GET") -> Dict:
        """Make API request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Merge base params with custom params
        base_params = self._get_base_params()
        if params:
            base_params.update(params)
        
        try:
            if method == "GET":
                response = self.session.get(url, params=base_params, timeout=30, allow_redirects=False)
            else:
                response = self.session.post(url, json=params, params=base_params, timeout=30, allow_redirects=False)
            
            # Handle redirects (302)
            if response.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({response.status_code}). May need cookies or authentication.",
                    "status_code": response.status_code,
                    "location": response.headers.get("Location", "Unknown")
                }
            
            response.raise_for_status()
            
            # Handle brotli compression if needed
            try:
                return response.json()
            except (ValueError, json.JSONDecodeError) as json_err:
                # Try manual brotli decompression
                # Sometimes responses are Brotli-compressed even if Content-Encoding header is missing
                try:
                    import brotli
                    # Try decompressing regardless of Content-Encoding header
                    # Check if content looks like Brotli (starts with specific magic bytes)
                    content = response.content
                    if content and len(content) > 0:
                        # Try Brotli decompression
                        try:
                            decompressed = brotli.decompress(content)
                            decoded = decompressed.decode('utf-8')
                            return json.loads(decoded)
                        except (brotli.error, UnicodeDecodeError, json.JSONDecodeError):
                            # If Brotli fails, check Content-Encoding header as fallback
                            if response.headers.get('Content-Encoding') == 'br':
                                # Already tried above, so this is a fallback
                                pass
                except ImportError:
                    # brotli library not installed
                    pass
                except Exception as decompress_err:
                    # Other decompression errors
                    pass
                
                # Response is not JSON, return text with better error message
                content_preview = response.text[:500] if hasattr(response, 'text') and response.text else str(response.content[:500])
                encoding = response.headers.get('Content-Encoding', 'unknown')
                return {
                    "error": f"Failed to parse JSON response: {str(json_err)}. Content-Encoding: {encoding}",
                    "status_code": response.status_code,
                    "response_text": content_preview,
                    "content_encoding": encoding
                }
        except requests.exceptions.HTTPError as e:
            return {
                "error": f"HTTP {e.response.status_code}: {str(e)}",
                "status_code": e.response.status_code,
                "response_text": e.response.text[:500] if hasattr(e.response, 'text') else None
            }
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
    
    # Command implementations
    
    def get_first_buy_wallets(self, token_address: str, period: str = "7d") -> Dict:
        """
        Get first-buy wallets for a token (/fbuy).

        This uses the internal token trades endpoint:
        /vas/api/v1/token_trades/{chain}/{token}

        We then post-process trades to find the earliest BUY trade per wallet.
        """
        chain = "bsc"  # for now we only support BSC as per your use case
        url = f"https://gmgn.ai/vas/api/v1/token_trades/{chain}/{token_address}"

        # Start from base params to mimic browser
        params: Dict[str, Any] = self._get_base_params()
        # Token trades endpoint expects these extra query params
        params.update({
            "limit": 500,     # fetch enough trades to find early buyers
            "maker": "",
            "revert": "true",  # newest first from API; we'll re-sort
        })

        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            raw = resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse token_trades response: {e}"}

        # Extract trades list from response; handle a few possible shapes
        trades: List[Dict[str, Any]] = []
        if isinstance(raw, list):
            trades = [t for t in raw if isinstance(t, dict)]
        elif isinstance(raw, dict):
            d = raw.get("data")
            if isinstance(d, list):
                trades = [t for t in d if isinstance(t, dict)]
            elif isinstance(d, dict):
                # Observed shape from /vas/api/v1/token_trades:
                # { "code": 0, "data": { "history": [ ... ], "next": ... } }
                # Prefer "history" if present
                if isinstance(d.get("history"), list):
                    trades = [t for t in d.get("history", []) if isinstance(t, dict)]
                else:
                    # fallback to other common keys if API changes
                    for key in ("list", "rows", "trades"):
                        v = d.get(key)
                        if isinstance(v, list):
                            trades = [t for t in v if isinstance(t, dict)]
                            break

        if not trades:
            return {"code": 0, "msg": "no trades", "data": {"rank": []}}

        # Helper: get timestamp from a trade item
        def _get_ts(t: Dict[str, Any]) -> float:
            for key in ("timestamp", "ts", "time", "block_time", "created_at"):
                if key in t:
                    try:
                        val = t[key]
                        # If it's already numeric (unix seconds)
                        if isinstance(val, (int, float)):
                            return float(val)
                        # If it's string, try parse as int
                        return float(val)
                    except Exception:
                        continue
            return 0.0

        # Sort trades by time ascending (earliest first)
        trades_sorted = sorted(trades, key=_get_ts)

        first_buys: Dict[str, Dict[str, Any]] = {}

        for t in trades_sorted:
            if not isinstance(t, dict):
                continue

            # Skip dev/creator buys (token deployer etc.)
            maker_token_tags = t.get("maker_token_tags") or []
            maker_event_tags = t.get("maker_event_tags") or []
            all_tags = [str(x).lower() for x in (maker_token_tags + maker_event_tags)]
            if any(tag in ("creator", "deployer", "owner") for tag in all_tags):
                # treat as dev buy; do not include in first-buy list
                continue

            # Determine side: we only care about BUY trades
            # In observed JSON, field is "event": "buy" / "sell"
            side = (
                t.get("event")
                or t.get("side")
                or t.get("trade_type")
                or t.get("direction")
            )
            if side is None:
                # Some APIs use boolean flags
                if t.get("is_buy") is True:
                    side = "buy"
            if not side or str(side).lower() != "buy":
                continue

            # Determine wallet field name (observed field: "maker")
            wallet = (
                t.get("maker")
                or t.get("trader")
                or t.get("wallet_address")
                or t.get("from")
                or t.get("address")
            )
            if not wallet:
                continue

            if wallet in first_buys:
                # we already recorded the earliest buy for this wallet
                continue

            # Value / amount fields (based on observed JSON)
            # base_amount: token amount, amount_usd: USD value, price_usd: price
            amount = (
                t.get("base_amount")
                or t.get("amount")
                or t.get("token_amount")
                or t.get("qty")
            )
            value_usd = (
                t.get("amount_usd")
                or t.get("value_usd")
                or t.get("usd_value")
                or t.get("volume_usd")
            )
            price = t.get("price_usd") or t.get("price") or t.get("avg_price")

            first_buys[wallet] = {
                "wallet": wallet,
                "address": wallet,
                "amount": amount,
                "value_usd": value_usd,
                "price": price,
                "timestamp": _get_ts(t),
            }

        # Convert dict to list, sort by timestamp asc (earliest first)
        items = sorted(first_buys.values(), key=lambda x: x["timestamp"])

        # Also extract token metadata from first trade if available
        token_name = None
        token_symbol = None
        deployer_address = None
        deploy_timestamp = None
        deploy_tx_hash = None
        
        
        if trades:
            # Try to get token info from first trade
            first_trade = trades[0]
            token_info = first_trade.get("token") or {}
            token_name = token_info.get("name") or first_trade.get("token_name")
            token_symbol = token_info.get("symbol") or first_trade.get("token_symbol")
            deploy_timestamp = token_info.get("creation_timestamp") or token_info.get("open_timestamp")
            
            # Look for deployer in maker_token_tags or from first trade maker if it's a creator
            # The first trade with "creator" tag is likely the deployer
            for trade in trades_sorted:
                maker_token_tags = trade.get("maker_token_tags") or []
                if "creator" in [str(t).lower() for t in maker_token_tags]:
                    if not deployer_address:
                        deployer_address = trade.get("maker")
                    # Get deploy tx from first trade with creator tag (creation transaction)
                    if not deploy_tx_hash:
                        deploy_tx_hash = trade.get("tx_hash")
                    break
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                # Use 'rank' so the existing formatter can display it
                "rank": items,
                "token_address": token_address,
                "token_name": token_name,
                "token_symbol": token_symbol,
                "deployer_address": deployer_address,
                "deploy_timestamp": deploy_timestamp,
                "deploy_tx_hash": deploy_tx_hash,
            },
        }
    
    def get_token_info(self, token_address: str, chain: str = "bsc") -> Dict:
        """
        Get token metadata including deployer info.
        
        Uses: POST /api/v1/mutil_window_token_info
        Request body: {"chain": "bsc", "addresses": ["0x..."]}
        Response: data[0].dev.creator_address contains the deployer address
        """
        url = "https://gmgn.ai/api/v1/mutil_window_token_info"
        params = self._get_base_params()
        
        # Request body format: {"chain": "bsc", "addresses": ["0x..."]}
        payload = {
            "chain": chain,
            "addresses": [token_address]
        }
        
        try:
            # Set proper headers for JSON POST
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
            }
            # Debug: print the request details
            import json as json_lib
            payload_json = json_lib.dumps(payload)
            print(f"DEBUG get_token_info: URL={url}")
            print(f"DEBUG get_token_info: payload (as JSON string)={payload_json}")
            print(f"DEBUG get_token_info: params={params}")
            print(f"DEBUG get_token_info: headers={headers}")
            print(f"DEBUG get_token_info: cookies={dict(self.session.cookies)}")
            
            resp = self.session.post(url, params=params, json=payload, headers=headers, timeout=30, allow_redirects=False)
            
            print(f"DEBUG get_token_info: Status={resp.status_code}")
            print(f"DEBUG get_token_info: Response headers={dict(resp.headers)}")
            try:
                response_json = resp.json()
                print(f"DEBUG get_token_info: Response JSON={response_json}")
            except:
                response_text = resp.text[:500] if hasattr(resp, 'text') else str(resp.content[:500])
                print(f"DEBUG get_token_info: Response text={response_text}")
            
            # Handle redirects
            if resp.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({resp.status_code})",
                    "status_code": resp.status_code,
                }
            
            resp.raise_for_status()
            
            # Handle brotli compression if needed
            try:
                return resp.json()
            except (ValueError, json.JSONDecodeError):
                # Try manual brotli decompression
                try:
                    import brotli
                    if resp.headers.get('Content-Encoding') == 'br':
                        decompressed = brotli.decompress(resp.content)
                        return json.loads(decompressed.decode('utf-8'))
                except:
                    pass
                
                return {
                    "error": "Response is not JSON",
                    "status_code": resp.status_code,
                    "response_text": resp.text[:500] if hasattr(resp, 'text') else str(resp.content[:500])
                }
        except requests.exceptions.HTTPError as e:
            return {
                "error": f"HTTP {e.response.status_code}: {str(e)}",
                "status_code": e.response.status_code,
                "response_text": e.response.text[:500] if hasattr(e.response, 'text') else None
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse token info response: {e}"}
    
    def get_wallet_holding_stats(self, wallet_address: str, token_address: str, chain: str = "bsc") -> Dict:
        """
        Get per-wallet stats for a specific token (used by /fbuy).
        
        Uses: /pf/api/v1/wallet/{chain}/{wallet}/holding?token_address={token}
        """
        url = f"https://gmgn.ai/pf/api/v1/wallet/{chain}/{wallet_address}/holding"
        params = self._get_base_params()
        params.update({
            "token_address": token_address,
        })
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse wallet holding response: {e}"}
    
    def get_wallet_profit_stat(self, wallet_address: str, period: str = "7d", chain: str = "bsc") -> Dict:
        """
        Get wallet profit statistics including hold time analysis (/ht).
        
        Uses: /pf/api/v1/wallet/{chain}/{wallet}/profit_stat/{period}
        """
        url = f"https://gmgn.ai/pf/api/v1/wallet/{chain}/{wallet_address}/profit_stat/{period}"
        params = self._get_base_params()
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            
            # Handle brotli compression if needed
            try:
                return resp.json()
            except (ValueError, json.JSONDecodeError):
                # Try manual brotli decompression
                try:
                    import brotli
                    if resp.headers.get('Content-Encoding') == 'br':
                        decompressed = brotli.decompress(resp.content)
                        return json.loads(decompressed.decode('utf-8'))
                except:
                    pass
                
                return {
                    "error": "Response is not JSON",
                    "status_code": resp.status_code,
                    "response_text": resp.text[:500] if hasattr(resp, 'text') else str(resp.content[:500])
                }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse wallet profit stat response: {e}"}
    
    def get_wallet_holdings(self, wallet_address: str, chain: str = "bsc", limit: int = 500) -> Dict:
        """
        Get all token holdings for a wallet (used to calculate hold times).
        
        Uses: /pf/api/v1/wallet/{chain}/{wallet}/holdings
        """
        url = f"https://gmgn.ai/pf/api/v1/wallet/{chain}/{wallet_address}/holdings"
        params = self._get_base_params()
        params.update({
            "limit": limit,
            "order_by": "last_active_timestamp",
            "direction": "desc",
            "hide_airdrop": "false",
            "hide_abnormal": "false",
            "hide_closed": "false",
            "sellout": "true",
            "showsmall": "true",
            "tx30d": "true",
        })
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            
            # Handle brotli compression if needed
            try:
                return resp.json()
            except (ValueError, json.JSONDecodeError):
                # Try manual brotli decompression
                try:
                    import brotli
                    if resp.headers.get('Content-Encoding') == 'br':
                        decompressed = brotli.decompress(resp.content)
                        return json.loads(decompressed.decode('utf-8'))
                except:
                    pass
                
                return {
                    "error": "Response is not JSON",
                    "status_code": resp.status_code,
                    "response_text": resp.text[:500] if hasattr(resp, 'text') else str(resp.content[:500])
                }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse wallet holdings response: {e}"}
    
    def get_profitable_wallets(self, token_address: str, period: str = "7d") -> Dict:
        """
        Get profitable wallets for a token (/pro).
        
        Uses: /vas/api/v1/token_traders/bsc/{token_address}
        """
        chain = "bsc"  # for now we only support BSC
        url = f"https://gmgn.ai/vas/api/v1/token_traders/{chain}/{token_address}"
        
        # Start from base params
        params: Dict[str, Any] = self._get_base_params()
        # Token traders endpoint expects these query params
        params.update({
            "limit": 100,
            "orderby": "profit",
            "direction": "desc",
        })
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            raw = resp.json()
            return raw
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse token_traders response: {e}"}
    
    def get_hold_time(self, token_address: str) -> Dict:
        """
        Get how long wallets hold a token before selling (/ht).
        
        Uses: /vas/api/v1/token_trades/{chain}/{token_address}
        Gets all trades and calculates hold times from buy-sell pairs.
        """
        chain = "bsc"  # for now we only support BSC
        url = f"https://gmgn.ai/vas/api/v1/token_trades/{chain}/{token_address}"
        
        # Start from base params
        params: Dict[str, Any] = self._get_base_params()
        # Token trades endpoint expects these query params
        params.update({
            "limit": 2000,  # Get more trades for accurate statistics
            "maker": "",
            "revert": "true",  # newest first from API
        })
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            raw = resp.json()
            return raw
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse token_trades response: {e}"}
    
    def get_most_profitable_wallets(self, period: str = "7d") -> Dict:
        """
        Get most profitable wallets on BSC (/mpro).

        Uses: /defi/quotation/v1/rank/bsc/wallets/{period}
        Example (7d):
        ?tag=smart_degen&tag=pump_smart&orderby=pnl_7d&direction=desc
        """
        endpoint = f"/rank/bsc/wallets/{period}"
        
        # Map period to pnl field
        pnl_field = {
            '1d': 'pnl_1d',
            '7d': 'pnl_7d',
            '30d': 'pnl_30d'
        }.get(period, 'pnl_7d')
        
        base_params = self._get_base_params()
        query: Dict[str, Any] = {
            **base_params,
            "orderby": pnl_field,
            "direction": "desc",
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            # tags must be repeated: &tag=smart_degen&tag=pump_smart
            tag_params = [("tag", "smart_degen"), ("tag", "pump_smart")]
            query_items = list(query.items()) + tag_params
            
            resp = self.session.get(url, params=query_items, timeout=30, allow_redirects=False)
            
            if resp.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({resp.status_code}). May need cookies or authentication.",
                    "status_code": resp.status_code,
                    "location": resp.headers.get("Location", "Unknown"),
                }
            
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse most profitable wallets response: {e}"}
    
    def get_profitable_deployers(self, period: str = "24h") -> Dict:
        """
        Get most profitable tokens (/pd).
        
        Uses: /api/v1/rank/bsc/swaps/{period}
        Period can be: 1h, 6h, 24h
        """
        # Map period to API format
        period_map = {
            '1h': '1h',
            '6h': '6h',
            '24h': '24h',
            '1d': '24h',  # Map 1d to 24h
        }
        api_period = period_map.get(period.lower(), '24h')
        
        url = f"https://gmgn.ai/api/v1/rank/bsc/swaps/{api_period}"
        base_params = self._get_base_params()
        
        # Build params - use list for filters[] to handle array parameters
        params = []
        for key, value in base_params.items():
            params.append((key, value))
        
        params.extend([
            ('orderby', 'history_highest_market_cap'),
            ('direction', 'desc'),
            ('min_created', '0m'),
            ('max_created', '1440m'),
            ('filters[]', 'not_honeypot'),
            ('filters[]', 'verified'),
            ('filters[]', 'renounced')
        ])
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            
            # Handle brotli compression if needed
            try:
                return resp.json()
            except (ValueError, json.JSONDecodeError):
                # Try manual brotli decompression
                try:
                    import brotli
                    if resp.headers.get('Content-Encoding') == 'br':
                        decompressed = brotli.decompress(resp.content)
                        return json.loads(decompressed.decode('utf-8'))
                except:
                    pass
                
                return {
                    "error": "Response is not JSON",
                    "status_code": resp.status_code,
                    "response_text": resp.text[:500] if hasattr(resp, 'text') else str(resp.content[:500])
                }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse profitable tokens response: {e}"}
    
    def get_low_tx_profitable_wallets(self, period: str = "7d", tx_min: int = 1, tx_max: int = 10) -> Dict:
        """
        Get profitable wallets with low transaction count (/lowtxp).

        Uses: /defi/quotation/v1/rank/bsc/wallets/{period}
        Example (7d):
        ?tag=smart_degen&tag=pump_smart&orderby=pnl_30d&direction=desc&min_txs=100&max_txs=500
        """
        endpoint = f"/rank/bsc/wallets/{period}"

        # Order by longer-term PnL (30d) to find consistently good wallets
        pnl_field = "pnl_30d"

        params = {
            "orderby": pnl_field,
            "direction": "desc",
            # Transaction count filters
            "min_txs": tx_min,
            "max_txs": tx_max,
            # Smart degen tags, as seen in working request
            "tag": ["smart_degen", "pump_smart"],
        }

        # _make_request doesn't support list values for params, so build manually
        base_params = self._get_base_params()
        query: Dict[str, Any] = {**base_params, "orderby": pnl_field, "direction": "desc", "min_txs": tx_min, "max_txs": tx_max}

        # We will pass tags via requests directly since _make_request flattens dicts
        url = f"{self.base_url}{endpoint}"
        try:
            # tags must be passed as repeated query params: &tag=smart_degen&tag=pump_smart
            tag_params = [("tag", "smart_degen"), ("tag", "pump_smart")]
            # Convert dict query to list of tuples then extend with tag_params
            query_items = list(query.items()) + tag_params

            resp = self.session.get(url, params=query_items, timeout=30, allow_redirects=False)
            if resp.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({resp.status_code}). May need cookies or authentication.",
                    "status_code": resp.status_code,
                    "location": resp.headers.get("Location", "Unknown"),
                }
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse low-tx profitable wallets response: {e}"}
    
    def get_kol_profitability(self, kol_name: str, period: str = "7d") -> Dict:
        """Get KOL wallet profitability (/kol)"""
        # NOTE: Old implementation used a dedicated /kol endpoint.
        # The site now uses generic wallet profit stats combined with search:
        # 1) GET /vas/api/v1/search_v3?chain=bsc&q={kol_name}  -> find wallet
        # 2) GET /pf/api/v1/wallet/{chain}/{wallet}/profit_stat/{period} -> stats
        #
        # We keep this method for backward compatibility but callers should
        # prefer: search_wallet_by_kol_name + get_wallet_profit_stat.
        wallet_search = self.search_wallet_by_kol_name(kol_name)
        if "error" in wallet_search:
            return wallet_search
        data = wallet_search.get("data", {}) or {}
        wallets = data.get("wallets") or []
        if not wallets:
            return {"error": f"No wallet found for KOL '{kol_name}'", "data": {}}
        # Pick first BSC wallet
        wallet = None
        for w in wallets:
            if isinstance(w, dict) and w.get("chain") == "bsc":
                wallet = w
                break
        if wallet is None:
            wallet = wallets[0] if isinstance(wallets[0], dict) else None
        if not wallet:
            return {"error": f"No valid wallet record for KOL '{kol_name}'", "data": {}}
        address = wallet.get("address")
        if not address:
            return {"error": f"No wallet address for KOL '{kol_name}'", "data": {}}
        # Delegate to wallet profit stat endpoint
        stats = self.get_wallet_profit_stat(address, period)
        # Attach basic KOL metadata for formatting
        if "data" in stats and isinstance(stats["data"], dict):
            stats["data"]["_kol_meta"] = {
                "address": address,
                "twitter_username": wallet.get("twitter_username"),
                "twitter_name": wallet.get("twitter_name"),
                "twitter_fans_num": wallet.get("twitter_fans_num"),
            }
        return stats

    def search_wallet_by_kol_name(self, kol_name: str, chain: str = "bsc") -> Dict:
        """
        Search GMGN for a KOL by name/handle and return wallet info.

        Uses: GET https://gmgn.ai/vas/api/v1/search_v3?chain=bsc&q={kol_name}
        """
        url = "https://gmgn.ai/vas/api/v1/search_v3"
        params: Dict[str, Any] = self._get_base_params()
        params.update({
            "chain": chain,
            "q": kol_name,
        })
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse KOL search response: {e}"}
    
    def get_high_volume_wallets(self, period: str = "7d") -> Dict:
        """
        Get high-volume wallets (/hvol).

        Uses: /defi/quotation/v1/rank/bsc/wallets/{period}
        Fetches wallets ordered by txs (we'll calculate volume = avg_cost * txs and sort client-side).
        Example (7d):
        ?tag=smart_degen&tag=pump_smart&orderby=txs&direction=desc
        """
        endpoint = f"/rank/bsc/wallets/{period}"

        base_params = self._get_base_params()
        query: Dict[str, Any] = {
            **base_params,
            "orderby": "txs",  # Order by transaction count, we'll sort by calculated volume client-side
            "direction": "desc",
        }

        url = f"{self.base_url}{endpoint}"

        try:
            # tags must be repeated: &tag=smart_degen&tag=pump_smart
            tag_params = [("tag", "smart_degen"), ("tag", "pump_smart")]
            query_items = list(query.items()) + tag_params

            resp = self.session.get(url, params=query_items, timeout=30, allow_redirects=False)

            if resp.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({resp.status_code}). May need cookies or authentication.",
                    "status_code": resp.status_code,
                    "location": resp.headers.get("Location", "Unknown"),
                }

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse high volume wallets response: {e}"}
    
    def get_high_activity_wallets(self, period: str = "7d") -> Dict:
        """
        Get high-activity (high transaction) wallets (/hact).

        Uses: /defi/quotation/v1/rank/bsc/wallets/{period}
        Example (7d):
        ?tag=smart_degen&tag=pump_smart&orderby=txs&direction=desc
        """
        endpoint = f"/rank/bsc/wallets/{period}"

        base_params = self._get_base_params()
        query: Dict[str, Any] = {
            **base_params,
            "orderby": "txs",   # sort by total transactions as in your example
            "direction": "desc",
        }

        url = f"{self.base_url}{endpoint}"

        try:
            # tags must be repeated: &tag=smart_degen&tag=pump_smart
            tag_params = [("tag", "smart_degen"), ("tag", "pump_smart")]
            query_items = list(query.items()) + tag_params

            resp = self.session.get(url, params=query_items, timeout=30, allow_redirects=False)

            if resp.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({resp.status_code}). May need cookies or authentication.",
                    "status_code": resp.status_code,
                    "location": resp.headers.get("Location", "Unknown"),
                }

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse high-activity wallets response: {e}"}
        self.base_url = "https://gmgn.ai/defi/quotation/v1"
        
        # Use cloudscraper if available (bypasses Cloudflare)
        if use_cloudscraper and USE_CLOUDSCRAPER:
            # Create scraper with delay to handle Cloudflare challenges
            self.session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                },
                delay=10  # Wait 10 seconds for Cloudflare challenge
            )
        else:
            self.session = requests.Session()
        
        # Use provided device IDs or generate new ones
        # Note: Using the same device_id/fp_did from browser session works better
        self.device_id = device_id or str(uuid.uuid4())
        self.fp_did = fp_did or self._generate_fp_did()
        self.client_id = "gmgn_web_20251203-8272-425773e"
        self.app_ver = "20251203-8272-425773e"
        
        # Set default headers to mimic browser (exact match from working request)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://gmgn.ai/trade/iMPLjKQt?chain=bsc',
            'Origin': 'https://gmgn.ai',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=1, i',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        })
        
        # Set cookies if provided (required to avoid 403 Forbidden from Cloudflare)
        if cookies:
            # If cookies is a dict, update session cookies
            if isinstance(cookies, dict):
                for key, value in cookies.items():
                    self.session.cookies.set(key, value, domain='.gmgn.ai')
            # If cookies is a string (cookie header format), parse it
            elif isinstance(cookies, str):
                from cookie_helper import parse_cookie_string
                cookies_dict = parse_cookie_string(cookies)
                for key, value in cookies_dict.items():
                    self.session.cookies.set(key, value, domain='.gmgn.ai')
        
        # Make an initial request to establish session (helps with Cloudflare)
        try:
            self.session.get('https://gmgn.ai/', timeout=10)
        except:
            pass  # Ignore errors on initial request
    
    def _generate_fp_did(self) -> str:
        """Generate fingerprint device ID (32 char hex string)"""
        return uuid.uuid4().hex[:32]
    
    def _get_base_params(self, tz_name: str = "Europe/London", tz_offset: int = 0) -> Dict[str, Any]:
        """Get base query parameters for all requests"""
        return {
            'device_id': self.device_id,
            'fp_did': self.fp_did,
            'client_id': self.client_id,
            'from_app': 'gmgn',
            'app_ver': self.app_ver,
            'tz_name': tz_name,
            'tz_offset': tz_offset,
            'app_lang': 'en-US',
            'os': 'web',
            'worker': 0
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, method: str = "GET") -> Dict:
        """Make API request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Merge base params with custom params
        base_params = self._get_base_params()
        if params:
            base_params.update(params)
        
        try:
            if method == "GET":
                response = self.session.get(url, params=base_params, timeout=30, allow_redirects=False)
            else:
                response = self.session.post(url, json=params, params=base_params, timeout=30, allow_redirects=False)
            
            # Handle redirects (302)
            if response.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({response.status_code}). May need cookies or authentication.",
                    "status_code": response.status_code,
                    "location": response.headers.get("Location", "Unknown")
                }
            
            response.raise_for_status()
            
            # Handle brotli compression if needed
            try:
                return response.json()
            except (ValueError, json.JSONDecodeError) as json_err:
                # Try manual brotli decompression
                # Sometimes responses are Brotli-compressed even if Content-Encoding header is missing
                try:
                    import brotli
                    # Try decompressing regardless of Content-Encoding header
                    # Check if content looks like Brotli (starts with specific magic bytes)
                    content = response.content
                    if content and len(content) > 0:
                        # Try Brotli decompression
                        try:
                            decompressed = brotli.decompress(content)
                            decoded = decompressed.decode('utf-8')
                            return json.loads(decoded)
                        except (brotli.error, UnicodeDecodeError, json.JSONDecodeError):
                            # If Brotli fails, check Content-Encoding header as fallback
                            if response.headers.get('Content-Encoding') == 'br':
                                # Already tried above, so this is a fallback
                                pass
                except ImportError:
                    # brotli library not installed
                    pass
                except Exception as decompress_err:
                    # Other decompression errors
                    pass
                
                # Response is not JSON, return text with better error message
                content_preview = response.text[:500] if hasattr(response, 'text') and response.text else str(response.content[:500])
                encoding = response.headers.get('Content-Encoding', 'unknown')
                return {
                    "error": f"Failed to parse JSON response: {str(json_err)}. Content-Encoding: {encoding}",
                    "status_code": response.status_code,
                    "response_text": content_preview,
                    "content_encoding": encoding
                }
        except requests.exceptions.HTTPError as e:
            return {
                "error": f"HTTP {e.response.status_code}: {str(e)}",
                "status_code": e.response.status_code,
                "response_text": e.response.text[:500] if hasattr(e.response, 'text') else None
            }
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
    
    # Command implementations
    
    def get_first_buy_wallets(self, token_address: str, period: str = "7d") -> Dict:
        """
        Get first-buy wallets for a token (/fbuy).

        This uses the internal token trades endpoint:
        /vas/api/v1/token_trades/{chain}/{token}

        We then post-process trades to find the earliest BUY trade per wallet.
        """
        chain = "bsc"  # for now we only support BSC as per your use case
        url = f"https://gmgn.ai/vas/api/v1/token_trades/{chain}/{token_address}"

        # Start from base params to mimic browser
        params: Dict[str, Any] = self._get_base_params()
        # Token trades endpoint expects these extra query params
        params.update({
            "limit": 500,     # fetch enough trades to find early buyers
            "maker": "",
            "revert": "true",  # newest first from API; we'll re-sort
        })

        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            raw = resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse token_trades response: {e}"}

        # Extract trades list from response; handle a few possible shapes
        trades: List[Dict[str, Any]] = []
        if isinstance(raw, list):
            trades = [t for t in raw if isinstance(t, dict)]
        elif isinstance(raw, dict):
            d = raw.get("data")
            if isinstance(d, list):
                trades = [t for t in d if isinstance(t, dict)]
            elif isinstance(d, dict):
                # Observed shape from /vas/api/v1/token_trades:
                # { "code": 0, "data": { "history": [ ... ], "next": ... } }
                # Prefer "history" if present
                if isinstance(d.get("history"), list):
                    trades = [t for t in d.get("history", []) if isinstance(t, dict)]
                else:
                    # fallback to other common keys if API changes
                    for key in ("list", "rows", "trades"):
                        v = d.get(key)
                        if isinstance(v, list):
                            trades = [t for t in v if isinstance(t, dict)]
                            break

        if not trades:
            return {"code": 0, "msg": "no trades", "data": {"rank": []}}

        # Helper: get timestamp from a trade item
        def _get_ts(t: Dict[str, Any]) -> float:
            for key in ("timestamp", "ts", "time", "block_time", "created_at"):
                if key in t:
                    try:
                        val = t[key]
                        # If it's already numeric (unix seconds)
                        if isinstance(val, (int, float)):
                            return float(val)
                        # If it's string, try parse as int
                        return float(val)
                    except Exception:
                        continue
            return 0.0

        # Sort trades by time ascending (earliest first)
        trades_sorted = sorted(trades, key=_get_ts)

        first_buys: Dict[str, Dict[str, Any]] = {}

        for t in trades_sorted:
            if not isinstance(t, dict):
                continue

            # Skip dev/creator buys (token deployer etc.)
            maker_token_tags = t.get("maker_token_tags") or []
            maker_event_tags = t.get("maker_event_tags") or []
            all_tags = [str(x).lower() for x in (maker_token_tags + maker_event_tags)]
            if any(tag in ("creator", "deployer", "owner") for tag in all_tags):
                # treat as dev buy; do not include in first-buy list
                continue

            # Determine side: we only care about BUY trades
            # In observed JSON, field is "event": "buy" / "sell"
            side = (
                t.get("event")
                or t.get("side")
                or t.get("trade_type")
                or t.get("direction")
            )
            if side is None:
                # Some APIs use boolean flags
                if t.get("is_buy") is True:
                    side = "buy"
            if not side or str(side).lower() != "buy":
                continue

            # Determine wallet field name (observed field: "maker")
            wallet = (
                t.get("maker")
                or t.get("trader")
                or t.get("wallet_address")
                or t.get("from")
                or t.get("address")
            )
            if not wallet:
                continue

            if wallet in first_buys:
                # we already recorded the earliest buy for this wallet
                continue

            # Value / amount fields (based on observed JSON)
            # base_amount: token amount, amount_usd: USD value, price_usd: price
            amount = (
                t.get("base_amount")
                or t.get("amount")
                or t.get("token_amount")
                or t.get("qty")
            )
            value_usd = (
                t.get("amount_usd")
                or t.get("value_usd")
                or t.get("usd_value")
                or t.get("volume_usd")
            )
            price = t.get("price_usd") or t.get("price") or t.get("avg_price")

            first_buys[wallet] = {
                "wallet": wallet,
                "address": wallet,
                "amount": amount,
                "value_usd": value_usd,
                "price": price,
                "timestamp": _get_ts(t),
            }

        # Convert dict to list, sort by timestamp asc (earliest first)
        items = sorted(first_buys.values(), key=lambda x: x["timestamp"])

        # Also extract token metadata from first trade if available
        token_name = None
        token_symbol = None
        deployer_address = None
        deploy_timestamp = None
        deploy_tx_hash = None
        
        
        if trades:
            # Try to get token info from first trade
            first_trade = trades[0]
            token_info = first_trade.get("token") or {}
            token_name = token_info.get("name") or first_trade.get("token_name")
            token_symbol = token_info.get("symbol") or first_trade.get("token_symbol")
            deploy_timestamp = token_info.get("creation_timestamp") or token_info.get("open_timestamp")
            
            # Look for deployer in maker_token_tags or from first trade maker if it's a creator
            # The first trade with "creator" tag is likely the deployer
            for trade in trades_sorted:
                maker_token_tags = trade.get("maker_token_tags") or []
                if "creator" in [str(t).lower() for t in maker_token_tags]:
                    if not deployer_address:
                        deployer_address = trade.get("maker")
                    # Get deploy tx from first trade with creator tag (creation transaction)
                    if not deploy_tx_hash:
                        deploy_tx_hash = trade.get("tx_hash")
                    break
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                # Use 'rank' so the existing formatter can display it
                "rank": items,
                "token_address": token_address,
                "token_name": token_name,
                "token_symbol": token_symbol,
                "deployer_address": deployer_address,
                "deploy_timestamp": deploy_timestamp,
                "deploy_tx_hash": deploy_tx_hash,
            },
        }
    
    def get_token_info(self, token_address: str, chain: str = "bsc") -> Dict:
        """
        Get token metadata including deployer info.
        
        Uses: POST /api/v1/mutil_window_token_info
        Request body: {"chain": "bsc", "addresses": ["0x..."]}
        Response: data[0].dev.creator_address contains the deployer address
        """
        url = "https://gmgn.ai/api/v1/mutil_window_token_info"
        params = self._get_base_params()
        
        # Request body format: {"chain": "bsc", "addresses": ["0x..."]}
        payload = {
            "chain": chain,
            "addresses": [token_address]
        }
        
        try:
            # Set proper headers for JSON POST
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
            }
            # Debug: print the request details
            import json as json_lib
            payload_json = json_lib.dumps(payload)
            print(f"DEBUG get_token_info: URL={url}")
            print(f"DEBUG get_token_info: payload (as JSON string)={payload_json}")
            print(f"DEBUG get_token_info: params={params}")
            print(f"DEBUG get_token_info: headers={headers}")
            print(f"DEBUG get_token_info: cookies={dict(self.session.cookies)}")
            
            resp = self.session.post(url, params=params, json=payload, headers=headers, timeout=30, allow_redirects=False)
            
            print(f"DEBUG get_token_info: Status={resp.status_code}")
            print(f"DEBUG get_token_info: Response headers={dict(resp.headers)}")
            try:
                response_json = resp.json()
                print(f"DEBUG get_token_info: Response JSON={response_json}")
            except:
                response_text = resp.text[:500] if hasattr(resp, 'text') else str(resp.content[:500])
                print(f"DEBUG get_token_info: Response text={response_text}")
            
            # Handle redirects
            if resp.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({resp.status_code})",
                    "status_code": resp.status_code,
                }
            
            resp.raise_for_status()
            
            # Handle brotli compression if needed
            try:
                return resp.json()
            except (ValueError, json.JSONDecodeError):
                # Try manual brotli decompression
                try:
                    import brotli
                    if resp.headers.get('Content-Encoding') == 'br':
                        decompressed = brotli.decompress(resp.content)
                        return json.loads(decompressed.decode('utf-8'))
                except:
                    pass
                
                return {
                    "error": "Response is not JSON",
                    "status_code": resp.status_code,
                    "response_text": resp.text[:500] if hasattr(resp, 'text') else str(resp.content[:500])
                }
        except requests.exceptions.HTTPError as e:
            return {
                "error": f"HTTP {e.response.status_code}: {str(e)}",
                "status_code": e.response.status_code,
                "response_text": e.response.text[:500] if hasattr(e.response, 'text') else None
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse token info response: {e}"}
    
    def get_wallet_holding_stats(self, wallet_address: str, token_address: str, chain: str = "bsc") -> Dict:
        """
        Get per-wallet stats for a specific token (used by /fbuy).
        
        Uses: /pf/api/v1/wallet/{chain}/{wallet}/holding?token_address={token}
        """
        url = f"https://gmgn.ai/pf/api/v1/wallet/{chain}/{wallet_address}/holding"
        params = self._get_base_params()
        params.update({
            "token_address": token_address,
        })
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse wallet holding response: {e}"}
    
    def get_wallet_profit_stat(self, wallet_address: str, period: str = "7d", chain: str = "bsc") -> Dict:
        """
        Get wallet profit statistics including hold time analysis (/ht).
        
        Uses: /pf/api/v1/wallet/{chain}/{wallet}/profit_stat/{period}
        """
        url = f"https://gmgn.ai/pf/api/v1/wallet/{chain}/{wallet_address}/profit_stat/{period}"
        params = self._get_base_params()
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            
            # Handle brotli compression if needed
            try:
                return resp.json()
            except (ValueError, json.JSONDecodeError):
                # Try manual brotli decompression
                try:
                    import brotli
                    if resp.headers.get('Content-Encoding') == 'br':
                        decompressed = brotli.decompress(resp.content)
                        return json.loads(decompressed.decode('utf-8'))
                except:
                    pass
                
                return {
                    "error": "Response is not JSON",
                    "status_code": resp.status_code,
                    "response_text": resp.text[:500] if hasattr(resp, 'text') else str(resp.content[:500])
                }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse wallet profit stat response: {e}"}
    
    def get_wallet_holdings(self, wallet_address: str, chain: str = "bsc", limit: int = 500) -> Dict:
        """
        Get all token holdings for a wallet (used to calculate hold times).
        
        Uses: /pf/api/v1/wallet/{chain}/{wallet}/holdings
        """
        url = f"https://gmgn.ai/pf/api/v1/wallet/{chain}/{wallet_address}/holdings"
        params = self._get_base_params()
        params.update({
            "limit": limit,
            "order_by": "last_active_timestamp",
            "direction": "desc",
            "hide_airdrop": "false",
            "hide_abnormal": "false",
            "hide_closed": "false",
            "sellout": "true",
            "showsmall": "true",
            "tx30d": "true",
        })
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            
            # Handle brotli compression if needed
            try:
                return resp.json()
            except (ValueError, json.JSONDecodeError):
                # Try manual brotli decompression
                try:
                    import brotli
                    if resp.headers.get('Content-Encoding') == 'br':
                        decompressed = brotli.decompress(resp.content)
                        return json.loads(decompressed.decode('utf-8'))
                except:
                    pass
                
                return {
                    "error": "Response is not JSON",
                    "status_code": resp.status_code,
                    "response_text": resp.text[:500] if hasattr(resp, 'text') else str(resp.content[:500])
                }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse wallet holdings response: {e}"}
    
    def get_profitable_wallets(self, token_address: str, period: str = "7d") -> Dict:
        """
        Get profitable wallets for a token (/pro).
        
        Uses: /vas/api/v1/token_traders/bsc/{token_address}
        """
        chain = "bsc"  # for now we only support BSC
        url = f"https://gmgn.ai/vas/api/v1/token_traders/{chain}/{token_address}"
        
        # Start from base params
        params: Dict[str, Any] = self._get_base_params()
        # Token traders endpoint expects these query params
        params.update({
            "limit": 100,
            "orderby": "profit",
            "direction": "desc",
        })
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            raw = resp.json()
            return raw
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse token_traders response: {e}"}
    
    def get_hold_time(self, token_address: str) -> Dict:
        """
        Get how long wallets hold a token before selling (/ht).
        
        Uses: /vas/api/v1/token_trades/{chain}/{token_address}
        Gets all trades and calculates hold times from buy-sell pairs.
        """
        chain = "bsc"  # for now we only support BSC
        url = f"https://gmgn.ai/vas/api/v1/token_trades/{chain}/{token_address}"
        
        # Start from base params
        params: Dict[str, Any] = self._get_base_params()
        # Token trades endpoint expects these query params
        params.update({
            "limit": 2000,  # Get more trades for accurate statistics
            "maker": "",
            "revert": "true",  # newest first from API
        })
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            raw = resp.json()
            return raw
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse token_trades response: {e}"}
    
    def get_most_profitable_wallets(self, period: str = "7d") -> Dict:
        """
        Get most profitable wallets on BSC (/mpro).

        Uses: /defi/quotation/v1/rank/bsc/wallets/{period}
        Example (7d):
        ?tag=smart_degen&tag=pump_smart&orderby=pnl_7d&direction=desc
        """
        endpoint = f"/rank/bsc/wallets/{period}"
        
        # Map period to pnl field
        pnl_field = {
            '1d': 'pnl_1d',
            '7d': 'pnl_7d',
            '30d': 'pnl_30d'
        }.get(period, 'pnl_7d')
        
        base_params = self._get_base_params()
        query: Dict[str, Any] = {
            **base_params,
            "orderby": pnl_field,
            "direction": "desc",
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            # tags must be repeated: &tag=smart_degen&tag=pump_smart
            tag_params = [("tag", "smart_degen"), ("tag", "pump_smart")]
            query_items = list(query.items()) + tag_params
            
            resp = self.session.get(url, params=query_items, timeout=30, allow_redirects=False)
            
            if resp.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({resp.status_code}). May need cookies or authentication.",
                    "status_code": resp.status_code,
                    "location": resp.headers.get("Location", "Unknown"),
                }
            
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse most profitable wallets response: {e}"}
    
    def get_profitable_deployers(self, period: str = "24h") -> Dict:
        # """
        # Get most profitable tokens (/pd).
        
        # Uses: /api/v1/rank/bsc/swaps/{period}
        # Period can be: 1h, 6h, 24h
        # """
        # Map period to API format
        period_map = {
            '1h': '1h',
            '6h': '6h',
            '24h': '24h',
            '1d': '24h',  # Map 1d to 24h
        }
        api_period = period_map.get(period.lower(), '24h')
        
        url = f"https://gmgn.ai/api/v1/rank/bsc/swaps/{api_period}"
        base_params = self._get_base_params()
        
        # Build params - use list for filters[] to handle array parameters
        params = []
        for key, value in base_params.items():
            params.append((key, value))
        
        params.extend([
            ('orderby', 'history_highest_market_cap'),
            ('direction', 'desc'),
            ('min_created', '0m'),
            ('max_created', '1440m'),
            ('filters[]', 'not_honeypot'),
            ('filters[]', 'verified'),
            ('filters[]', 'renounced')
        ])
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            
            # Handle brotli compression if needed
            try:
                return resp.json()
            except (ValueError, json.JSONDecodeError):
                # Try manual brotli decompression
                try:
                    import brotli
                    if resp.headers.get('Content-Encoding') == 'br':
                        decompressed = brotli.decompress(resp.content)
                        return json.loads(decompressed.decode('utf-8'))
                except:
                    pass
                
                return {
                    "error": "Response is not JSON",
                    "status_code": resp.status_code,
                    "response_text": resp.text[:500] if hasattr(resp, 'text') else str(resp.content[:500])
                }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse profitable tokens response: {e}"}
    
    def get_low_tx_profitable_wallets(self, period: str = "7d", tx_min: int = 1, tx_max: int = 10) -> Dict:
        """
        Get profitable wallets with low transaction count (/lowtxp).

        Uses: /defi/quotation/v1/rank/bsc/wallets/{period}
        Example (7d):
        ?tag=smart_degen&tag=pump_smart&orderby=pnl_30d&direction=desc&min_txs=100&max_txs=500
        """
        endpoint = f"/rank/bsc/wallets/{period}"

        # Order by longer-term PnL (30d) to find consistently good wallets
        pnl_field = "pnl_30d"

        params = {
            "orderby": pnl_field,
            "direction": "desc",
            # Transaction count filters
            "min_txs": tx_min,
            "max_txs": tx_max,
            # Smart degen tags, as seen in working request
            "tag": ["smart_degen", "pump_smart"],
        }

        # _make_request doesn't support list values for params, so build manually
        base_params = self._get_base_params()
        query: Dict[str, Any] = {**base_params, "orderby": pnl_field, "direction": "desc", "min_txs": tx_min, "max_txs": tx_max}

        # We will pass tags via requests directly since _make_request flattens dicts
        url = f"{self.base_url}{endpoint}"
        try:
            # tags must be passed as repeated query params: &tag=smart_degen&tag=pump_smart
            tag_params = [("tag", "smart_degen"), ("tag", "pump_smart")]
            # Convert dict query to list of tuples then extend with tag_params
            query_items = list(query.items()) + tag_params

            resp = self.session.get(url, params=query_items, timeout=30, allow_redirects=False)
            if resp.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({resp.status_code}). May need cookies or authentication.",
                    "status_code": resp.status_code,
                    "location": resp.headers.get("Location", "Unknown"),
                }
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse low-tx profitable wallets response: {e}"}
    
    def get_kol_profitability(self, kol_name: str, period: str = "7d") -> Dict:
        """Get KOL wallet profitability (/kol)"""
        # NOTE: Old implementation used a dedicated /kol endpoint.
        # The site now uses generic wallet profit stats combined with search:
        # 1) GET /vas/api/v1/search_v3?chain=bsc&q={kol_name}  -> find wallet
        # 2) GET /pf/api/v1/wallet/{chain}/{wallet}/profit_stat/{period} -> stats
        #
        # We keep this method for backward compatibility but callers should
        # prefer: search_wallet_by_kol_name + get_wallet_profit_stat.
        wallet_search = self.search_wallet_by_kol_name(kol_name)
        if "error" in wallet_search:
            return wallet_search
        data = wallet_search.get("data", {}) or {}
        wallets = data.get("wallets") or []
        if not wallets:
            return {"error": f"No wallet found for KOL '{kol_name}'", "data": {}}
        # Pick first BSC wallet
        wallet = None
        for w in wallets:
            if isinstance(w, dict) and w.get("chain") == "bsc":
                wallet = w
                break
        if wallet is None:
            wallet = wallets[0] if isinstance(wallets[0], dict) else None
        if not wallet:
            return {"error": f"No valid wallet record for KOL '{kol_name}'", "data": {}}
        address = wallet.get("address")
        if not address:
            return {"error": f"No wallet address for KOL '{kol_name}'", "data": {}}
        # Delegate to wallet profit stat endpoint
        stats = self.get_wallet_profit_stat(address, period)
        # Attach basic KOL metadata for formatting
        if "data" in stats and isinstance(stats["data"], dict):
            stats["data"]["_kol_meta"] = {
                "address": address,
                "twitter_username": wallet.get("twitter_username"),
                "twitter_name": wallet.get("twitter_name"),
                "twitter_fans_num": wallet.get("twitter_fans_num"),
            }
        return stats

    def search_wallet_by_kol_name(self, kol_name: str, chain: str = "bsc") -> Dict:
        """
        Search GMGN for a KOL by name/handle and return wallet info.

        Uses: GET https://gmgn.ai/vas/api/v1/search_v3?chain=bsc&q={kol_name}
        """
        url = "https://gmgn.ai/vas/api/v1/search_v3"
        params: Dict[str, Any] = self._get_base_params()
        params.update({
            "chain": chain,
            "q": kol_name,
        })
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse KOL search response: {e}"}
    
    def get_high_volume_wallets(self, period: str = "7d") -> Dict:
        """
        Get high-volume wallets (/hvol).

        Uses: /defi/quotation/v1/rank/bsc/wallets/{period}
        Fetches wallets ordered by txs (we'll calculate volume = avg_cost * txs and sort client-side).
        Example (7d):
        ?tag=smart_degen&tag=pump_smart&orderby=txs&direction=desc
        """
        endpoint = f"/rank/bsc/wallets/{period}"

        base_params = self._get_base_params()
        query: Dict[str, Any] = {
            **base_params,
            "orderby": "txs",  # Order by transaction count, we'll sort by calculated volume client-side
            "direction": "desc",
        }

        url = f"{self.base_url}{endpoint}"

        try:
            # tags must be repeated: &tag=smart_degen&tag=pump_smart
            tag_params = [("tag", "smart_degen"), ("tag", "pump_smart")]
            query_items = list(query.items()) + tag_params

            resp = self.session.get(url, params=query_items, timeout=30, allow_redirects=False)

            if resp.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({resp.status_code}). May need cookies or authentication.",
                    "status_code": resp.status_code,
                    "location": resp.headers.get("Location", "Unknown"),
                }

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse high volume wallets response: {e}"}
    
    def get_high_activity_wallets(self, period: str = "7d") -> Dict:
        """
        Get high-activity (high transaction) wallets (/hact).

        Uses: /defi/quotation/v1/rank/bsc/wallets/{period}
        Example (7d):
        ?tag=smart_degen&tag=pump_smart&orderby=txs&direction=desc
        """
        endpoint = f"/rank/bsc/wallets/{period}"

        base_params = self._get_base_params()
        query: Dict[str, Any] = {
            **base_params,
            "orderby": "txs",   # sort by total transactions as in your example
            "direction": "desc",
        }

        url = f"{self.base_url}{endpoint}"

        try:
            # tags must be repeated: &tag=smart_degen&tag=pump_smart
            tag_params = [("tag", "smart_degen"), ("tag", "pump_smart")]
            query_items = list(query.items()) + tag_params

            resp = self.session.get(url, params=query_items, timeout=30, allow_redirects=False)

            if resp.status_code in [301, 302, 303, 307, 308]:
                return {
                    "error": f"Redirected ({resp.status_code}). May need cookies or authentication.",
                    "status_code": resp.status_code,
                    "location": resp.headers.get("Location", "Unknown"),
                }

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(getattr(e, "response", None), "status_code", None),
            }
        except Exception as e:
            return {"error": f"Failed to parse high-activity wallets response: {e}"}


