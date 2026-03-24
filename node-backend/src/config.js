import "dotenv/config";

export default {
  azure: {
    connectionString: process.env.AZURE_NOTIFICATION_HUB_CONNECTION_STRING,
    hubName: process.env.AZURE_NOTIFICATION_HUB_NAME,
  },
  vapid: {
    publicKey: process.env.VAPID_PUBLIC_KEY,
    privateKey: process.env.VAPID_PRIVATE_KEY,
    subject: process.env.VAPID_SUBJECT,
  },
  server: {
    port: process.env.PORT || 4000,
    frontendUrl: process.env.FRONTEND_URL || "http://localhost:5173",
  },
};
