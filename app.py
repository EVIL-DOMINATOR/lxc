#!/usr/bin/env python3
"""
LXC Web Panel - Main Application
A cPanel-like web interface for managing LXC containers
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

# Configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()  # Default password

# LXC Management Functions
def run_lxc_command(command):
    """Run LXC command and return output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
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
    result = run_lxc_command("lxc list --format json")
    if result["success"]:
        try:
            containers = json.loads(result["output"])
            return containers
        except json.JSONDecodeError:
            return []
    return []

def get_container_info(name):
    """Get detailed info about a container"""
    result = run_lxc_command(f"lxc info {name} --format json")
    if result["success"]:
        try:
            return json.loads(result["output"])
        except json.JSONDecodeError:
            return None
    return None

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
    
    # Create container
    create_cmd = f"lxc launch {image} {name}"
    result = run_lxc_command(create_cmd)
    
    if result["success"]:
        # Set limits
        run_lxc_command(f"lxc config set {name} limits.cpu {cpu}")
        run_lxc_command(f"lxc config set {name} limits.memory {memory}")
        run_lxc_command(f"lxc config device set {name} root size {disk}")
        
        return jsonify({"success": True, "message": f"Container {name} created"})
    else:
        return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/start', methods=['POST'])
@login_required
def api_start_container(name):
    result = run_lxc_command(f"lxc start {name}")
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} started"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/stop', methods=['POST'])
@login_required
def api_stop_container(name):
    result = run_lxc_command(f"lxc stop {name}")
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} stopped"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/restart', methods=['POST'])
@login_required
def api_restart_container(name):
    result = run_lxc_command(f"lxc restart {name}")
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} restarted"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/freeze', methods=['POST'])
@login_required
def api_freeze_container(name):
    result = run_lxc_command(f"lxc freeze {name}")
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} frozen"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/unfreeze', methods=['POST'])
@login_required
def api_unfreeze_container(name):
    result = run_lxc_command(f"lxc unfreeze {name}")
    if result["success"]:
        return jsonify({"success": True, "message": f"Container {name} unfrozen"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>', methods=['DELETE'])
@login_required
def api_delete_container(name):
    force = request.args.get('force', 'false') == 'true'
    cmd = f"lxc delete {name}" if not force else f"lxc delete -f {name}"
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
    """Get container console output"""
    result = run_lxc_command(f"lxc exec {name} -- bash -c 'whoami'")
    if result["success"]:
        return jsonify({"success": True, "message": "Console access available"})
    return jsonify({"error": result["error"]}), 500

@app.route('/api/containers/<name>/execute', methods=['POST'])
@login_required
def api_execute_command(name):
    """Execute command inside container"""
    data = request.json
    command = data.get('command', '')
    if not command:
        return jsonify({"error": "Command required"}), 400
    
    result = run_lxc_command(f"lxc exec {name} -- {command}")
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
    result = run_lxc_command("lxc --version")
    info['lxc_version'] = result['output'].strip() if result['success'] else 'Unknown'
    
    return jsonify(info)

@app.route('/api/images', methods=['GET'])
@login_required
def api_get_images():
    """Get available LXC images"""
    result = run_lxc_command("lxc image list --format json")
    if result["success"]:
        try:
            images = json.loads(result["output"])
            return jsonify(images)
        except json.JSONDecodeError:
            return jsonify([])
    return jsonify([])

if __name__ == '__main__':
    print("=" * 50)
    print("LXC Web Panel Starting...")
    print("Default Login: admin / admin123")
    print("Access: http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
