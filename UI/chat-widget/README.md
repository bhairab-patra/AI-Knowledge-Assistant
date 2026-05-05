# Chat Widget

AI-powered knowledge assistant widget for Solifi products (ILS, ROS, ABL).

## Local Development

### Prerequisites
- Node.js
- npm or yarn

### Installation
```bash
# Clone repository
git clone 
cd chat-widget

# Install dependencies
npm install
```

### Environment Setup

Create `.env.development`:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

Create `.env.production`:
```bash
VITE_API_BASE_URL=https://your-api-gateway-url.com/dev
```

### Run Development Server
```bash
npm run dev
# Opens at http://localhost:5173
```

### Build for Production
```bash
npm run build
# Output: dist/ folder
```

### Test Locally
```bash
# Build first
npm run build

# Serve build
../ai-knowledge-assistant/AIKA-frontend/chat-widget 
npx serve dist -p 3000

# Open browser
# http://localhost:3000/?session=test_session_123
```
  "dev": "vite --mode development",
    "build": "vite build && cp chatWidget.html dist/index.html",
    "preview": "vite preview"




  Usage:
Build for DEV:
bash npm run build:dev
Build for UAT:
bash npm run build:uat
Build for PROD:
bash npm run build:prod

Make sure you have these files:
```
chatwidget-frontend/
├── .env.development    # REACT_APP_API_BASE_URL=http://localhost:8000
├── .env.dev           # REACT_APP_API_BASE_URL=https://api.aikadev.idscloud.io/dev
├── .env.uat           # REACT_APP_API_BASE_URL=https://api.aikauat.idscloud.io/uat
├── .env.prod          # REACT_APP_API_BASE_URL=https://api.solifi.com/prod
└── package.json


npx serve dist -p 3000

Verify Results:
bash# 1. Check BUILD_INFO.txt
cat dist/BUILD_INFO.txt

# Should show CDN URL now:
# Environment: DEV
# Version: 1.0.0
# Build Date: ...
# API URL: https://api.aikadev.idscloud.io/dev
# CDN URL: https://chatwidget.aikauat.idscloud.io

# 2. Check if __CDN_URL__ was replaced
grep "chatwidget" dist/index.html

# Should show:
# : 'https://chatwidget.aikauat.idscloud.io/chat-widget.umd.js';