"""
Azure Notification Hubs SAS token authentication.
Ported from @azure/notification-hubs JS SDK.
"""

import base64
import hashlib
import hmac
import time
from urllib.parse import quote, urlencode


def sign_string(key: str, to_sign: str) -> str:
    """HMAC-SHA256 sign, base64 encode, URL encode."""
    sig = hmac.new(
        key.encode("utf-8"),
        to_sign.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    encoded = base64.b64encode(sig).decode("utf-8")
    return quote(encoded, safe="")


def create_sas_token(
    shared_access_key_name: str,
    shared_access_key: str,
    audience: str,
    expiry: int | None = None,
) -> str:
    """
    Create a SAS token for Azure Notification Hubs.

    Returns: SharedAccessSignature sr=<resource>&sig=<signature>&se=<expiry>&skn=<keyname>
    """
    if expiry is None:
        expiry = int(time.time()) + 3600  # 1 hour

    audience = quote(audience.lower(), safe="")
    key_name = quote(shared_access_key_name, safe="")

    string_to_sign = f"{audience}\n{expiry}"
    sig = sign_string(shared_access_key, string_to_sign)

    return f"SharedAccessSignature sr={audience}&sig={sig}&se={expiry}&skn={key_name}"


def parse_connection_string(connection_string: str) -> dict:
    """
    Parse Azure Service Bus / Notification Hub connection string.

    Returns dict with: endpoint, shared_access_key, shared_access_key_name
    """
    result = {}
    parts = connection_string.strip().split(";")

    for part in parts:
        part = part.strip()
        if not part:
            continue
        eq_idx = part.index("=")
        key = part[:eq_idx].strip()
        value = part[eq_idx + 1 :].strip()
        result[key] = value

    if "Endpoint" not in result:
        raise ValueError("Connection string missing 'Endpoint'")

    if "SharedAccessKey" in result and "SharedAccessKeyName" not in result:
        raise ValueError(
            "Connection string with SharedAccessKey needs SharedAccessKeyName"
        )

    if "SharedAccessKeyName" in result and "SharedAccessKey" not in result:
        raise ValueError(
            "Connection string with SharedAccessKeyName needs SharedAccessKey"
        )

    return {
        "endpoint": result["Endpoint"],
        "shared_access_key": result.get("SharedAccessKey"),
        "shared_access_key_name": result.get("SharedAccessKeyName"),
        "entity_path": result.get("EntityPath"),
    }
