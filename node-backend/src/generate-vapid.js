import webpush from "web-push";

const vapidKeys = webpush.generateVAPIDKeys();

console.log("\n=== VAPID Keys ===\n");
console.log("Public Key:", vapidKeys.publicKey);
console.log("Private Key:", vapidKeys.privateKey);
console.log("\nAdd these to your .env file\n");
