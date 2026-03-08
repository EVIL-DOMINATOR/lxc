#!/usr/bin/env python3
"""
LXC Web Panel - Main Application
A cPanel-like web interface for managing LXC containers
Compatible with LXC 6.x (Debian Trixie)
"""

import os
import subprocess
import json
import hashlib
import secrets
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Set PATH for LXC commands
os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:" + os.environ.get("PATH", "")

# Configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()  # Default password

# LXC command paths (LXC 6.x uses separate binaries)
LXC_CMD = {
    "ls": "/usr/bin/lxc-ls",
    "info": "/usr/bin/lxc-info",
    "start": "/usr/bin/lxc-start",
    "stop": "/usr/bin/lxc-stop",
    "restart": "/usr/bin/lxc-restart",
    "freeze": "/usr/bin/lxc-freeze",
    "unfreeze": "/usr/bin/lxc-unfreeze",
    "destroy": "/usr/bin/lxc-destroy",
    "config": "/usr/bin/lxc-config",
    "execute": "/usr/bin/lxc-execute",
    "create": "/usr/bin/lxc-create",
    "copy": "/usr/bin/lxc-copy",
    "snapshot": "/usr/bin/lxc-snapshot",
    "monitor": "/usr/bin/lxc-monitor",
    "console": "/usr/bin/lxc-console",
    "cgroup": "/usr/bin/lxc-cgroup",
    "checkpoint": "/usr/bin/lxc-checkpoint",
    "unshare": "/usr/bin/lxc-unshare",
    "top": "/usr/bin/lxc-top",
    "usernsrun": "/usr/bin/lxc-usernsexec",
}

def get_lxc_path(cmd_name):
    """Get full path for LXC command"""
    return LXC_CMD.get(cmd_name, f"/usr/bin/lxc-{cmd_name}")

def run_lxc_command(command):
    """Run LXC command and return output"""
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/usr/sbin:/bin:/sbin:/usr/local/bin:/usr/local/sbin:" + env.get("PATH", "")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_all_containers():
    """Get list of all LXC containers"""
    # Use lxc-ls to get container names
    ls_result = run_lxc_command(f"{get_lxc_path('ls')} --list")
    if not ls_result["success"]:
        return []
    
    container_names = ls_result["output"].strip().split()
    if not container_names:
        return []
    
    containers = []
    for name in container_names:
        # Get state for each container
        info_result = run_lxc_command(f"{get_lxc_path('info')} -s -n {name}")
        state = "Stopped"
        if info_result["success"]:
            state_output = info_result["output"].strip()
            if "RUNNING" in state_output:
                state = "Running"
            elif "FROZEN" in state_output:
                state = "Frozen"
        
        # Get IP address
        ip_result = run_lxc_command(f"{get_lxc_path('info')} -i -n {name}")
        ipv4 = ip_result["output"].strip() if ip_result["success"] else "N/A"
        
        containers.append({
            "name": name,
            "status": state,
            "image": "unknown",
            "network": {
                "eth0": {
                    "addresses": [{"address": ipv4}] if ipv4 and ipv4 != "N/A" else []
                }
            },
            "config": {}
        })
    
    return containers

def get_container_info(name):
    """Get detailed info about a container"""
    result = run_lxc_command(f"{get_lxc_path('info')} -n {name}")
    if result["success"]:
        return {"name": name, "info": result["output"], "success": True}
    return {"error": result["error"], "success": False}

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# API Routes
@app.route('/api/containers', methods=['GET'])
@login_required
def api_get_containers():
    containers = get_all_containers()
    return jsonify(containers)

@app.route('/api/containers', methods=['POST'])
@login_required
def api_create_container():
    data = request.json
    name = data.get('name')
    image = data.get('image', 'ubuntu:22.04')
    cpu = data.get('cpu', 2)
    memory = data.get('memory', '2GB')
    disk = data.get('disk', '10GB')
    
    if not name:
        return jsonify({"error": "Container name required"}), 400
    
    # Create container using lxc-create with download template
    # Format: lxc-create -t download -n <name> -- -d ubuntu -r jammy -a amd64
    create_cmd = f"{get_lxc_path('create')} -t download -n {name} -- -d ubuntu -r jammy -a amd64"
    result = run_lxc_command(create_cmd)
    
    if result["success"] or "already exists" in result["error"].lower():
        # Set CPU limits
        run_lxc_command(f"{get_lxc_path('config')} -n {name} lxc.cgroup2.cpu.max {cpu} 100000")
        
        # Set memory limits
        run_lxc_command(f"{get_lxc_path('config')} -n {name} lxc.cgroup2.memory.max {memory}")
        
        return jsonify({"success": True, "message": f"Container {name} created"})
    else:
        return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/start', methods=['POST'])
@login_required
def api_start_container(name):
    # -d for daemon mode
    result = run_lxc_command(f"{get_lxc_path('start')} -d -n {name}")
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} started"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/stop', methods=['POST'])
@login_required
def api_stop_container(name):
    result = run_lxc_command(f"{get_lxc_path('stop')} -n {name}")
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} stopped"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/restart', methods=['POST'])
@login_required
def api_restart_container(name):
    result = run_lxc_command(f"{get_lxc_path('restart')} -n {name}")
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} restarted"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/freeze', methods=['POST'])
@login_required
def api_freeze_container(name):
    result = run_lxc_command(f"{get_lxc_path('freeze')} -n {name}")
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} frozen"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/unfreeze', methods=['POST'])
@login_required
def api_unfreeze_container(name):
    result = run_lxc_command(f"{get_lxc_path('unfreeze')} -n {name}")
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} unfrozen"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>', methods=['DELETE'])
@login_required
def api_delete_container(name):
    force = request.args.get('force', 'false') == 'true'
    cmd = f"{get_lxc_path('destroy')} -n {name}"
    if force:
        cmd = f"{get_lxc_path('destroy')} -f -n {name}"
    result = run_lxc_command(cmd)
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} deleted"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/info', methods=['GET'])
@login_required
def api_container_info(name):
    info = get_container_info(name)
    if info:
        return jsonify(info)
    return jsonify({"error": "Container not found"}), 404

@app.route('/api/containers/<name>/console', methods=['GET'])
@login_required
def api_container_console(name):
    """Check if container is running for console access"""
    result = run_lxc_command(f"{get_lxc_path('info')} -s -n {name}")
    if result["success"] and "RUNNING" in result["output"]:
        return jsonify({"success": True, "message": "Console access available"})
    return jsonify({"error": "Container not running"}), 500

@app.route('/api/containers/<name>/execute', methods=['POST'])
@login_required
def api_execute_command(name):
    """Execute command inside container"""
    data = request.json
    command = data.get('command', '')
    if not command:
        return jsonify({"error": "Command required"}), 400
    
    # Use lxc-execute with -- option
    result = run_lxc_command(f"{get_lxc_path('execute')} -n {name} -- {command}")
    return jsonify(result)

@app.route('/api/system/info', methods=['GET'])
@login_required
def api_system_info():
    """Get host system information"""
    info = {}
    
    # Get hostname
    result = run_lxc_command("hostname")
    info['hostname'] = result['output'].strip() if result['success'] else 'Unknown'
    
    # Get uptime
    result = run_lxc_command("uptime -p")
    info['uptime'] = result['output'].strip() if result['success'] else 'Unknown'
    
    # Get memory info
    result = run_lxc_command("free -h")
    info['memory'] = result['output'].strip() if result['success'] else 'Unknown'
    
    # Get disk info
    result = run_lxc_command("df -h /")
    info['disk'] = result['output'].strip() if result['success'] else 'Unknown'
    
    # Get CPU info
    result = run_lxc_command("nproc")
    info['cpu_cores'] = result['output'].strip() if result['success'] else 'Unknown'
    
    # Get LXC version
    result = run_lxc_command(f"{get_lxc_path('ls')} --version")
    info['lxc_version'] = result['output'].strip() if result['success'] else 'Unknown'
    
    return jsonify(info)

@app.route('/api/images', methods=['GET'])
@login_required
def api_get_images():
    """Get available LXC images from images.linuxcontainers.org"""
    # Return predefined list of popular images
    images = [
        {"aliases": [{"name": "ubuntu:22.04"}], "properties": {"description": "Ubuntu 22.04 LTS Jammy", "architecture": "amd64"}, "size": 77000000},
        {"aliases": [{"name": "ubuntu:20.04"}], "properties": {"description": "Ubuntu 20.04 LTS Focal", "architecture": "amd64"}, "size": 72000000},
        {"aliases": [{"name": "debian:12"}], "properties": {"description": "Debian 12 Bookworm", "architecture": "amd64"}, "size": 65000000},
        {"aliases": [{"name": "debian:11"}], "properties": {"description": "Debian 11 Bullseye", "architecture": "amd64"}, "size": 68000000},
        {"aliases": [{"name": "almalinux:9"}], "properties": {"description": "AlmaLinux 9", "architecture": "amd64"}, "size": 85000000},
        {"aliases": [{"name": "centos:7"}], "properties": {"description": "CentOS 7", "architecture": "amd64"}, "size": 75000000},
    ]
    return jsonify(images)

if __name__ == '__main__':
    print("=" * 50)
    print("LXC Web Panel Starting...")
    print("Default Login: admin / admin123")
    print("Access: http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
