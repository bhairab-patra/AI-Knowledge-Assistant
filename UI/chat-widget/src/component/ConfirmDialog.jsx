

import React from 'react';
export default function ConfirmDialog({
  isOpen,
  title,
  message,
  primaryButtonText,
  secondaryButtonText,
  primaryColor = '#272323ff',
  onConfirm,
  onCancel
}) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
        fontFamily: 'inherit'
      }}
      onClick={onCancel}
    >
      <div
        style={{
          background: 'white',
          borderRadius: '12px',
          padding: '24px',
          maxWidth: '400px',
          width: '90%',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{
          fontSize: '18px',
          fontWeight: 600,
          color: '#2d3748',
          marginBottom: '12px'
        }}>
          {title}
        </h2>

        <p style={{
          fontSize: '14px',
          color: '#4a5568',
          lineHeight: '1.6',
          marginBottom: '16px'
        }}>
          {message}
        </p>

        <div style={{
          display: 'flex',
          gap: '12px',
          justifyContent: 'flex-end'
        }}>
          <button
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              background: '#f3f4f6',
              color: '#4a5568'
            }}
            onClick={onCancel}
          >
            {secondaryButtonText}
          </button>

          <button
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              backgroundColor: primaryColor,
              color: 'white'
            }}
            onClick={onConfirm}
          >
            {primaryButtonText}
          </button>
        </div>
      </div>
    </div>
  );
}