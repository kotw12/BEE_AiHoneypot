#!/bin/bash
# EC2 Startup script for Main Server
# Run: chmod +x start.sh && ./start.sh

echo "=== Honey Main Server Setup ==="

# Install dependencies
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "OPENAI_API_KEY=your-api-key-here" > .env
    echo "[!] Created .env - please set OPENAI_API_KEY"
fi

# Start server (systemd or direct)
echo "[*] Starting Main Server on port 80..."
PORT=80 python app.py
