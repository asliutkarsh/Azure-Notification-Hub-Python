import { randomUUID } from "node:crypto";
import {
  NotificationHubsClient,
  createBrowserInstallation,
  createBrowserNotification,
} from "@azure/notification-hubs";
import config from "./config.js";

let client = null;

function getClient() {
  if (!client) {
    client = new NotificationHubsClient(
      config.azure.connectionString,
      config.azure.hubName
    );
  }
  return client;
}

export async function createOrUpdateInstallation(subscription, userId) {
  const hub = getClient();
  const installationId = randomUUID();

  const installation = createBrowserInstallation({
    installationId,
    pushChannel: {
      endpoint: subscription.endpoint,
      p256dh: subscription.keys.p256dh,
      auth: subscription.keys.auth,
    },
    tags: [`user:${userId}`, "all", "web"],
    expirationTime: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
  });

  await hub.createOrUpdateInstallation(installation);
  return installationId;
}

export async function sendNotificationToUser(userId, payload) {
  const hub = getClient();

  const notification = createBrowserNotification({
    body: JSON.stringify(payload),
  });

  try {
    return await hub.sendNotification(notification, {
      tagExpression: `user:${userId}`,
    });
  } catch (err) {
    if (err.statusCode === 410) {
      console.log(`Subscription expired for user:${userId}, cleaning up`);
      // Azure auto-cleans expired installations, no action needed
    }
    throw err;
  }
}

export async function sendBroadcastNotification(payload) {
  const hub = getClient();

  const notification = createBrowserNotification({
    body: JSON.stringify(payload),
  });

  return hub.sendBroadcastNotification(notification);
}

export async function deleteInstallation(installationId) {
  const hub = getClient();
  await hub.deleteInstallation(installationId);
}
