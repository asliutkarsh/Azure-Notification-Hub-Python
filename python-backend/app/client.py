"""
Azure Notification Hubs REST API client.
Python port of @azure/notification-hubs JS SDK.
"""

import json
import logging
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

import httpx

from .auth import create_sas_token, parse_connection_string
from .notifications import JSON_CONTENT_TYPE

logger = logging.getLogger("nh.client")

API_VERSION = "2020-06"


class NotificationHubsClient:
    def __init__(self, connection_string: str, hub_name: str):
        parsed = parse_connection_string(connection_string)
        self._hub_name = hub_name
        self._endpoint = parsed["endpoint"].replace("sb://", "https://")
        self._shared_access_key = parsed["shared_access_key"]
        self._shared_access_key_name = parsed["shared_access_key_name"]
        self._entity_path = parsed.get("entity_path")
        self._client = httpx.Client(timeout=30)

        logger.info(
            f"Initialized | endpoint={self._endpoint} "
            f"hub={hub_name} entity={self._entity_path} "
            f"key={self._shared_access_key_name}"
        )

    def _base_url(self) -> str:
        base = self._endpoint.rstrip("/")
        hub_path = self._entity_path or self._hub_name
        return f"{base}/{hub_path}"

    def _request_url(self, path: str = "", extra_params: dict | None = None) -> str:
        url = f"{self._base_url()}{path}?api-version={API_VERSION}"
        if extra_params:
            for k, v in extra_params.items():
                url += f"&{k}={v}"
        return url

    def _create_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        token = create_sas_token(
            self._shared_access_key_name,
            self._shared_access_key,
            self._endpoint,
        )
        headers = {
            "Authorization": token,
            "x-ms-version": API_VERSION,
            "x-ms-azsdk-telemetry": "class=NotificationHubsClient;method=python",
            "Content-Type": "application/json;charset=utf-8",
        }
        if extra:
            headers.update(extra)
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        logger.debug(f"Response {response.status_code} | {response.text[:500]}")

        if response.status_code == 410:
            raise SubscriptionGoneError(response.text)

        if response.status_code >= 400:
            raise AzureNHError(response.status_code, response.text)

        if response.status_code == 204 or not response.content:
            return {}

        content_type = response.headers.get("content-type", "")
        if "xml" in content_type:
            return {"_raw_xml": response.text}
        return response.json()

    # ─── Installations ───────────────────────────────────────────

    def create_or_update_installation(self, installation: dict) -> dict:
        installation_id = installation["installationId"]
        url = self._request_url(f"/installations/{installation_id}")
        headers = self._create_headers()
        headers["Content-Type"] = "application/json"
        body = json.dumps(installation)

        logger.info(f"PUT /installations/{installation_id}")
        logger.debug(f"Body: {body}")

        resp = self._client.put(url, content=body, headers=headers)
        return self._handle_response(resp)

    def delete_installation(self, installation_id: str) -> dict:
        url = self._request_url(f"/installations/{installation_id}")
        headers = self._create_headers()

        logger.info(f"DELETE /installations/{installation_id}")
        resp = self._client.delete(url, headers=headers)
        return self._handle_response(resp)

    def get_installation(self, installation_id: str) -> dict:
        url = self._request_url(f"/installations/{installation_id}")
        headers = self._create_headers()

        logger.info(f"GET /installations/{installation_id}")
        resp = self._client.get(url, headers=headers)
        return self._handle_response(resp)

    # ─── Notifications ───────────────────────────────────────────

    def send_notification(
        self,
        notification: dict,
        tag_expression: str | None = None,
        test_send: bool = False,
        ttl: int | None = None,
        urgency: str | None = None,
    ) -> dict:
        url = self._request_url("/messages")
        headers = self._create_headers()

        # Platform format header
        headers["ServiceBusNotification-Format"] = notification.get(
            "platform", "browser"
        )

        # Content type from notification (supports all platforms)
        content_type = notification.get("contentType", JSON_CONTENT_TYPE)
        headers["Content-Type"] = content_type

        # Platform-specific headers (e.g. X-WNS-Type for Windows)
        notif_headers = notification.get("headers", {})
        for k, v in notif_headers.items():
            headers[k] = v

        if tag_expression:
            headers["ServiceBusNotification-Tags"] = tag_expression
        if test_send:
            headers["ServiceBusNotification-TestSend"] = "true"
        if ttl is not None:
            headers["ServiceBusNotification-TimeToLive"] = str(ttl)
        if urgency:
            headers["ServiceBusNotification-Urgency"] = urgency

        body = notification.get("body", "")

        platform = notification.get("platform", "unknown")
        logger.info(
            f"POST /messages | platform={platform} tags={tag_expression} "
            f"ttl={ttl} urgency={urgency}"
        )
        logger.debug(f"Body: {body}")

        resp = self._client.post(url, content=body, headers=headers)
        return self._handle_response(resp)

    def send_broadcast_notification(
        self,
        notification: dict,
        test_send: bool = False,
        ttl: int | None = None,
        urgency: str | None = None,
    ) -> dict:
        return self.send_notification(
            notification,
            tag_expression=None,
            test_send=test_send,
            ttl=ttl,
            urgency=urgency,
        )

    # ─── Scheduled Notifications (Standard SKU) ──────────────────

    def schedule_notification(
        self,
        scheduled_time: datetime,
        notification: dict,
        tag_expression: str | None = None,
    ) -> dict:
        url = self._request_url("/schedulednotifications")
        headers = self._create_headers()
        headers["ServiceBusNotification-Format"] = notification.get(
            "platform", "browser"
        )
        headers["Content-Type"] = notification.get("contentType", JSON_CONTENT_TYPE)
        headers["ServiceBusNotification-ScheduleTime"] = scheduled_time.isoformat()

        # Platform-specific headers
        for k, v in notification.get("headers", {}).items():
            headers[k] = v

        if tag_expression:
            headers["ServiceBusNotification-Tags"] = tag_expression

        body = notification.get("body", "")

        logger.info(
            f"POST /schedulednotifications | at={scheduled_time} tags={tag_expression}"
        )

        resp = self._client.post(url, content=body, headers=headers)
        return self._handle_response(resp)

    def schedule_broadcast_notification(
        self,
        scheduled_time: datetime,
        notification: dict,
    ) -> dict:
        return self.schedule_notification(scheduled_time, notification)

    def cancel_scheduled_notification(self, notification_id: str) -> dict:
        url = self._request_url(f"/schedulednotifications/{notification_id}")
        headers = self._create_headers()

        logger.info(f"DELETE /schedulednotifications/{notification_id}")
        resp = self._client.delete(url, headers=headers)
        return self._handle_response(resp)

    # ─── Analytics ───────────────────────────────────────────────

    def get_notification_outcome_details(self, notification_id: str) -> dict:
        url = self._request_url(f"/messages/{notification_id}")
        headers = self._create_headers()

        logger.info(f"GET /messages/{notification_id}")
        resp = self._client.get(url, headers=headers)
        return self._handle_response(resp)

    def get_feedback_container_url(self) -> str:
        url = self._request_url("/feedbackcontainer")
        headers = self._create_headers()

        logger.info("GET /feedbackcontainer")
        resp = self._client.get(url, headers=headers)
        data = self._handle_response(resp)
        return data.get("url", "")

    # ─── Registrations ───────────────────────────────────────────

    def list_registrations(self, top: int = 100) -> list[dict]:
        url = self._request_url("/registrations", extra_params={"$top": top})
        headers = self._create_headers()

        logger.info(f"GET /registrations")
        resp = self._client.get(url, headers=headers)

        if resp.status_code >= 400:
            raise AzureNHError(resp.status_code, resp.text)

        return self._parse_atom_entries(resp.text)

    def get_registration(self, registration_id: str) -> dict:
        url = self._request_url(f"/registrations/{registration_id}")
        headers = self._create_headers()

        logger.info(f"GET /registrations/{registration_id}")
        resp = self._client.get(url, headers=headers)

        if resp.status_code >= 400:
            raise AzureNHError(resp.status_code, resp.text)

        return self._parse_atom_entry(resp.text)

    def delete_registration(self, registration_id: str) -> dict:
        url = self._request_url(f"/registrations/{registration_id}")
        headers = self._create_headers()

        logger.info(f"DELETE /registrations/{registration_id}")
        resp = self._client.delete(url, headers=headers)
        return self._handle_response(resp)

    # ─── Helpers ─────────────────────────────────────────────────

    def _parse_atom_entries(self, xml_text: str) -> list[dict]:
        """Parse Atom feed XML into a list of dicts."""
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
            "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
        }

        root = ET.fromstring(xml_text)
        entries = []

        for entry in root.findall("atom:entry", ns):
            entries.append(self._extract_entry(entry, ns))

        return entries

    def _parse_atom_entry(self, xml_text: str) -> dict:
        """Parse a single Atom entry."""
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
            "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
        }

        root = ET.fromstring(xml_text)
        return self._extract_entry(root, ns)

    def _extract_entry(self, entry, ns: dict) -> dict:
        """Extract fields from an Atom entry into a dict."""
        result = {}

        # Basic fields
        title_el = entry.find("atom:title", ns)
        if title_el is not None and title_el.text:
            result["title"] = title_el.text

        updated_el = entry.find("atom:updated", ns)
        if updated_el is not None and updated_el.text:
            result["updated"] = updated_el.text

        # ETag from attribute
        etag = entry.get(
            "{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}etag"
        )
        if etag:
            result["etag"] = etag

        # Content properties — try both m:properties and direct children
        # (Azure NH uses direct children in servicebus/connect namespace)
        content = entry.find("atom:content", ns)
        if content is not None:
            # Try m:properties first (some endpoints use this)
            properties = content.find("m:properties", ns)
            if properties is not None:
                for prop in properties:
                    tag = prop.tag.split("}")[-1] if "}" in prop.tag else prop.tag
                    value = prop.text
                    result[tag] = value
            else:
                # Azure NH uses direct child elements inside content
                # (e.g. BrowserRegistrationDescription with namespace
                # http://schemas.microsoft.com/netservices/2010/10/servicebus/connect)
                for child in content:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if tag.endswith("RegistrationDescription") or tag.endswith(
                        "Installation"
                    ):
                        # Process all children of the description element
                        for prop in child:
                            prop_tag = (
                                prop.tag.split("}")[-1] if "}" in prop.tag else prop.tag
                            )
                            value = prop.text
                            # Parse Tags as comma-separated list
                            if prop_tag == "Tags" and value:
                                value = [t.strip() for t in value.split(",")]
                            result[prop_tag] = value
                    elif tag not in ("title", "content"):
                        result[tag] = child.text

        # RegistrationId from id element
        id_el = entry.find("atom:id", ns)
        if id_el is not None and id_el.text:
            result["id"] = id_el.text

        return result

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ─── Exceptions ──────────────────────────────────────────────────


class AzureNHError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Azure NH error {status_code}: {body}")


class SubscriptionGoneError(AzureNHError):
    def __init__(self, body: str):
        super().__init__(410, body)


# ─── Factory functions ───────────────────────────────────────────


def create_browser_installation(
    installation_id: str,
    push_channel: dict,
    tags: list[str] | None = None,
    expiration_time: str | None = None,
) -> dict:
    installation: dict[str, Any] = {
        "installationId": installation_id,
        "platform": "browser",
        "pushChannel": push_channel,
    }
    if tags:
        installation["tags"] = tags
    if expiration_time:
        installation["expirationTime"] = expiration_time
    return installation


def create_browser_notification(body: str) -> dict:
    return {"platform": "browser", "body": body}
