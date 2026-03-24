import { useState } from "react";
import { Modal, Field, Input, Button, Select } from "./Modal";

export default function BroadcastModal({ open, onClose, onSend }) {
  const [title, setTitle] = useState("Announcement");
  const [body, setBody] = useState("This goes to ALL subscribers.");
  const [url, setUrl] = useState("");
  const [ttl, setTtl] = useState("");
  const [urgency, setUrgency] = useState("");
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    setSending(true);
    try {
      await onSend({
        title,
        body,
        url: url || undefined,
        ttl: ttl ? parseInt(ttl) : undefined,
        urgency: urgency || undefined,
      });
      onClose();
    } catch {
    } finally {
      setSending(false);
    }
  };

  return (
    <Modal open={open} title="Broadcast to All" onClose={onClose}>
      <p style={{ fontSize: 13, color: "#e65100", background: "#fff3e0", padding: 10, borderRadius: 6, margin: "0 0 12px" }}>
        This sends to ALL registered devices regardless of tags.
      </p>
      <Field label="Title">
        <Input value={title} onChange={setTitle} />
      </Field>
      <Field label="Body">
        <Input value={body} onChange={setBody} />
      </Field>
      <Field label="Click URL (optional)">
        <Input value={url} onChange={setUrl} />
      </Field>
      <Field label="TTL (seconds)">
        <Input value={ttl} onChange={setTtl} placeholder="60" type="number" />
      </Field>
      <Field label="Urgency">
        <Select
          value={urgency}
          onChange={setUrgency}
          options={[
            { value: "", label: "Default" },
            { value: "low", label: "Low" },
            { value: "normal", label: "Normal" },
            { value: "high", label: "High" },
          ]}
        />
      </Field>
      <div>
        <Button onClick={handleSend} disabled={sending}>
          {sending ? "Broadcasting..." : "Broadcast"}
        </Button>
        <Button variant="cancel" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </Modal>
  );
}
