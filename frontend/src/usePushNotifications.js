import { useState, useEffect, useCallback } from "react";

const API_BASE = "http://localhost:8000/api";

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

async function api(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${API_BASE}${path}`, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.error || `Request failed: ${res.status}`);
  return data;
}

export function usePushNotifications() {
  const [permission, setPermission] = useState(
    typeof Notification !== "undefined" ? Notification.permission : "default"
  );
  const [subscribed, setSubscribed] = useState(false);
  const [installationId, setInstallationId] = useState(
    () => localStorage.getItem("push_installation_id")
  );
  const [userId, setUserId] = useState(
    () => localStorage.getItem("push_user_id") || null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [logs, setLogs] = useState([]);

  const log = useCallback((msg, type = "info") => {
    console.log("[Push]", msg);
    setLogs((prev) => [
      ...prev,
      { time: new Date().toLocaleTimeString(), msg, type },
    ]);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const reg = await navigator.serviceWorker.ready;
        const sub = await reg.pushManager.getSubscription();
        setSubscribed(!!sub);
        log(`Existing subscription: ${sub ? "yes" : "no"}`);
      } catch {
        log("No service worker registered yet");
      }
    })();
  }, [log]);

  const subscribe = useCallback(
    async (asUser) => {
      setLoading(true);
      setError(null);
      const uid = asUser || userId || "anonymous";

      try {
        log(`Registering service worker as ${uid}...`);
        const registration = await navigator.serviceWorker.register("/sw.js");
        await navigator.serviceWorker.ready;
        log("Service worker ready");

        log("Fetching VAPID public key...");
        const { publicKey } = await api("GET", "/vapid-public-key");
        log("Got VAPID public key");

        log("Subscribing to push...");
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(publicKey),
        });
        log("Push subscription created");

        log(`Saving subscription as user:${uid}...`);
        const saveData = await api("POST", "/save-subscription", {
          ...subscription.toJSON(),
          userId: uid,
        });
        log(`Saved: installationId=${saveData.installationId}`);

        localStorage.setItem("push_installation_id", saveData.installationId);
        localStorage.setItem("push_user_id", uid);
        setInstallationId(saveData.installationId);
        setUserId(uid);
        setSubscribed(true);
        setPermission("granted");
      } catch (err) {
        log(`Error: ${err.message}`, "error");
        setError(err.message);
        setSubscribed(false);
      } finally {
        setLoading(false);
      }
    },
    [log, userId]
  );

  const unsubscribe = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();

      if (sub) {
        log("Unsubscribing from backend...");
        await api("DELETE", "/unsubscribe", {
          installationId: installationId || sub.endpoint,
        });
        log("Backend unsubscribed");

        await sub.unsubscribe();
        log("Browser push unsubscribed");
      }

      localStorage.removeItem("push_installation_id");
      localStorage.removeItem("push_user_id");
      setInstallationId(null);
      setUserId(null);
      setSubscribed(false);
    } catch (err) {
      log(`Error: ${err.message}`, "error");
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [log, installationId]);

  // ─── Scenario API calls ─────────────────────────────────────

  const sendBasic = useCallback(
    async ({ userId: uid, title, body, url }) => {
      log(`[Basic] Sending to user:${uid}...`);
      try {
        const data = await api("POST", "/send", { userId: uid, title, body, url });
        log(`[Basic] Sent: ${JSON.stringify(data.result)}`);
        return data;
      } catch (err) {
        log(`[Basic] Error: ${err.message}`, "error");
        throw err;
      }
    },
    [log]
  );

  const sendRich = useCallback(
    async (payload) => {
      log(`[Rich] Sending to user:${payload.userId}...`);
      try {
        const data = await api("POST", "/send/rich", payload);
        log(`[Rich] Sent: ${JSON.stringify(data.result)}`);
        return data;
      } catch (err) {
        log(`[Rich] Error: ${err.message}`, "error");
        throw err;
      }
    },
    [log]
  );

  const sendTargeted = useCallback(
    async ({ tagExpression, title, body, url, ttl, urgency }) => {
      log(`[Targeted] Sending to ${tagExpression}...`);
      try {
        const data = await api("POST", "/send/targeted", {
          tagExpression,
          title,
          body,
          url,
          ttl,
          urgency,
        });
        log(`[Targeted] Sent: ${JSON.stringify(data.result)}`);
        return data;
      } catch (err) {
        log(`[Targeted] Error: ${err.message}`, "error");
        throw err;
      }
    },
    [log]
  );

  const sendBroadcast = useCallback(
    async ({ title, body, url, ttl, urgency }) => {
      log("[Broadcast] Sending to all...");
      try {
        const data = await api("POST", "/broadcast", {
          title,
          body,
          url,
          ttl,
          urgency,
        });
        log(`[Broadcast] Sent: ${JSON.stringify(data.result)}`);
        return data;
      } catch (err) {
        log(`[Broadcast] Error: ${err.message}`, "error");
        throw err;
      }
    },
    [log]
  );

  const sendScheduled = useCallback(
    async ({ userId: uid, title, body, url, scheduledTime }) => {
      log(`[Scheduled] Scheduling for user:${uid} at ${scheduledTime}...`);
      try {
        const data = await api("POST", "/send/scheduled", {
          userId: uid,
          title,
          body,
          url,
          scheduledTime,
        });
        log(`[Scheduled] Scheduled: ${JSON.stringify(data.result)}`);
        return data;
      } catch (err) {
        log(`[Scheduled] Error: ${err.message}`, "error");
        throw err;
      }
    },
    [log]
  );

  const getRegistrations = useCallback(async () => {
    log("[Debug] Fetching registrations...");
    try {
      const data = await api("GET", "/registrations");
      log(`[Debug] Found ${data.registrations.length} registrations`);
      return data.registrations;
    } catch (err) {
      log(`[Debug] Error: ${err.message}`, "error");
      throw err;
    }
  }, [log]);

  return {
    permission,
    subscribed,
    installationId,
    userId,
    loading,
    error,
    logs,
    subscribe,
    unsubscribe,
    sendBasic,
    sendRich,
    sendTargeted,
    sendBroadcast,
    sendScheduled,
    getRegistrations,
    log,
  };
}
