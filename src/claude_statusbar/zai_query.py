"""Query ZAI/ZHIPU platform usage API.

Port of zai-coding-plugins query-usage.mjs to Python.
Queries model-usage, tool-usage, and quota/limit endpoints using
ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN environment variables.
"""

import json
import logging
import os
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def _detect_platform() -> Optional[Tuple[str, str]]:
    """Return (platform_name, base_domain) or None if env vars not set/unsupported."""
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")

    if not base_url or not auth_token:
        return None

    if "api.z.ai" in base_url:
        platform = "ZAI"
    elif "open.bigmodel.cn" in base_url or "dev.bigmodel.cn" in base_url:
        platform = "ZHIPU"
    else:
        return None

    # Extract base domain (protocol + host)
    parsed = urllib.parse.urlparse(base_url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"

    return platform, base_domain


def _format_datetime(dt: datetime) -> str:
    """Format datetime as 'yyyy-MM-dd HH:mm:ss'."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _build_time_window() -> Tuple[str, str]:
    """Build time window: yesterday at current hour → today at current hour end (UTC)."""
    now = datetime.now(timezone.utc)
    # Use timedelta to handle month boundaries correctly
    yesterday = now - __import__("datetime").timedelta(days=1)
    start = datetime(yesterday.year, yesterday.month, yesterday.day, now.hour, 0, 0)
    end = datetime(now.year, now.month, now.day, now.hour, 59, 59)
    return _format_datetime(start), _format_datetime(end)


def _http_get(url: str, auth_token: str, timeout: int = 10) -> Dict[str, Any]:
    """Make an authenticated GET request and return parsed JSON."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": auth_token,
            "Accept-Language": "en-US,en",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def _process_quota_limits(data: Any) -> Dict[str, Any]:
    """Process quota limit response, extracting all TOKENS_LIMIT and TIME_LIMIT items.

    Platforms may return multiple TOKENS_LIMIT entries (e.g. short-term + long-term
    rolling windows).  We sort them by nextResetTime so that:
      - token_limits[0]  = shortest-window (used for "5h" bar)
      - token_limits[-1] = longest-window  (used for "7d" bar)
    """
    result: Dict[str, Any] = {
        "token_limits": [],
        "time_limit": None,
        "raw_limits": [],
    }

    if not data or not isinstance(data, dict):
        return result

    limits = data.get("limits", [])
    result["raw_limits"] = limits

    for item in limits:
        item_type = item.get("type", "")
        if item_type == "TOKENS_LIMIT":
            result["token_limits"].append(item)
        elif item_type == "TIME_LIMIT":
            result["time_limit"] = item

    result["token_limits"].sort(key=lambda x: x.get("nextResetTime", float("inf")))

    return result


def query_usage() -> Optional[Dict[str, Any]]:
    """Query ZAI/ZHIPU platform usage API.

    Returns a dict with:
      - platform: "ZAI" or "ZHIPU"
      - source: "zai-plugin"
      - model_usage: raw model usage data
      - tool_usage: raw tool usage data
      - quota_raw: raw limits list from the platform API
    Or None if the platform is not configured or query fails.
    """
    platform_info = _detect_platform()
    if platform_info is None:
        return None

    platform, base_domain = platform_info
    auth_token = os.environ["ANTHROPIC_AUTH_TOKEN"]

    model_usage_url = f"{base_domain}/api/monitor/usage/model-usage"
    tool_usage_url = f"{base_domain}/api/monitor/usage/tool-usage"
    quota_limit_url = f"{base_domain}/api/monitor/usage/quota/limit"

    start_time, end_time = _build_time_window()
    query_params = f"?startTime={urllib.parse.quote(start_time)}&endTime={urllib.parse.quote(end_time)}"

    result: Dict[str, Any] = {
        "platform": platform,
        "source": "zai-plugin",
        "model_usage": None,
        "tool_usage": None,
        "quota_raw": None,
    }

    try:
        try:
            resp = _http_get(model_usage_url + query_params, auth_token)
            result["model_usage"] = resp.get("data", resp)
        except Exception as e:
            logger.debug("Model usage query failed: %s", e)

        try:
            resp = _http_get(tool_usage_url + query_params, auth_token)
            result["tool_usage"] = resp.get("data", resp)
        except Exception as e:
            logger.debug("Tool usage query failed: %s", e)

        try:
            resp = _http_get(quota_limit_url, auth_token)
            raw_data = resp.get("data", resp)
            processed = _process_quota_limits(raw_data)
            result["quota_raw"] = processed["raw_limits"]
        except Exception as e:
            logger.debug("Quota limit query failed: %s", e)

        if result["quota_raw"] is None:
            return None

        return result

    except Exception as e:
        logger.error("ZAI plugin query failed: %s", e)
        return None
