import requests
import logging
import time
from typing import Tuple, Optional
from .config import cfg

logger = logging.getLogger(__name__)

# Simple in-memory token cache
# _CACHE = { 'token': str, 'expires_at': float }
_CACHE: dict = {}


def _get_cached_token() -> Optional[str]:
    now = time.time()
    tok = _CACHE.get('token')
    exp = _CACHE.get('expires_at')
    if tok and exp and now < exp:
        return tok
    return None


def _set_cached_token(token: str, ttl_seconds: Optional[int] = None) -> None:
    if ttl_seconds is None:
        # default short TTL to avoid permanent caching when no expiry provided
        ttl_seconds = 300
    _CACHE['token'] = token
    _CACHE['expires_at'] = time.time() + float(ttl_seconds) - 5.0  # small margin


def set_handday_token(token: str, ttl_seconds: Optional[int] = None) -> None:
    """Explicitly set a token into the in-memory cache.

    Use this when a token is obtained out-of-band (e.g., pasted into env or UI).
    """
    _set_cached_token(token, ttl_seconds)


def _extract_token_and_ttl(j: dict) -> Tuple[Optional[str], Optional[int]]:
    # Try common locations for token and expiry
    if not isinstance(j, dict):
        return None, None
    def find_token(d: dict):
        for k in ('access_token', 'token'):
            if k in d and isinstance(d[k], str):
                return d[k]
        return None

    token = find_token(j)
    if not token and 'data' in j and isinstance(j['data'], dict):
        token = find_token(j['data'])

    # expiry: try expires_in (seconds) or expires (timestamp)
    ttl = None
    if 'expires_in' in j and isinstance(j['expires_in'], (int, float, str)):
        try:
            ttl = int(j['expires_in'])
        except Exception:
            ttl = None
    elif 'data' in j and isinstance(j['data'], dict) and 'expires_in' in j['data']:
        try:
            ttl = int(j['data']['expires_in'])
        except Exception:
            ttl = None
    elif 'expires' in j and isinstance(j['expires'], (int, float)):
        # expires as a unix timestamp
        try:
            exp_ts = float(j['expires'])
            ttl = int(exp_ts - time.time())
        except Exception:
            ttl = None

    return token, ttl


def get_handday_token(force_refresh: bool = False) -> Tuple[bool, str]:
    """Fetch token from Handday token endpoint with simple in-memory caching.

    Returns (True, token) or (False, error_message).
    If force_refresh is False, a cached valid token will be returned.
    """
    # 1) If an explicit token is provided via environment var, use it (highest priority)
    env_tok = getattr(cfg, 'HANDDAY_TOKEN', None)
    if env_tok:
        logger.debug('Using token supplied via HANDDAY_TOKEN env var')
        _set_cached_token(env_tok, ttl_seconds=3600)
        return True, env_tok

    # 2) Return cached if available
    if not force_refresh:
        cached = _get_cached_token()
        if cached:
            logger.debug('Using cached Handday token')
            return True, cached

    url = cfg.HANDDAY_TOKEN_URL
    # build payload using available config values
    payload = {}
    if cfg.HANDDAY_CORP_ID:
        try:
            payload['corpId'] = int(cfg.HANDDAY_CORP_ID)
        except Exception:
            payload['corpId'] = cfg.HANDDAY_CORP_ID
    if cfg.HANDDAY_APP_TYPE:
        try:
            payload['appType'] = int(cfg.HANDDAY_APP_TYPE)
        except Exception:
            payload['appType'] = cfg.HANDDAY_APP_TYPE
    if cfg.HANDDAY_APP_ID:
        payload['appId'] = cfg.HANDDAY_APP_ID
    if cfg.HANDDAY_APP_SECRET:
        payload['appSecret'] = cfg.HANDDAY_APP_SECRET

    timeout = getattr(cfg, 'HANDDAY_AUTH_TIMEOUT', 5)

    # try POST
    try:
        logger.debug('Requesting Handday token POST %s', url)
        r = requests.post(url, json=payload or None, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        token, ttl = _extract_token_and_ttl(j)
        if token:
            _set_cached_token(token, ttl)
            return True, token
        return False, f'No token found in response JSON: {j}'
    except Exception as e_post:
        logger.warning('Handday token POST failed: %s', e_post)
        # fallback to GET
        try:
            params = {k: v for k, v in payload.items() if v is not None}
            logger.debug('Requesting Handday token GET %s params=%s', url, params)
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            j = r.json()
            token, ttl = _extract_token_and_ttl(j)
            if token:
                _set_cached_token(token, ttl)
                return True, token
            return False, f'No token found in GET response JSON: {j}'
        except Exception as e_get:
            logger.exception('Handday token GET also failed')
            return False, f'POST error: {e_post}; GET error: {e_get}'

