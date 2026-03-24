self.addEventListener("push", (event) => {
  const data = event.data?.json() || {};

  const options = {
    body: data.body || "",
    data: { url: data.url || "/" },
  };

  if (data.icon) options.icon = data.icon;
  if (data.badge) options.badge = data.badge;
  if (data.image) options.image = data.image;
  if (data.tag) options.tag = data.tag;
  if (data.actions) options.actions = data.actions;
  if (data.silent) options.silent = true;
  if (data.requireInteraction) options.requireInteraction = true;

  event.waitUntil(
    self.registration.showNotification(data.title || "Notification", options)
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil(clients.openWindow(url));
});
