# 🚀 LXC Web Panel

A **cPanel-like web interface** for managing LXC containers on your VPS/host server.

![Dashboard](https://img.shields.io/badge/Status-Production%20Ready-green)
![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.8+-blue)

---

## ✨ Features

- 📊 **Dashboard** - Real-time statistics and system information
- 📦 **Container Management** - Create, start, stop, restart, freeze, delete containers
- 🖥️ **Web Console** - Execute commands inside containers directly from browser
- 🖼️ **Image Management** - View available LXC images
- 🔐 **Authentication** - Secure login system
- 📱 **Responsive UI** - Works on desktop and mobile
- 🎨 **Modern Design** - Beautiful gradient UI with Bootstrap 5

---

## 📋 Requirements

- **OS**: Ubuntu 20.04+ / Debian 11+ (with LXC support)
- **Python**: 3.8 or higher
- **LXC**: Installed and configured
- **Root/Sudo Access**

---

## 🚀 Installation

### Option 1: Automated Installation

```bash
# Clone or download the project
cd /path/to/LXC-WEB

# Run installation script (as root)
sudo ./install.sh
```

### Option 2: Manual Installation

```bash
# 1. Install LXC
sudo apt update
sudo apt install -y lxc lxc-utils

# 2. Install Python dependencies
pip3 install flask flask-cors

# 3. Run the application
python3 app.py
```

---

## 🔧 Usage

### Starting the Panel

```bash
# Development mode
python3 app.py

# Production (with systemd)
sudo systemctl start lxc-web-panel
sudo systemctl enable lxc-web-panel
```

### Access the Panel

Open your browser and navigate to:
```
http://YOUR_SERVER_IP:5000
```

### Default Credentials

```
Username: admin
Password: admin123
```

**⚠️ IMPORTANT**: Change the default password immediately!

---

## 📖 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/containers` | GET | Get all containers |
| `/api/containers` | POST | Create new container |
| `/api/containers/<name>/start` | POST | Start container |
| `/api/containers/<name>/stop` | POST | Stop container |
| `/api/containers/<name>/restart` | POST | Restart container |
| `/api/containers/<name>/freeze` | POST | Freeze container |
| `/api/containers/<name>/unfreeze` | POST | Unfreeze container |
| `/api/containers/<name>` | DELETE | Delete container |
| `/api/containers/<name>/info` | GET | Get container details |
| `/api/containers/<name>/execute` | POST | Execute command in container |
| `/api/system/info` | GET | Get system information |
| `/api/images` | GET | Get available images |

---

## 🛡️ Security

### Change Default Password

Edit `app.py` and change:
```python
ADMIN_PASSWORD_HASH = hashlib.sha256("your_secure_password".encode()).hexdigest()
```

### Use HTTPS (Production)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

### Firewall Configuration

```bash
# Allow only specific IPs
sudo ufw allow from YOUR_IP to any port 5000
```

---

## 🎨 Screenshots

### Dashboard
- Real-time container statistics
- System resource monitoring
- Quick actions

### Container Management
- Create containers with custom specs
- Start/Stop/Restart/Freeze
- Delete containers
- View detailed information

### Web Console
- Execute commands in containers
- Real-time output
- Interactive terminal

---

## 🔨 Development

### Project Structure

```
LXC-WEB/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── install.sh            # Installation script
├── README.md             # Documentation
└── templates/
    ├── index.html        # Dashboard UI
    └── login.html        # Login page
```

### Run in Development Mode

```bash
export FLASK_ENV=development
python3 app.py
```

---

## 🐛 Troubleshooting

### LXC not working?
```bash
# Check LXC status
sudo systemctl status lxc

# Enable LXC
sudo systemctl enable lxc
sudo systemctl start lxc
```

### Port already in use?
```bash
# Change port in app.py
app.run(host='0.0.0.0', port=8080)
```

### Permission denied?
```bash
# Run as root or add user to lxc group
sudo usermod -aG lxc your_username
```

---

## 📝 License

MIT License - Feel free to use and modify!

---

## 🤝 Support

If you like this project, please ⭐ star this repository!

### Features Requested?
Open an issue and let me know what features you'd like to see!

---

## 🙏 Credits

- **Flask** - Web Framework
- **Bootstrap 5** - UI Framework
- **LXC** - Container Technology
- **Bootstrap Icons** - Icons

---

**Made with ❤️ for LXC enthusiasts**
