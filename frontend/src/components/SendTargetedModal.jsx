import { useState } from "react";
import { Modal, Field, Input, Button, Select } from "./Modal";

export default function SendTargetedModal({ open, onClose, onSend }) {
  const [tagExpression, setTagExpression] = useState("user:user-a");
  const [title, setTitle] = useState("Targeted");
  const [body, setBody] = useState("Sent to specific users.");
  const [url, setUrl] = useState("");
  const [ttl, setTtl] = useState("");
  const [urgency, setUrgency] = useState("");
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    setSending(true);
    try {
      await onSend({
        tagExpression,
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
    <Modal open={open} title="Send with Tag Expression" onClose={onClose}>
      <Field label="Tag Expression">
        <Input
          value={tagExpression}
          onChange={setTagExpression}
          placeholder="user:user-a, all, web"
        />
      </Field>
      <p style={{ fontSize: 11, color: "#888", margin: "4px 0 0" }}>
        Examples: <code>user:user-a</code> · <code>user:user-a AND web</code> · <code>all</code>
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
      <Field label="TTL (seconds, optional)">
        <Input value={ttl} onChange={setTtl} placeholder="30" type="number" />
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
          {sending ? "Sending..." : "Send Targeted"}
        </Button>
        <Button variant="cancel" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </Modal>
  );
}
