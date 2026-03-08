#!/bin/bash
#
# LXC Web Panel Installation Script
# For Ubuntu/Debian Linux
#

set -e

echo "=========================================="
echo "  LXC Web Panel Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo ./install.sh)"
    exit 1
fi

# Update system
echo "[1/6] Updating system packages..."
apt update -y

# Install LXC if not installed
echo "[2/6] Installing LXC..."
apt install -y lxc lxc-utils

# Enable and start LXC service
echo "[3/6] Enabling LXC service..."
systemctl enable lxc
systemctl start lxc

# Install Python and pip
echo "[4/6] Installing Python dependencies..."
apt install -y python3 python3-pip

# Install Python packages
echo "[5/6] Installing Python packages..."
pip3 install flask flask-cors

# Create systemd service
echo "[6/6] Creating systemd service..."
cat > /etc/systemd/system/lxc-web-panel.service << EOF
[Unit]
Description=LXC Web Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/lxc-web-panel
ExecStart=/usr/bin/python3 /opt/lxc-web-panel/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create app directory
mkdir -p /opt/lxc-web-panel
cp -r ./* /opt/lxc-web-panel/

# Reload systemd and start service
systemctl daemon-reload
systemctl enable lxc-web-panel
systemctl start lxc-web-panel

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "  Access Panel: http://YOUR_SERVER_IP:5000"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "  IMPORTANT: Change the default password!"
echo "=========================================="
echo ""

# Show status
systemctl status lxc-web-panel --no-pager
