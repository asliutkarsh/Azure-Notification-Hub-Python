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
    create_browser_notification,
)
from .config import settings

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
