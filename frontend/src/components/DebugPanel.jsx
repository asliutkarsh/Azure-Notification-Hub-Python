import { useState } from "react";

const panelStyle = {
  position: "fixed",
  bottom: 0,
  left: 0,
  right: 0,
  background: "#1e1e1e",
  color: "#d4d4d4",
  fontFamily: "monospace",
  fontSize: 12,
  zIndex: 999,
  borderTop: "2px solid #333",
  transition: "height 0.2s",
};

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "8px 16px",
  background: "#2d2d2d",
  cursor: "pointer",
  userSelect: "none",
};

const logStyle = (type) => ({
  padding: "2px 16px",
  borderBottom: "1px solid #2a2a2a",
  color:
    type === "error" ? "#f44336" :
    type === "success" ? "#4caf50" :
    type === "warn" ? "#ff9800" :
    "#d4d4d4",
});

export default function DebugPanel({ logs }) {
  const [expanded, setExpanded] = useState(true);
  const [height, setHeight] = useState(200);

  return (
    <div style={{ ...panelStyle, height: expanded ? height : 36 }}>
      <div style={headerStyle} onClick={() => setExpanded(!expanded)}>
        <span>
          🐛 Debug Log ({logs.length}) {expanded ? "▼" : "▲"}
        </span>
        <div style={{ display: "flex", gap: 12 }}>
          <span
            style={{ cursor: "ns-resize", color: "#666", fontSize: 11 }}
            onClick={(e) => {
              e.stopPropagation();
              setHeight(height === 200 ? 400 : 200);
            }}
          >
            {height === 200 ? "⬆ Expand" : "⬇ Shrink"}
          </span>
        </div>
      </div>
      {expanded && (
        <div
          style={{
            overflowY: "auto",
            height: height - 36,
          }}
        >
          {logs.length === 0 && (
            <div style={{ padding: 16, color: "#666" }}>
              No logs yet. Subscribe and send a notification to see activity.
            </div>
          )}
          {logs.map((entry, i) => (
            <div key={i} style={logStyle(entry.type)}>
              <span style={{ color: "#666" }}>{entry.time}</span>{" "}
              <span style={{ color: entry.type === "error" ? "#f44336" : "#9cdcfe" }}>
                {entry.type === "error" ? "ERR" : entry.type === "warn" ? "WRN" : "INF"}
              </span>{" "}
              {entry.msg}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
