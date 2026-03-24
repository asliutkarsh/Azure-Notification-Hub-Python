import { useState } from "react";
import { Modal, Field, Input, Button } from "./Modal";

export default function SendBasicModal({ open, onClose, onSend, userId }) {
  const [targetUser, setTargetUser] = useState(userId || "user-a");
  const [title, setTitle] = useState("Hello!");
  const [body, setBody] = useState("This is a test notification.");
  const [url, setUrl] = useState("");
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    setSending(true);
    try {
      await onSend({ userId: targetUser, title, body, url: url || undefined });
      onClose();
    } catch {
      // error shown in debug panel
    } finally {
      setSending(false);
    }
  };

  return (
    <Modal open={open} title="Send Basic Notification" onClose={onClose}>
      <Field label="Target User ID">
        <Input value={targetUser} onChange={setTargetUser} placeholder="user-a" />
      </Field>
      <Field label="Title">
        <Input value={title} onChange={setTitle} />
      </Field>
      <Field label="Body">
        <Input value={body} onChange={setBody} />
      </Field>
      <Field label="Click URL (optional)">
        <Input value={url} onChange={setUrl} placeholder="https://example.com" />
      </Field>
      <div>
        <Button onClick={handleSend} disabled={sending}>
          {sending ? "Sending..." : "Send"}
        </Button>
        <Button variant="cancel" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </Modal>
  );
}
