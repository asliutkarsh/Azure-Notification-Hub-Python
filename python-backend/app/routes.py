import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .client import (
    AzureNHError,
    NotificationHubsClient,
    SubscriptionGoneError,
    create_browser_installation,
)
from .config import settings
from .notifications import (
    create_adm_body,
    create_adm_notification,
    create_apple_body,
    create_apple_notification,
    create_baidu_body,
    create_baidu_notification,
    create_browser_notification,
    create_fcm_legacy_body,
    create_fcm_legacy_notification,
    create_fcm_v1_body,
    create_fcm_v1_notification,
    create_template_notification,
    create_windows_badge_notification,
    create_windows_notification,
    create_windows_raw_notification,
    create_windows_tile_notification,
    create_windows_toast_body,
    create_windows_toast_notification,
    create_xiaomi_notification,
)

logger = logging.getLogger("nh.routes")

router = APIRouter(prefix="/api")

_client: NotificationHubsClient | None = None


def get_client() -> NotificationHubsClient:
    global _client
    if _client is None:
        logger.info(f"Creating NH client | hub={settings.azure_notification_hub_name}")
        _client = NotificationHubsClient(
            settings.azure_notification_hub_connection_string,
            settings.azure_notification_hub_name,
        )
    return _client


# ─── Models ──────────────────────────────────────────────────────


class SubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class SaveSubscriptionRequest(BaseModel):
    endpoint: str
    keys: SubscriptionKeys
    userId: str | None = None


class SendBasicRequest(BaseModel):
    userId: str = "anonymous"
    title: str
    body: str
    url: str | None = None


class SendRichRequest(BaseModel):
    userId: str = "anonymous"
    title: str
    body: str
    icon: str | None = None
    image: str | None = None
    badge: str | None = None
    url: str | None = None
    actions: list[dict] | None = None
    tag: str | None = None
    silent: bool = False
    requireInteraction: bool = False


class SendTargetedRequest(BaseModel):
    tagExpression: str
    title: str
    body: str
    url: str | None = None
    ttl: int | None = None
    urgency: str | None = None


class BroadcastRequest(BaseModel):
    title: str
    body: str
    url: str | None = None
    ttl: int | None = None
    urgency: str | None = None


class ScheduledRequest(BaseModel):
    userId: str = "anonymous"
    title: str
    body: str
    url: str | None = None
    scheduledTime: str


class UnsubscribeRequest(BaseModel):
    installationId: str


# ─── Core Routes ─────────────────────────────────────────────────


@router.get("/vapid-public-key")
def vapid_public_key():
    logger.info("Serving VAPID public key")
    return {"publicKey": settings.vapid_public_key}


@router.post("/save-subscription")
def save_subscription(req: SaveSubscriptionRequest):
    installation_id = str(uuid.uuid4())
    user_id = req.userId or "anonymous"

    logger.info(f"Save subscription | user={user_id} id={installation_id}")

    try:
        installation = create_browser_installation(
            installation_id=installation_id,
            push_channel={
                "endpoint": req.endpoint,
                "p256dh": req.keys.p256dh,
                "auth": req.keys.auth,
            },
            tags=[f"user:{user_id}", "all", "web"],
            expiration_time=(
                datetime.now(timezone.utc) + timedelta(days=30)
            ).isoformat(),
        )

        client = get_client()
        client.create_or_update_installation(installation)

        logger.info(f"Installation saved | id={installation_id}")
        return {"status": "saved", "installationId": installation_id, "userId": user_id}

    except Exception as e:
        logger.error(f"Save subscription failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/unsubscribe")
def unsubscribe(req: UnsubscribeRequest):
    logger.info(f"Unsubscribe | id={req.installationId}")

    try:
        client = get_client()
        client.delete_installation(req.installationId)
        logger.info(f"Unsubscribed | id={req.installationId}")
        return {"status": "unsubscribed"}

    except Exception as e:
        logger.error(f"Unsubscribe failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Send Notification Scenarios ─────────────────────────────────


@router.post("/send")
def send_basic(req: SendBasicRequest):
    """2.1 — Send basic notification to a specific user."""
    logger.info(f"Send basic | user={req.userId} title={req.title!r}")

    try:
        payload = {"title": req.title, "body": req.body}
        if req.url:
            payload["url"] = req.url

        notification = create_browser_notification(body=json.dumps(payload))
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=f"user:{req.userId}"
        )

        logger.info(f"Sent | result={result}")
        return {"status": "sent", "result": result}

    except SubscriptionGoneError:
        logger.warning(f"Subscription gone for user={req.userId}")
        return {"status": "gone", "error": "Subscription expired (410)"}
    except AzureNHError as e:
        logger.error(f"Send failed: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/rich")
def send_rich(req: SendRichRequest):
    """3.1–3.6 — Send rich notification with icon, image, actions, etc."""
    logger.info(f"Send rich | user={req.userId} title={req.title!r}")

    try:
        payload = {"title": req.title, "body": req.body}

        if req.icon:
            payload["icon"] = req.icon
        if req.image:
            payload["image"] = req.image
        if req.badge:
            payload["badge"] = req.badge
        if req.url:
            payload["url"] = req.url
        if req.actions:
            payload["actions"] = req.actions
        if req.tag:
            payload["tag"] = req.tag
        if req.silent:
            payload["silent"] = True
        if req.requireInteraction:
            payload["requireInteraction"] = True

        notification = create_browser_notification(body=json.dumps(payload))
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=f"user:{req.userId}"
        )

        logger.info(f"Rich sent | result={result}")
        return {"status": "sent", "result": result, "payload": payload}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Rich send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/targeted")
def send_targeted(req: SendTargetedRequest):
    """2.2, 2.3, 4.3, 4.4 — Send with tag expression, TTL, urgency."""
    logger.info(
        f"Send targeted | tags={req.tagExpression} ttl={req.ttl} urgency={req.urgency}"
    )

    try:
        payload = {"title": req.title, "body": req.body}
        if req.url:
            payload["url"] = req.url

        notification = create_browser_notification(body=json.dumps(payload))
        client = get_client()
        result = client.send_notification(
            notification,
            tag_expression=req.tagExpression,
            ttl=req.ttl,
            urgency=req.urgency,
        )

        logger.info(f"Targeted sent | result={result}")
        return {"status": "sent", "result": result}

    except SubscriptionGoneError:
        return {"status": "gone", "error": "Subscription expired (410)"}
    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Targeted send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast")
def broadcast(req: BroadcastRequest):
    """2.3 — Send to ALL subscribers."""
    logger.info(f"Broadcast | title={req.title!r}")

    try:
        payload = {"title": req.title, "body": req.body}
        if req.url:
            payload["url"] = req.url

        notification = create_browser_notification(body=json.dumps(payload))
        client = get_client()
        result = client.send_broadcast_notification(
            notification,
            ttl=req.ttl,
            urgency=req.urgency,
        )

        logger.info(f"Broadcast sent | result={result}")
        return {"status": "sent", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Broadcast failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/scheduled")
def send_scheduled(req: ScheduledRequest):
    """7.1 — Schedule notification for future delivery."""
    logger.info(f"Schedule | user={req.userId} at={req.scheduledTime}")

    try:
        scheduled_time = datetime.fromisoformat(req.scheduledTime)
        payload = {"title": req.title, "body": req.body}
        if req.url:
            payload["url"] = req.url

        notification = create_browser_notification(body=json.dumps(payload))
        client = get_client()
        result = client.schedule_notification(
            scheduled_time,
            notification,
            tag_expression=f"user:{req.userId}",
        )

        logger.info(f"Scheduled | result={result}")
        return {"status": "scheduled", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Schedule failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/scheduled/{notification_id}")
def cancel_scheduled(notification_id: str):
    """7.2 — Cancel a scheduled notification."""
    logger.info(f"Cancel scheduled | id={notification_id}")

    try:
        client = get_client()
        result = client.cancel_scheduled_notification(notification_id)
        return {"status": "cancelled", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Cancel scheduled failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Platform-Specific Routes ────────────────────────────────────


class PlatformSendRequest(BaseModel):
    """Generic request for platform-specific sends."""

    tagExpression: str | None = None
    payload: dict  # Platform-native message body
    headers: dict | None = None  # Platform-specific headers
    ttl: int | None = None
    urgency: str | None = None


# ─── Apple (APNs) ────────────────────────────────────────────────


class AppleSendRequest(BaseModel):
    tagExpression: str | None = None
    alert: str | dict | None = None
    badge: int | None = None
    sound: str | dict | None = "default"
    category: str | None = None
    thread_id: str | None = None
    content_available: int | None = None
    mutable_content: int | None = None
    interruption_level: str | None = None
    custom: dict | None = None
    headers: dict | None = None


@router.post("/send/apple")
def send_apple(req: AppleSendRequest):
    """Send Apple Push Notification (APNs)."""
    logger.info(f"Send Apple | tags={req.tagExpression}")

    try:
        body = create_apple_body(
            alert=req.alert,
            badge=req.badge,
            sound=req.sound,
            category=req.category,
            thread_id=req.thread_id,
            content_available=req.content_available,
            mutable_content=req.mutable_content,
            interruption_level=req.interruption_level,
            custom=req.custom,
        )
        notification = create_apple_notification(body=body, headers=req.headers)
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=req.tagExpression
        )
        return {"status": "sent", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Apple send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── FCM Legacy (GCM) ───────────────────────────────────────────


class FcmLegacySendRequest(BaseModel):
    tagExpression: str | None = None
    to: str | None = None
    collapse_key: str | None = None
    priority: str = "high"
    time_to_live: int | None = None
    data: dict | None = None
    notification: dict | None = None


@router.post("/send/gcm")
def send_gcm(req: FcmLegacySendRequest):
    """Send FCM Legacy (GCM) notification."""
    logger.info(f"Send GCM | tags={req.tagExpression}")

    try:
        body = create_fcm_legacy_body(
            to=req.to,
            collapse_key=req.collapse_key,
            priority=req.priority,
            time_to_live=req.time_to_live,
            data=req.data,
            notification=req.notification,
        )
        notification = create_fcm_legacy_notification(body=body)
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=req.tagExpression
        )
        return {"status": "sent", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"GCM send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── FCM V1 ──────────────────────────────────────────────────────


class FcmV1SendRequest(BaseModel):
    tagExpression: str | None = None
    notification: dict | None = None
    data: dict | None = None
    android: dict | None = None
    webpush: dict | None = None
    apns: dict | None = None
    token: str | None = None
    topic: str | None = None
    condition: str | None = None


@router.post("/send/fcmv1")
def send_fcmv1(req: FcmV1SendRequest):
    """Send FCM V1 notification."""
    logger.info(f"Send FCM V1 | tags={req.tagExpression}")

    try:
        body = create_fcm_v1_body(
            notification=req.notification,
            data=req.data,
            android=req.android,
            webpush=req.webpush,
            apns=req.apns,
            token=req.token,
            topic=req.topic,
            condition=req.condition,
        )
        notification = create_fcm_v1_notification(body=body)
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=req.tagExpression
        )
        return {"status": "sent", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"FCM V1 send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Windows (WNS) ───────────────────────────────────────────────


class WindowsSendRequest(BaseModel):
    tagExpression: str | None = None
    wns_type: str = "wns/toast"  # wns/toast | wns/tile | wns/badge | wns/raw
    body: str  # XML body
    headers: dict | None = None


@router.post("/send/windows")
def send_windows(req: WindowsSendRequest):
    """Send Windows Notification (WNS). Supports toast, tile, badge, raw."""
    logger.info(f"Send Windows | type={req.wns_type} tags={req.tagExpression}")

    try:
        notification = create_windows_notification(
            body=req.body,
            wns_type=req.wns_type,
            headers=req.headers,
        )
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=req.tagExpression
        )
        return {"status": "sent", "result": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Windows send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class WindowsToastRequest(BaseModel):
    tagExpression: str | None = None
    text: str
    launch: str | None = None
    duration: str | None = None


@router.post("/send/windows/toast")
def send_windows_toast(req: WindowsToastRequest):
    """Send Windows Toast notification with auto-generated XML."""
    logger.info(f"Send Windows Toast | tags={req.tagExpression}")

    try:
        body = create_windows_toast_body(
            text=req.text,
            launch=req.launch,
            duration=req.duration,
        )
        notification = create_windows_toast_notification(body=body)
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=req.tagExpression
        )
        return {"status": "sent", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Windows toast send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── ADM (Amazon) ────────────────────────────────────────────────


class AdmSendRequest(BaseModel):
    tagExpression: str | None = None
    data: dict | None = None
    notification: dict | None = None
    consolidation_key: str | None = None
    expires_after: int | None = None
    priority: str = "normal"


@router.post("/send/adm")
def send_adm(req: AdmSendRequest):
    """Send ADM (Amazon Device Messaging) notification."""
    logger.info(f"Send ADM | tags={req.tagExpression}")

    try:
        body = create_adm_body(
            data=req.data,
            notification=req.notification,
            consolidation_key=req.consolidation_key,
            expires_after=req.expires_after,
            priority=req.priority,
        )
        notification = create_adm_notification(body=body)
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=req.tagExpression
        )
        return {"status": "sent", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"ADM send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Baidu ───────────────────────────────────────────────────────


class BaiduSendRequest(BaseModel):
    tagExpression: str | None = None
    title: str | None = None
    description: str | None = None
    notification_builder_id: int = 0
    notification_basic_style: int = 0
    open_type: int = 1
    url: str | None = None
    custom_content: dict | None = None


@router.post("/send/baidu")
def send_baidu(req: BaiduSendRequest):
    """Send Baidu Push notification."""
    logger.info(f"Send Baidu | tags={req.tagExpression}")

    try:
        body = create_baidu_body(
            title=req.title,
            description=req.description,
            notification_builder_id=req.notification_builder_id,
            notification_basic_style=req.notification_basic_style,
            open_type=req.open_type,
            url=req.url,
            custom_content=req.custom_content,
        )
        notification = create_baidu_notification(body=body)
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=req.tagExpression
        )
        return {"status": "sent", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Baidu send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Template ────────────────────────────────────────────────────


class TemplateSendRequest(BaseModel):
    """Template notification — payload fills template variables."""

    tagExpression: str | None = None
    data: dict  # Key-value pairs matching template placeholders


@router.post("/send/template")
def send_template(req: TemplateSendRequest):
    """Send Template notification (cross-platform).

    Template registrations define platform-specific templates.
    The data dict fills template variables like {message}, {badge}, etc.
    """
    logger.info(f"Send Template | tags={req.tagExpression} data={req.data}")

    try:
        notification = create_template_notification(body=req.data)
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=req.tagExpression
        )
        return {"status": "sent", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Template send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Xiaomi ──────────────────────────────────────────────────────


class XiaomiSendRequest(BaseModel):
    tagExpression: str | None = None
    payload: dict


@router.post("/send/xiaomi")
def send_xiaomi(req: XiaomiSendRequest):
    """Send Xiaomi Push notification."""
    logger.info(f"Send Xiaomi | tags={req.tagExpression}")

    try:
        notification = create_xiaomi_notification(body=req.payload)
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=req.tagExpression
        )
        return {"status": "sent", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Xiaomi send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Generic Platform Send ───────────────────────────────────────


PLATFORM_CREATORS = {
    "apple": create_apple_notification,
    "gcm": create_fcm_legacy_notification,
    "fcmv1": create_fcm_v1_notification,
    "browser": create_browser_notification,
    "adm": create_adm_notification,
    "baidu": create_baidu_notification,
    "template": create_template_notification,
    "xiaomi": create_xiaomi_notification,
    "windows": create_windows_notification,
}


@router.post("/send/platform/{platform}")
def send_platform(platform: str, req: PlatformSendRequest):
    """Generic platform send — specify platform in URL path."""
    logger.info(f"Send {platform} | tags={req.tagExpression}")

    if platform not in PLATFORM_CREATORS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown platform: {platform}. Supported: {', '.join(PLATFORM_CREATORS)}",
        )

    try:
        creator = PLATFORM_CREATORS[platform]
        notification = creator(body=req.payload, headers=req.headers)
        client = get_client()
        result = client.send_notification(
            notification, tag_expression=req.tagExpression
        )
        return {"status": "sent", "result": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"{platform} send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Analytics & Debug ───────────────────────────────────────────


@router.get("/registrations")
def list_registrations():
    """List all registrations (debug)."""
    try:
        client = get_client()
        regs = client.list_registrations()
        logger.info(f"Found {len(regs)} registrations")
        return {"registrations": regs}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"List registrations failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/installations/{installation_id}")
def get_installation(installation_id: str):
    """Get a specific installation."""
    try:
        client = get_client()
        inst = client.get_installation(installation_id)
        return {"installation": inst}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Get installation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outcome/{notification_id}")
def get_outcome(notification_id: str):
    """5.1 — Get delivery outcome for a sent notification."""
    try:
        client = get_client()
        result = client.get_notification_outcome_details(notification_id)
        return {"outcome": result}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Get outcome failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback")
def get_feedback_url():
    """5.2 — Get PNS feedback container URL."""
    try:
        client = get_client()
        url = client.get_feedback_container_url()
        return {"url": url}

    except AzureNHError as e:
        raise HTTPException(status_code=e.status_code, detail=e.body)
    except Exception as e:
        logger.error(f"Get feedback failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
