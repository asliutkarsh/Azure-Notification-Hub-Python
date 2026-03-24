"""
Azure Notification Hubs — Platform notification factories.
Ported from @azure/notification-hubs JS SDK.

Supported platforms:
- Apple (APNs)
- FCM Legacy (GCM)
- FCM V1
- Windows (WNS — toast, tile, badge, raw)
- ADM (Amazon Device Messaging)
- Baidu
- Browser (Web Push)
- Template (cross-platform)
- Xiaomi
"""

import json
from typing import Any

# ─── Content Types ───────────────────────────────────────────────

JSON_CONTENT_TYPE = "application/json;charset=utf-8"
XML_CONTENT_TYPE = "application/xml"
STREAM_CONTENT_TYPE = "application/octet-stream"


# ─── Apple (APNs) ────────────────────────────────────────────────


def create_apple_notification(
    body: dict | str,
    headers: dict[str, str] | None = None,
) -> dict:
    """
    Create an Apple Push Notification (APNs).

    body: Apple native message dict or JSON string.
          Structure: { "aps": { "alert": {...}, "badge": 1, "sound": "default" } }

    Optional headers:
        apns-push-type: alert | background | voip | ...
        apns-priority: "5" | "10"
        apns-topic: bundle ID
        apns-collapse-id: collapse identifier
        apns-expiration: unix timestamp
    """
    payload = _ensure_string(body)
    result: dict[str, Any] = {
        "platform": "apple",
        "contentType": JSON_CONTENT_TYPE,
        "body": payload,
    }
    if headers:
        result["headers"] = headers
    return result


def create_apple_body(
    alert: str | dict | None = None,
    badge: int | None = None,
    sound: str | dict | None = "default",
    category: str | None = None,
    thread_id: str | None = None,
    content_available: int | None = None,
    mutable_content: int | None = None,
    interruption_level: str | None = None,
    relevance_score: float | None = None,
    custom: dict | None = None,
) -> str:
    """Build an Apple APNs native message body."""
    aps: dict[str, Any] = {}

    if alert is not None:
        aps["alert"] = alert
    if badge is not None:
        aps["badge"] = badge
    if sound is not None:
        aps["sound"] = sound
    if category is not None:
        aps["category"] = category
    if thread_id is not None:
        aps["thread-id"] = thread_id
    if content_available is not None:
        aps["content-available"] = content_available
    if mutable_content is not None:
        aps["mutable-content"] = mutable_content
    if interruption_level is not None:
        aps["interruption-level"] = interruption_level
    if relevance_score is not None:
        aps["relevance-score"] = relevance_score

    message: dict[str, Any] = {"aps": aps}
    if custom:
        message.update(custom)

    return json.dumps(message)


# ─── FCM Legacy (GCM) ───────────────────────────────────────────


def create_fcm_legacy_notification(
    body: dict | str,
    headers: dict[str, str] | None = None,
) -> dict:
    """Create an FCM Legacy (GCM) notification."""
    payload = _ensure_string(body)
    result: dict[str, Any] = {
        "platform": "gcm",
        "contentType": JSON_CONTENT_TYPE,
        "body": payload,
    }
    if headers:
        result["headers"] = headers
    return result


# Alias
create_gcm_notification = create_fcm_legacy_notification


def create_fcm_legacy_body(
    to: str | None = None,
    registration_ids: list[str] | None = None,
    condition: str | None = None,
    collapse_key: str | None = None,
    priority: str = "high",
    time_to_live: int | None = None,
    restricted_package_name: str | None = None,
    dry_run: bool = False,
    data: dict | None = None,
    notification: dict | None = None,
) -> str:
    """Build an FCM Legacy native message body."""
    message: dict[str, Any] = {"priority": priority, "dry_run": dry_run}

    if to:
        message["to"] = to
    if registration_ids:
        message["registration_ids"] = registration_ids
    if condition:
        message["condition"] = condition
    if collapse_key:
        message["collapse_key"] = collapse_key
    if time_to_live is not None:
        message["time_to_live"] = time_to_live
    if restricted_package_name:
        message["restricted_package_name"] = restricted_package_name
    if data:
        message["data"] = data
    if notification:
        message["notification"] = notification

    return json.dumps(message)


# ─── FCM V1 ──────────────────────────────────────────────────────


def create_fcm_v1_notification(
    body: dict | str,
    headers: dict[str, str] | None = None,
) -> dict:
    """Create an FCM V1 notification."""
    payload = _ensure_string(body)
    result: dict[str, Any] = {
        "platform": "fcmv1",
        "contentType": JSON_CONTENT_TYPE,
        "body": payload,
    }
    if headers:
        result["headers"] = headers
    return result


def create_fcm_v1_body(
    notification: dict | None = None,
    data: dict | None = None,
    android: dict | None = None,
    webpush: dict | None = None,
    apns: dict | None = None,
    token: str | None = None,
    topic: str | None = None,
    condition: str | None = None,
) -> str:
    """Build an FCM V1 native message body."""
    message: dict[str, Any] = {}

    if notification:
        message["notification"] = notification
    if data:
        message["data"] = data
    if android:
        message["android"] = android
    if webpush:
        message["webpush"] = webpush
    if apns:
        message["apns"] = apns
    if token:
        message["token"] = token
    if topic:
        message["topic"] = topic
    if condition:
        message["condition"] = condition

    return json.dumps(message)


# ─── Windows (WNS) ───────────────────────────────────────────────


def create_windows_toast_notification(
    body: str,
    headers: dict[str, str] | None = None,
) -> dict:
    """Create a Windows Toast notification (WNS)."""
    result: dict[str, Any] = {
        "platform": "windows",
        "contentType": XML_CONTENT_TYPE,
        "body": body,
        "headers": headers or {},
    }
    result["headers"].setdefault("X-WNS-Type", "wns/toast")
    return result


def create_windows_tile_notification(
    body: str,
    headers: dict[str, str] | None = None,
) -> dict:
    """Create a Windows Tile notification (WNS)."""
    result: dict[str, Any] = {
        "platform": "windows",
        "contentType": XML_CONTENT_TYPE,
        "body": body,
        "headers": headers or {},
    }
    result["headers"].setdefault("X-WNS-Type", "wns/tile")
    return result


def create_windows_badge_notification(
    body: str,
    headers: dict[str, str] | None = None,
) -> dict:
    """Create a Windows Badge notification (WNS)."""
    result: dict[str, Any] = {
        "platform": "windows",
        "contentType": XML_CONTENT_TYPE,
        "body": body,
        "headers": headers or {},
    }
    result["headers"].setdefault("X-WNS-Type", "wns/badge")
    return result


def create_windows_raw_notification(
    body: str,
    headers: dict[str, str] | None = None,
) -> dict:
    """Create a Windows Raw notification (WNS)."""
    result: dict[str, Any] = {
        "platform": "windows",
        "contentType": STREAM_CONTENT_TYPE,
        "body": body,
        "headers": headers or {},
    }
    result["headers"].setdefault("X-WNS-Type", "wns/raw")
    return result


def create_windows_notification(
    body: str,
    wns_type: str = "wns/toast",
    headers: dict[str, str] | None = None,
) -> dict:
    """
    Generic Windows notification factory.

    wns_type: wns/toast | wns/tile | wns/badge | wns/raw
    """
    factories = {
        "wns/toast": create_windows_toast_notification,
        "wns/tile": create_windows_tile_notification,
        "wns/badge": create_windows_badge_notification,
        "wns/raw": create_windows_raw_notification,
    }
    factory = factories.get(wns_type)
    if not factory:
        raise ValueError(f"Invalid WNS type: {wns_type}. Use: {', '.join(factories)}")
    return factory(body, headers)


def create_windows_toast_body(
    text: str,
    launch: str | None = None,
    duration: str | None = None,
    scenario: str | None = None,
) -> str:
    """Build a Windows Toast XML body."""
    toast_attrs = {}
    if launch:
        toast_attrs["launch"] = launch
    if duration:
        toast_attrs["duration"] = duration
    if scenario:
        toast_attrs["scenario"] = scenario

    attrs = " ".join(f'{k}="{v}"' for k, v in toast_attrs.items())
    return f'<toast {attrs}><visual><binding template="ToastText01"><text id="1">{text}</text></binding></visual></toast>'


# ─── ADM (Amazon Device Messaging) ──────────────────────────────


def create_adm_notification(
    body: dict | str,
    headers: dict[str, str] | None = None,
) -> dict:
    """Create an ADM (Amazon) notification."""
    payload = _ensure_string(body)
    result: dict[str, Any] = {
        "platform": "adm",
        "contentType": JSON_CONTENT_TYPE,
        "body": payload,
    }
    if headers:
        result["headers"] = headers
    return result


def create_adm_body(
    data: dict | None = None,
    notification: dict | None = None,
    consolidation_key: str | None = None,
    expires_after: int | None = None,
    priority: str = "normal",
) -> str:
    """Build an ADM native message body."""
    message: dict[str, Any] = {"priority": priority}

    if data:
        message["data"] = data
    if notification:
        message["notification"] = notification
    if consolidation_key:
        message["consolidationKey"] = consolidation_key
    if expires_after is not None:
        message["expiresAfter"] = expires_after

    return json.dumps(message)


# ─── Baidu ───────────────────────────────────────────────────────


def create_baidu_notification(
    body: dict | str,
    headers: dict[str, str] | None = None,
) -> dict:
    """Create a Baidu Push notification."""
    payload = _ensure_string(body)
    result: dict[str, Any] = {
        "platform": "baidu",
        "contentType": JSON_CONTENT_TYPE,
        "body": payload,
    }
    if headers:
        result["headers"] = headers
    return result


def create_baidu_body(
    title: str | None = None,
    description: str | None = None,
    notification_builder_id: int = 0,
    notification_basic_style: int = 0,
    open_type: int = 1,
    custom_content: dict | None = None,
    url: str | None = None,
) -> str:
    """Build a Baidu native message body."""
    message: dict[str, Any] = {
        "notification_builder_id": notification_builder_id,
        "notification_basic_style": notification_basic_style,
        "open_type": open_type,
    }

    if title:
        message["title"] = title
    if description:
        message["description"] = description
    if url:
        message["url"] = url
    if custom_content:
        message["custom_content"] = custom_content

    return json.dumps(message)


# ─── Browser (Web Push) ──────────────────────────────────────────


def create_browser_notification(
    body: dict | str,
    headers: dict[str, str] | None = None,
) -> dict:
    """Create a Browser Web Push notification."""
    payload = _ensure_string(body)
    result: dict[str, Any] = {
        "platform": "browser",
        "contentType": JSON_CONTENT_TYPE,
        "body": payload,
    }
    if headers:
        result["headers"] = headers
    return result


# ─── Template ────────────────────────────────────────────────────


def create_template_notification(
    body: dict | str,
    headers: dict[str, str] | None = None,
) -> dict:
    """
    Create a Template notification (cross-platform).

    Template registrations define the platform-specific template.
    The body contains the data to fill template variables.
    Example body: { "message": "Hello", "badge": 1, "sound": "default" }
    """
    payload = _ensure_string(body)
    result: dict[str, Any] = {
        "platform": "template",
        "contentType": JSON_CONTENT_TYPE,
        "body": payload,
    }
    if headers:
        result["headers"] = headers
    return result


# ─── Xiaomi ──────────────────────────────────────────────────────


def create_xiaomi_notification(
    body: dict | str,
    headers: dict[str, str] | None = None,
) -> dict:
    """Create a Xiaomi Push notification."""
    payload = _ensure_string(body)
    result: dict[str, Any] = {
        "platform": "xiaomi",
        "contentType": JSON_CONTENT_TYPE,
        "body": payload,
    }
    if headers:
        result["headers"] = headers
    return result


# ─── Helpers ─────────────────────────────────────────────────────


def _ensure_string(body: dict | str) -> str:
    """Convert dict to JSON string, pass through if already string."""
    if isinstance(body, str):
        return body
    return json.dumps(body)
