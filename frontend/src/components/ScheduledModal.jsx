import { useState } from "react";
import { Modal, Field, Input, Button } from "./Modal";

export default function ScheduledModal({ open, onClose, onSend, userId }) {
  const [targetUser, setTargetUser] = useState(userId || "user-a");
  const [title, setTitle] = useState("Scheduled Hello");
  const [body, setBody] = useState("Delivered at the scheduled time.");
  const [url, setUrl] = useState("");
  const [minutes, setMinutes] = useState(5);
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    setSending(true);
    try {
      const scheduledTime = new Date(
        Date.now() + parseInt(minutes) * 60 * 1000
      ).toISOString();

      await onSend({
        userId: targetUser,
        title,
        body,
        url: url || undefined,
        scheduledTime,
      });
      onClose();
    } catch {
    } finally {
      setSending(false);
    }
  };

  return (
    <Modal open={open} title="Schedule Notification" onClose={onClose}>
      <p style={{ fontSize: 13, color: "#e65100", background: "#fff3e0", padding: 10, borderRadius: 6, margin: "0 0 12px" }}>
        Requires Standard SKU. Free tier does not support scheduling.
      </p>
      <Field label="Target User ID">
        <Input value={targetUser} onChange={setTargetUser} />
      </Field>
      <Field label="Title">
        <Input value={title} onChange={setTitle} />
      </Field>
      <Field label="Body">
        <Input value={body} onChange={setBody} />
      </Field>
      <Field label="Click URL (optional)">
        <Input value={url} onChange={setUrl} />
      </Field>
      <Field label="Deliver in (minutes)">
        <Input value={minutes} onChange={setMinutes} type="number" min={1} />
      </Field>
      <div>
        <Button onClick={handleSend} disabled={sending}>
          {sending ? "Scheduling..." : "Schedule"}
        </Button>
        <Button variant="cancel" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </Modal>
  );
}
