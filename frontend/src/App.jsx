import { useState } from "react";
import { usePushNotifications } from "./usePushNotifications";
import SubscribeModal from "./components/SubscribeModal";
import SendBasicModal from "./components/SendBasicModal";
import SendRichModal from "./components/SendRichModal";
import SendTargetedModal from "./components/SendTargetedModal";
import BroadcastModal from "./components/BroadcastModal";
import ScheduledModal from "./components/ScheduledModal";
import DebugPanel from "./components/DebugPanel";

const scenarios = [
  {
    phase: "Core",
    items: [
      {
        id: "subscribe",
        title: "Subscribe",
        desc: "Register browser as a user",
        color: "#2e7d32",
        icon: "🔔",
      },
    ],
  },
  {
    phase: "Phase 2 — Targeting",
    items: [
      {
        id: "send-basic",
        title: "Send to User",
        desc: "2.1 — Tag-based send to specific user",
        color: "#1565c0",
        icon: "👤",
      },
      {
        id: "send-targeted",
        title: "Tag Expression",
        desc: "2.2 — Multi-tag filtering (AND/OR)",
        color: "#1565c0",
        icon: "🎯",
      },
      {
        id: "broadcast",
        title: "Broadcast All",
        desc: "2.3 — Send to every subscriber",
        color: "#e65100",
        icon: "📢",
      },
    ],
  },
  {
    phase: "Phase 3 — Rich Notifications",
    items: [
      {
        id: "send-rich",
        title: "Rich Notification",
        desc: "3.1–3.6 — Icon, image, actions, tag collapse",
        color: "#6a1b9a",
        icon: "✨",
      },
    ],
  },
  {
    phase: "Phase 4 — Reliability",
    items: [
      {
        id: "send-targeted",
        title: "TTL + Urgency",
        desc: "4.3–4.4 — Expiration and priority levels",
        color: "#c62828",
        icon: "⏱️",
        preset: { ttl: 30, urgency: "high" },
      },
    ],
  },
  {
    phase: "Phase 7 — Scheduling",
    items: [
      {
        id: "scheduled",
        title: "Schedule",
        desc: "7.1 — Deliver at future time (Standard SKU)",
        color: "#00695c",
        icon: "📅",
      },
    ],
  },
  {
    phase: "Phase 5 — Analytics",
    items: [
      {
        id: "registrations",
        title: "List Registrations",
        desc: "5.1 — View all installations in Azure",
        color: "#37474f",
        icon: "📊",
        action: true,
      },
    ],
  },
];

export default function App() {
  const hook = usePushNotifications();
  const {
    permission,
    subscribed,
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
  } = hook;

  const [modal, setModal] = useState(null);
  const [registrations, setRegistrations] = useState(null);

  const supported =
    typeof window !== "undefined" &&
    "serviceWorker" in navigator &&
    "PushManager" in window;

  if (!supported) {
    return (
      <div style={styles.container}>
        <h1>Push Notifications Lab</h1>
        <p style={styles.error}>Your browser does not support web push.</p>
      </div>
    );
  }

  const handleAction = async (id) => {
    if (id === "subscribe") {
      setModal("subscribe");
    } else if (id === "registrations") {
      try {
        const regs = await getRegistrations();
        setRegistrations(regs);
        setModal("registrations");
      } catch {}
    } else {
      setModal(id);
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={{ margin: 0, fontSize: 24 }}>Push Notifications Lab</h1>
        <p style={{ margin: "4px 0 0", color: "#666", fontSize: 14 }}>
          Azure Notification Hubs • Web Push Testing Dashboard
        </p>
      </div>

      {/* Status bar */}
      <div style={styles.statusBar}>
        <span>
          🔑 Permission: <strong>{permission}</strong>
        </span>
        <span>
          📡 Subscribed: <strong style={{ color: subscribed ? "#2e7d32" : "#c62828" }}>{subscribed ? "Yes" : "No"}</strong>
        </span>
        {userId && (
          <span>
            👤 User: <strong style={{ color: "#1565c0" }}>{userId}</strong>
          </span>
        )}
        {subscribed && (
          <button style={styles.smallBtn} onClick={unsubscribe} disabled={loading}>
            Unsubscribe
          </button>
        )}
      </div>

      {error && <div style={styles.errorBar}>❌ {error}</div>}

      {/* Scenario cards */}
      {scenarios.map((group) => (
        <div key={group.phase} style={{ marginBottom: 24 }}>
          <h3 style={styles.phaseTitle}>{group.phase}</h3>
          <div style={styles.cardGrid}>
            {group.items.map((item) => (
              <div
                key={item.id + (item.preset ? JSON.stringify(item.preset) : "")}
                style={{ ...styles.card, borderTop: `3px solid ${item.color}` }}
                onClick={() => handleAction(item.id)}
              >
                <div style={styles.cardIcon}>{item.icon}</div>
                <div style={styles.cardTitle}>{item.title}</div>
                <div style={styles.cardDesc}>{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Modals */}
      <SubscribeModal
        open={modal === "subscribe"}
        onClose={() => setModal(null)}
        onSubscribe={subscribe}
        loading={loading}
      />

      <SendBasicModal
        open={modal === "send-basic"}
        onClose={() => setModal(null)}
        onSend={sendBasic}
        userId={userId}
      />

      <SendRichModal
        open={modal === "send-rich"}
        onClose={() => setModal(null)}
        onSend={sendRich}
        userId={userId}
      />

      <SendTargetedModal
        open={modal === "send-targeted"}
        onClose={() => setModal(null)}
        onSend={sendTargeted}
      />

      <BroadcastModal
        open={modal === "broadcast"}
        onClose={() => setModal(null)}
        onSend={sendBroadcast}
      />

      <ScheduledModal
        open={modal === "scheduled"}
        onClose={() => setModal(null)}
        onSend={sendScheduled}
        userId={userId}
      />

      {/* Registrations modal */}
      {modal === "registrations" && (
        <div style={styles.overlay} onClick={() => setModal(null)}>
          <div style={styles.regModal} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
              <h2 style={{ margin: 0, fontSize: 18 }}>Registrations</h2>
              <button onClick={() => setModal(null)} style={styles.closeBtn}>✕</button>
            </div>
            {registrations && registrations.length === 0 && (
              <p style={{ color: "#666" }}>No registrations found.</p>
            )}
            {registrations?.map((reg, i) => (
              <div key={i} style={styles.regCard}>
                <div style={{ fontSize: 12, color: "#666", marginBottom: 4 }}>
                  {reg.kind || "Browser"} • {reg.registrationId?.substring(0, 20)}...
                </div>
                <div style={{ fontSize: 12 }}>
                  <strong>Tags:</strong> {reg.tags?.join(", ") || "none"}
                </div>
                <div style={{ fontSize: 11, color: "#999", marginTop: 2 }}>
                  Expires: {reg.expirationTime || "N/A"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <DebugPanel logs={logs} />
    </div>
  );
}

const styles = {
  container: {
    fontFamily: "system-ui, -apple-system, sans-serif",
    maxWidth: 900,
    margin: "0 auto",
    padding: "24px 24px 240px",
  },
  header: {
    marginBottom: 16,
  },
  statusBar: {
    display: "flex",
    gap: 20,
    alignItems: "center",
    padding: "12px 16px",
    background: "#f5f5f5",
    borderRadius: 8,
    marginBottom: 24,
    fontSize: 14,
    flexWrap: "wrap",
  },
  smallBtn: {
    padding: "4px 12px",
    fontSize: 12,
    border: "1px solid #ccc",
    borderRadius: 4,
    background: "#fff",
    cursor: "pointer",
    marginLeft: "auto",
  },
  errorBar: {
    padding: "10px 16px",
    background: "#ffebee",
    color: "#c62828",
    borderRadius: 8,
    marginBottom: 16,
    fontSize: 14,
  },
  phaseTitle: {
    margin: "0 0 8px",
    fontSize: 14,
    color: "#666",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  cardGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
    gap: 12,
  },
  card: {
    background: "#fff",
    border: "1px solid #e0e0e0",
    borderRadius: 8,
    padding: 16,
    cursor: "pointer",
    transition: "box-shadow 0.15s, transform 0.15s",
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  },
  cardIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: 600,
    marginBottom: 4,
  },
  cardDesc: {
    fontSize: 12,
    color: "#666",
    lineHeight: 1.4,
  },
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.5)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  regModal: {
    background: "#fff",
    borderRadius: 12,
    padding: 24,
    width: 560,
    maxHeight: "80vh",
    overflowY: "auto",
  },
  closeBtn: {
    background: "none",
    border: "none",
    fontSize: 20,
    cursor: "pointer",
    color: "#999",
  },
  regCard: {
    padding: 12,
    border: "1px solid #eee",
    borderRadius: 6,
    marginBottom: 8,
    background: "#fafafa",
  },
};
