import express from "express";
import config from "./config.js";
import {
  createOrUpdateInstallation,
  sendNotificationToUser,
  sendBroadcastNotification,
  deleteInstallation,
} from "./notificationService.js";

const router = express.Router();

router.post("/save-subscription", async (req, res) => {
  try {
    const subscription = req.body;

    if (!subscription?.endpoint || !subscription?.keys) {
      return res.status(400).json({ error: "Invalid subscription object" });
    }

    // TODO: Replace with auth middleware in production
    const userId = req.body.userId || "anonymous";

    const installationId = await createOrUpdateInstallation(subscription, userId);

    res.json({ status: "saved", installationId });
  } catch (err) {
    console.error("Save subscription error:", err.message, err.statusCode, err.body);
    res.status(err.statusCode || 500).json({ error: err.message || "Failed to save subscription" });
  }
});

router.post("/send", async (req, res) => {
  try {
    const { userId = "anonymous", title, body, url } = req.body;

    if (!title || !body) {
      return res.status(400).json({ error: "title and body are required" });
    }

    const result = await sendNotificationToUser(userId, { title, body, url });

    res.json({ status: "sent", result });
  } catch (err) {
    console.error("Send notification error:", err.message, err.statusCode, err.body);
    res.status(err.statusCode || 500).json({ error: err.message || "Failed to send notification" });
  }
});

router.post("/broadcast", async (req, res) => {
  try {
    const { title, body, url } = req.body;

    if (!title || !body) {
      return res.status(400).json({ error: "title and body are required" });
    }

    const result = await sendBroadcastNotification({ title, body, url });

    res.json({ status: "sent", result });
  } catch (err) {
    console.error("Broadcast error:", err.message, err.statusCode, err.body);
    res.status(err.statusCode || 500).json({ error: err.message || "Failed to broadcast" });
  }
});

router.delete("/unsubscribe", async (req, res) => {
  try {
    const { installationId } = req.body;

    if (!installationId) {
      return res.status(400).json({ error: "installationId is required" });
    }

    await deleteInstallation(installationId);
    res.json({ status: "unsubscribed" });
  } catch (err) {
    console.error("Unsubscribe error:", err.message, err.statusCode, err.body);
    res.status(err.statusCode || 500).json({ error: err.message || "Failed to unsubscribe" });
  }
});

router.get("/vapid-public-key", (_req, res) => {
  res.json({ publicKey: config.vapid.publicKey });
});

export default router;
