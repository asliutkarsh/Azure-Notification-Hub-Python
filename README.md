# Web Push Notifications — Azure Notification Hubs

Full-stack web push notification system with **two backend options** (Node.js / Python) and a **React testing dashboard**.

## Architecture

```
┌─────────────────────┐       ┌─────────────────────┐
│   React Frontend    │       │   React Frontend    │
│   (User A browser)  │       │   (User B browser)  │
└────────┬────────────┘       └────────┬────────────┘
         │ subscription                 │ subscription
         ▼                              ▼
┌─────────────────────────────────────────────────────┐
│              Backend API                            │
│  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │  Node.js (Express)│  │  Python (FastAPI)        │ │
│  │  :4000            │  │  :8001                   │ │
│  └────────┬─────────┘  └────────┬─────────────────┘ │
│           │                     │                    │
│           └─────────┬───────────┘                    │
│                     ▼                                │
│        Azure Notification Hubs                      │
│        (installations + send)                       │
│                     │                                │
│                     ▼                                │
│              Browser Push (FCM/APNs)                │
│                     │                                │
│                     ▼                                │
│              Service Worker → Notification           │
└─────────────────────────────────────────────────────┘
```

## Project Structure

```
p-not/
├── node-backend/                    # Node.js backend (Express)
│   ├── src/
│   │   ├── index.js            # Server entry
│   │   ├── config.js           # Environment config
│   │   ├── routes.js           # API routes
│   │   ├── notificationService.js  # Azure NH client wrapper
│   │   └── generate-vapid.js   # VAPID key generator
│   ├── .env.example
│   └── package.json
│
├── python-backend/             # Python backend (FastAPI)
│   ├── app/
│   │   ├── main.py             # FastAPI app + middleware + logging
│   │   ├── config.py           # Pydantic settings
│   │   ├── auth.py             # HMAC-SHA256 + SAS token generation
│   │   ├── client.py           # NotificationHubsClient (REST API)
│   │   └── routes.py           # All API endpoints
│   ├── requirements.txt
│   └── .env
│
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── App.jsx             # Dashboard with scenario cards
│   │   ├── main.jsx            # Entry point
│   │   ├── usePushNotifications.js  # Push hook (all API calls)
│   │   └── components/
│   │       ├── Modal.jsx            # Base modal + form fields
│   │       ├── SubscribeModal.jsx   # Subscribe as User A/B
│   │       ├── SendBasicModal.jsx   # Phase 2.1 — tag-based send
│   │       ├── SendRichModal.jsx    # Phase 3 — icon, image, actions
│   │       ├── SendTargetedModal.jsx # Phase 2.2, 4.3, 4.4 — TTL, urgency
│   │       ├── BroadcastModal.jsx   # Phase 2.3 — all subscribers
│   │       ├── ScheduledModal.jsx   # Phase 7 — future delivery
│   │       └── DebugPanel.jsx       # Real-time debug log
│   ├── public/
│   │   └── sw.js               # Service worker (rich notification support)
│   ├── index.html
│   └── vite.config.js
│
├── package.json                # Root scripts
├── .gitignore
└── README.md
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.12+ (for Python backend)
- Azure Notification Hub (Free tier works)
- Modern browser (Chrome, Firefox, Edge — HTTPS or localhost)

### 1. Generate VAPID Keys

```bash
cd node-backend
npm install
npm run generate-vapid
```

Copy the output — you'll need both keys.

### 2. Configure Azure Notification Hub

1. Create a Notification Hub in Azure Portal
2. Go to **Notification Hub → Access Policies** → copy `DefaultFullSharedAccessSignature` connection string
3. Go to **Browser Push (Web)** → set:
   - **Public Key**: from step 1
   - **Private Key**: from step 1
   - **Subject**: `mailto:you@example.com`

### 3. Configure Environment

**Node.js backend** (`node-backend/.env`):

```env
AZURE_NOTIFICATION_HUB_CONNECTION_STRING=Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=DefaultFullSharedAccessSignature;SharedAccessKey=<key>;EntityPath=<hub-name>
AZURE_NOTIFICATION_HUB_NAME=<hub-name>
VAPID_PUBLIC_KEY=<from step 1>
VAPID_PRIVATE_KEY=<from step 1>
VAPID_SUBJECT=mailto:you@example.com
PORT=4000
FRONTEND_URL=http://localhost:5173
```

**Python backend** (`python-backend/.env`):

```env
AZURE_NOTIFICATION_HUB_CONNECTION_STRING=Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=DefaultFullSharedAccessSignature;SharedAccessKey=<key>
AZURE_NOTIFICATION_HUB_NAME=<hub-name>
VAPID_PUBLIC_KEY=<from step 1>
VAPID_PRIVATE_KEY=<from step 1>
VAPID_SUBJECT=mailto:you@example.com
PORT=8001
FRONTEND_URL=http://localhost:5173
```

### 4. Install Dependencies

```bash
# Node backend
cd node-backend && npm install

# Python backend
cd python-backend && pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### 5. Run

**Option A — Python backend + React frontend:**

```bash
# Terminal 1
cd python-backend
python -m uvicorn app.main:app --reload --port 8001

# Terminal 2
cd frontend
npm run dev
```

**Option B — Node backend + React frontend:**

```bash
# Terminal 1
cd    node-backend
npm run dev    # port 4000

# Terminal 2
cd frontend
npm run dev    # port 5173
```

> If using Node backend, update `API_BASE` in `frontend/src/usePushNotifications.js` to `http://localhost:4000/api`.

### 6. Test

1. Open `http://localhost:5173` in **Chrome**
2. Click **Subscribe** → enter `user-a` → subscribe
3. Open `http://localhost:5173` in a **second browser/incognito**
4. Click **Subscribe** → enter `user-b` → subscribe
5. Use the dashboard scenario cards to test each feature

## Testing Scenarios

| Phase | Scenario | Description |
|---|---|---|
| **Core** | Subscribe | Register browser as User A or User B |
| **2.1** | Send to User | Tag-based send to `user:user-a` |
| **2.2** | Tag Expression | Multi-tag filtering (`user:user-a AND web`) |
| **2.3** | Broadcast | Send to ALL subscribers via `all` tag |
| **3.x** | Rich Notification | Custom icon, image, action buttons, tag collapse |
| **4.3** | TTL | Notification expires after N seconds |
| **4.4** | Urgency | Priority levels: low / normal / high |
| **4.1** | 410 GONE | Auto-cleanup of expired subscriptions |
| **5.1** | Registrations | List all Azure installations (debug) |
| **7.1** | Schedule | Future delivery (Standard SKU only) |
| **7.2** | Cancel | Cancel a scheduled notification |

## API Reference

### Core

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/vapid-public-key` | Returns VAPID public key for browser subscription |
| `POST` | `/api/save-subscription` | Register browser push subscription as Azure installation |
| `DELETE` | `/api/unsubscribe` | Remove installation from Azure |

### Send Notifications

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/api/send` | `{ userId, title, body, url? }` | Send to specific user |
| `POST` | `/api/send/rich` | `{ userId, title, body, icon?, image?, actions?, tag?, silent? }` | Rich notification |
| `POST` | `/api/send/targeted` | `{ tagExpression, title, body, ttl?, urgency? }` | Send with tag expression + TTL + urgency |
| `POST` | `/api/broadcast` | `{ title, body, url?, ttl?, urgency? }` | Send to all subscribers |
| `POST` | `/api/send/scheduled` | `{ userId, title, body, scheduledTime }` | Schedule future delivery (Standard SKU) |
| `DELETE` | `/api/scheduled/{id}` | — | Cancel scheduled notification |

### Analytics & Debug

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/registrations` | List all installations (debug) |
| `GET` | `/api/installations/{id}` | Get specific installation |
| `GET` | `/api/outcome/{id}` | Get delivery outcome for a sent notification |
| `GET` | `/api/feedback` | Get PNS feedback container URL |

## Service Worker

The service worker (`frontend/public/sw.js`) handles:

- **Push events** — displays notification with title, body, icon, image, badge, actions
- **Click events** — opens the `url` from the notification payload
- **Tag collapse** — notifications with same `tag` replace previous ones
- **Silent mode** — `silent: true` suppresses sound/vibration

## Azure Notification Hubs — How It Works

### Installation Model

When a user subscribes:

1. Browser generates a push subscription (endpoint + keys)
2. Frontend sends it to the backend
3. Backend creates an **installation** in Azure with:
   - `installationId` — UUID
   - `platform` — `"browser"`
   - `pushChannel` — endpoint, p256dh, auth
   - `tags` — `[user:<id>, all, web]`
   - `expirationTime` — 30 days

### Send Model

When sending a notification:

1. Backend calls Azure REST API (`POST /messages`)
2. Azure matches tags to installations
3. Azure forwards to browser push service (FCM)
4. FCM delivers to the service worker

### Tag System

Tags enable targeting:

| Tag | Purpose |
|---|---|
| `user:<id>` | Target a specific user |
| `all` | Target everyone (broadcast) |
| `web` | Target web browsers only |

Tag expressions: `user:user-a`, `user:user-a AND web`, `all`.

## Production Checklist

- [ ] **HTTPS** — push requires HTTPS (localhost is exempt)
- [ ] **Auth middleware** — replace `userId` from request body with JWT/session
- [ ] **Connection string security** — use `DefaultSendSharedAccessSignature` (not `Full`)
- [ ] **410 handling** — auto-delete expired installations
- [ ] **Rate limiting** — prevent abuse of send endpoints
- [ ] **TTL** — set appropriate expiration for time-sensitive notifications
- [ ] **Error monitoring** — log Azure NH errors with tracking IDs
- [ ] **Registration cleanup** — periodically remove expired installations

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Wrong connection string | Add `EntityPath=<hub-name>` to connection string |
| `404 Hub not found` | Wrong hub name | Check `AZURE_NOTIFICATION_HUB_NAME` matches Azure Portal |
| `400 Bad Request` | Invalid JSON body | Check request Content-Type is `application/json` |
| Notification not received | VAPID not configured | Set VAPID keys in Azure Portal → Browser Push |
| `successCount: 0` | No matching installations | Check tags match between installation and send |
| Permission denied | User blocked notifications | Detect via `Notification.permission === "denied"` |

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Service Workers |
| Node backend | Express, @azure/notification-hubs v2 |
| Python backend | FastAPI, httpx, Azure REST API |
| Push service | Azure Notification Hubs |
| Browser push | FCM (Chrome/Firefox/Edge), APNs (Safari) |

## License

MIT
