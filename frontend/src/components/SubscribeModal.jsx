import { useState } from "react";
import { Modal, Field, Input, Button } from "./Modal";

export default function SubscribeModal({ open, onClose, onSubscribe, loading }) {
  const [userId, setUserId] = useState("user-a");

  const handleSubscribe = () => {
    onSubscribe(userId);
    onClose();
  };

  return (
    <Modal open={open} title="Subscribe as User" onClose={onClose}>
      <Field label="User ID">
        <Input
          value={userId}
          onChange={setUserId}
          placeholder="e.g. user-a, user-b"
        />
      </Field>
      <p style={{ fontSize: 12, color: "#666", marginTop: 8 }}>
        This browser will be registered as this user. Open a different browser
        to simulate a second user.
      </p>
      <div>
        <Button onClick={handleSubscribe} disabled={loading}>
          {loading ? "Subscribing..." : "Subscribe"}
        </Button>
        <Button variant="cancel" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </Modal>
  );
}
