#!/bin/bash
#
# LXC Web Panel - Quick Install Script
# For Debian/Ubuntu
#

set -e

echo "=========================================="
echo "  LXC Web Panel - Quick Install"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Running as root with sudo..."
    exec sudo bash "$0" "$@"
fi

# Install LXC
echo "[1/4] Installing LXC..."
apt update
apt install -y lxc lxc-templates lxcfs

# Create Python virtual environment
echo "[2/4] Setting up Python environment..."
apt install -y python3 python3-venv python3-pip

cd /home/admin/lxc/lxc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Flask
echo "[3/4] Installing Python packages..."
pip install --upgrade pip
pip install flask flask-cors

# Create systemd service
echo "[4/4] Creating systemd service..."
cat > /etc/systemd/system/lxc-web-panel.service << 'EOF'
[Unit]
Description=LXC Web Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/admin/lxc/lxc
Environment="PATH=/home/admin/lxc/lxc/venv/bin"
ExecStart=/home/admin/lxc/lxc/venv/bin/python /home/admin/lxc/lxc/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable lxc-web-panel
systemctl start lxc-web-panel

echo ""
echo "=========================================="
echo "  ✅ Installation Complete!"
echo "=========================================="
echo ""
echo "  🌐 Access: http://$(hostname -I | awk '{print $1}'):5000"
echo "  👤 Username: admin"
echo "  🔑 Password: admin123"
echo ""
echo "  ⚠️  CHANGE DEFAULT PASSWORD!"
echo "=========================================="

# Show status
systemctl status lxc-web-panel --no-pager
