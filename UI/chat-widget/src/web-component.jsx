// src/web-component.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import ChatApp from './ChatApp';
import styles from './ChatApp.css?inline';

class ChatWidget extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    const mountPoint = document.createElement('div');

    // Inject CSS into shadow DOM
    const style = document.createElement('style');
    style.textContent = styles;

    this.shadowRoot.appendChild(style);
    this.shadowRoot.appendChild(mountPoint);

    // Get attributes and pass as props
    const props = {
      chatSessionId: this.getAttribute('session-id'),
      iframeMode: this.getAttribute('iframe-mode'),
    };

    // Render React app
    this.root = ReactDOM.createRoot(mountPoint);
    this.root.render(<ChatApp {...props} />);
  }

  disconnectedCallback() {
    if (this.root) {
      this.root.unmount();
    }
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue && this.root) {
      this.connectedCallback();
    }
  }
}

if (!customElements.get('chat-widget')) {
  customElements.define('chat-widget', ChatWidget);
}

export default ChatWidget;