import { useState } from "react";
import { Modal, Field, Input, Button } from "./Modal";

export default function SendRichModal({ open, onClose, onSend, userId }) {
  const [targetUser, setTargetUser] = useState(userId || "user-a");
  const [title, setTitle] = useState("Rich Notification");
  const [body, setBody] = useState("With icon, image, and actions.");
  const [icon, setIcon] = useState("https://via.placeholder.com/64");
  const [image, setImage] = useState("");
  const [url, setUrl] = useState("https://example.com");
  const [tag, setTag] = useState("");
  const [silent, setSilent] = useState(false);
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    setSending(true);
    try {
      await onSend({
        userId: targetUser,
        title,
        body,
        icon: icon || undefined,
        image: image || undefined,
        url: url || undefined,
        tag: tag || undefined,
        silent,
        actions: [
          { action: "open", title: "Open" },
          { action: "dismiss", title: "Dismiss" },
        ],
      });
      onClose();
    } catch {
    } finally {
      setSending(false);
    }
  };

  return (
    <Modal open={open} title="Send Rich Notification" onClose={onClose}>
      <Field label="Target User ID">
        <Input value={targetUser} onChange={setTargetUser} />
      </Field>
      <Field label="Title">
        <Input value={title} onChange={setTitle} />
      </Field>
      <Field label="Body">
        <Input value={body} onChange={setBody} />
      </Field>
      <Field label="Icon URL">
        <Input value={icon} onChange={setIcon} placeholder="https://example.com/icon.png" />
      </Field>
      <Field label="Image URL">
        <Input value={image} onChange={setImage} placeholder="https://example.com/image.jpg" />
      </Field>
      <Field label="Click URL">
        <Input value={url} onChange={setUrl} />
      </Field>
      <Field label="Tag (collapse ID)">
        <Input value={tag} onChange={setTag} placeholder="Same tag replaces old notification" />
      </Field>
      <Field label="Silent">
        <label style={{ fontSize: 14 }}>
          <input type="checkbox" checked={silent} onChange={(e) => setSilent(e.target.checked)} />{" "}
          No sound/vibration
        </label>
      </Field>
      <div>
        <Button onClick={handleSend} disabled={sending}>
          {sending ? "Sending..." : "Send Rich"}
        </Button>
        <Button variant="cancel" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </Modal>
  );
}
