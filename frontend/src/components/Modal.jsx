import { useState } from "react";

const overlayStyle = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.5)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 1000,
};

const modalStyle = {
  background: "#fff",
  borderRadius: 12,
  padding: 24,
  width: 480,
  maxHeight: "80vh",
  overflowY: "auto",
  boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
};

const labelStyle = {
  display: "block",
  fontSize: 13,
  fontWeight: 600,
  color: "#333",
  marginBottom: 4,
  marginTop: 12,
};

const inputStyle = {
  width: "100%",
  padding: "8px 12px",
  border: "1px solid #ddd",
  borderRadius: 6,
  fontSize: 14,
  boxSizing: "border-box",
};

const selectStyle = { ...inputStyle };

const buttonStyle = {
  padding: "10px 20px",
  fontSize: 14,
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  background: "#1976d2",
  color: "#fff",
  fontWeight: 600,
  marginTop: 16,
};

const cancelStyle = {
  ...buttonStyle,
  background: "#757575",
  marginLeft: 8,
};

export function Modal({ open, title, onClose, children }) {
  if (!open) return null;

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 18 }}>{title}</h2>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", fontSize: 20, cursor: "pointer", color: "#999" }}
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Field({ label, children }) {
  return (
    <div>
      <label style={labelStyle}>{label}</label>
      {children}
    </div>
  );
}

export function Input({ value, onChange, placeholder, ...rest }) {
  return (
    <input
      style={inputStyle}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      {...rest}
    />
  );
}

export function Select({ value, onChange, options }) {
  return (
    <select style={selectStyle} value={value} onChange={(e) => onChange(e.target.value)}>
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

export function Button({ children, onClick, disabled, variant }) {
  const style = variant === "cancel" ? cancelStyle : buttonStyle;
  return (
    <button style={style} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}
