# Personal FastNAS

> Transform your old laptop into a secure, personal cloud storage server

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tailscale](https://img.shields.io/badge/Secure-Tailscale-purple.svg)](https://tailscale.com/)

Turn any old Windows, Mac, or Linux laptop into your own private Network Attached Storage (NAS) server. Access your files securely from anywhere in the world using a clean, modern web interface.

**Perfect for:** Students, families, creators, small businesses, or anyone wanting private cloud storage without monthly fees.

---

## Screenshots

- System Architecutre
<img width="578" height="733" alt="image" src="https://github.com/user-attachments/assets/a6fd9334-6f0f-41de-baea-a9d4aa91994b" />

  
- Main file browser interface
<img width="1710" height="1112" alt="image" src="https://github.com/user-attachments/assets/26609715-c513-4488-8945-6be620f99b3c" />

- Search functionality
<img width="1710" height="1112" alt="image" src="https://github.com/user-attachments/assets/da5677cf-6fc3-43bc-a9d9-15478e9b47b6" />

- Storage statistics dashboard
<img width="1710" height="1112" alt="image" src="https://github.com/user-attachments/assets/036eac49-d0d5-4abd-ac8f-4e16bc26f4be" />

- Tailscale Dashboard
<img width="1710" height="1112" alt="image" src="https://github.com/user-attachments/assets/a96da39a-d3b3-49f5-ac42-f48769d92778" />




---

## Features

### For Everyone

- **Easy Setup** - Works on Windows, Mac, and Linux
- **Access Anywhere** - Use from phone, tablet, or any computer
- **Secure** - End-to-end encrypted access via Tailscale VPN
- **Modern UI** - Clean, Apple-like interface with Google Sans font
- **Full File Management** - Browse, upload, download, search, and delete
- **Fast Search** - Find files instantly by name or type
- **Storage Stats** - Monitor your disk usage in real-time

### For Developers

- **FastAPI Backend** - Modern, fast, production-ready API
- **API Key Authentication** - Secure access control
- **Structured Logging** - JSON logs for monitoring
- **Performance Optimized** - Caching, rate limiting, chunked uploads
- **RESTful API** - Complete API documentation
- **Easy Deployment** - Run as system service (24/7)

---

## Quick Start

### Prerequisites

- **Old laptop or desktop** (Windows 10/11, macOS, or Linux)
- **Python 3.11 or higher**
- **Internet connection** for initial setup
- A few minutes of your time

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/adityaa05/personal-fastNAS.git
cd personal-fastNAS
```

#### 2. Create Storage Directory

**Windows:**

```cmd
mkdir C:\nas-storage
```

**Mac/Linux:**

```bash
mkdir ~/nas-storage
```

#### 3. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 4. Configure Your Server

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit it with your values
```

**Edit `.env` with these settings:**

```env
# Storage Configuration
# Windows example: C:\nas-storage
# Mac/Linux example: /home/yourusername/nas-storage
NAS_BASE_DIR=/path/to/your/storage

# Security (IMPORTANT!)
ENABLE_AUTH=true
API_KEY=your-super-secret-key-change-this

# Performance Settings
MAX_UPLOAD_SIZE=104857600
LOG_LEVEL=INFO
ENVIRONMENT=production
```

Generate a secure API key (example):

```bash
# Using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Using OpenSSL (Mac/Linux)
openssl rand -hex 32
```

Copy the generated key and paste it into your `.env` file.

#### 5. Run the Server

```bash
# Make sure virtual environment is activated
python main.py
```

Visit in your browser: **http://localhost:8000/app**

---

## Remote Access Setup (Recommended)

Access your NAS from anywhere securely using **Tailscale VPN** (free for personal use).

### Step 1: Install Tailscale

**Download for your platform:**

- Windows: https://tailscale.com/download/windows
- Mac: https://tailscale.com/download/mac
- Linux: `curl -fsSL https://tailscale.com/install.sh | sh`
- Android/iOS: Search "Tailscale" in App Store/Play Store

### Step 2: Connect Your Devices

1. Install Tailscale on your NAS laptop (server)
2. Install Tailscale on your phone, tablet, other laptops (clients)
3. Sign in with the same account on all devices

### Step 3: Find Your Server IP

On your NAS laptop:

```bash
tailscale ip -4
```

Example output: `100.86.106.93` — this is your server IP

### Step 4: Access From Other Devices

On any device connected to Tailscale:

1. Open browser
2. Go to: `http://100.86.106.93:8000/app` (use your actual IP)
3. Click Settings in sidebar
4. Enter your Server URL: `http://100.86.106.93:8000`
5. Enter your API Key (from `.env` file)
6. Click Save and reload

Done! You can now access your files from anywhere.

---

## Running 24/7 as a Service

### Windows (Using NSSM)

#### Step 1: Download NSSM

1. Visit: https://nssm.cc/download
2. Download NSSM 2.24
3. Extract to `C:\nssm`

#### Step 2: Create Service Entry Point

Create `server.py` in your project directory:

```python
import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Listen on all interfaces
        port=8000,
        workers=2,  # Adjust based on CPU cores
        log_level="info"
    )
```

#### Step 3: Create Log Directory

```cmd
mkdir logs
```

#### Step 4: Install the Service

Open Command Prompt as Administrator:

```cmd
cd C:\nssm\win64
nssm install NASServer
```

In the NSSM GUI configure:

**Application Tab:**

- Path: `C:\path\to\personal-fastNAS\venv\Scripts\python.exe`
- Startup directory: `C:\path\to\personal-fastNAS`
- Arguments: `server.py`

**Details Tab:**

- Display name: Personal NAS Server
- Description: FastAPI NAS Server for file storage and access
- Startup type: Automatic

**I/O Tab:**

- Output (stdout): `C:\path\to\personal-fastNAS\logs\output.log`
- Error (stderr): `C:\path\to\personal-fastNAS\logs\error.log`

**Environment Tab:**

- Add environment file: Path to your `.env` file

Click "Install service"

#### Step 5: Manage the Service

Start the service:

```cmd
nssm start NASServer
```

Other useful commands:

```cmd
# Check status
nssm status NASServer

# Stop service
nssm stop NASServer

# Restart service
nssm restart NASServer

# Remove service (if needed)
nssm remove NASServer confirm

# View logs
type logs\output.log
type logs\error.log
```

You can also manage the service through Windows Services (services.msc)

### Linux (Using systemd)

Create `/etc/systemd/system/nas-server.service`:

```ini
[Unit]
Description=Personal NAS Server
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/personal-fastNAS
Environment="PATH=/home/yourusername/personal-fastNAS/venv/bin"
ExecStart=/home/yourusername/personal-fastNAS/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl enable nas-server
sudo systemctl start nas-server
```

### macOS (Using launchd)

Create `~/Library/LaunchAgents/com.personal.nas.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.personal.nas</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

**Load the service:**

```bash
launchctl load ~/Library/LaunchAgents/com.personal.nas.plist
```

---

## Usage Guide

### Browsing Files

1. Click **"Files"** in sidebar
2. Click folders to open them
3. Click files to download
4. Use breadcrumb navigation to go back

### Uploading Files

1. Click **"Upload"** in sidebar
2. Drag and drop files **OR** click to browse
3. Wait for upload to complete
4. Files appear in your current folder

### Searching Files

1. Click **"Search"** in sidebar
2. Type at least 2 characters
3. Press **Enter** or click **"Search"**
4. Click results to download

### Checking Storage

1. Click **"Storage"** in sidebar
2. View total, used, and free space
3. See file and folder counts

---

## Configuration

### Environment Variables (`.env` file)

| Variable          | Description               | Example                     | Required |
| ----------------- | ------------------------- | --------------------------- | -------- |
| `NAS_BASE_DIR`    | Storage directory path    | `/home/user/nas-storage`    | Yes      |
| `API_KEY`         | Secret authentication key | `abc123...`                 | Yes      |
| `ENABLE_AUTH`     | Enable API key auth       | `true` or `false`           | Yes      |
| `MAX_UPLOAD_SIZE` | Max file size in bytes    | `104857600` (100MB)         | No       |
| `LOG_LEVEL`       | Logging verbosity         | `INFO`, `DEBUG`, `ERROR`    | No       |
| `ENVIRONMENT`     | Environment mode          | `production`, `development` | No       |

### Allowed File Types

By default, these file types are supported:

- **Documents**: `.txt`, `.pdf`, `.doc`, `.docx`
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **Videos**: `.mp4`, `.mkv`
- **Audio**: `.mp3`
- **Archives**: `.zip`

To add more types, edit `ALLOWED_EXTENSIONS` in `main.py`.

---

## Security Best Practices

### ✅ DO:

- ✅ Use a **strong, random API key** (32+ characters)
- ✅ Enable authentication (`ENABLE_AUTH=true`)
- ✅ Use **Tailscale** for remote access (not port forwarding)
- ✅ Keep **Windows/Mac/Linux updated**
- ✅ Change API key **regularly** (every 3-6 months)
- ✅ Backup your `.env` file **securely**
- ✅ Use **HTTPS** if exposing to internet (advanced)

### ❌ DON'T:

- ❌ Share your API key with anyone
- ❌ Use simple API keys like "password123"
- ❌ Disable authentication in production
- ❌ Expose port 8000 directly to internet
- ❌ Store `.env` file in version control
- ❌ Use the same API key on multiple servers

---

## Troubleshooting

### Server Won't Start

**Problem**: `Port 8000 already in use`

**Solution**:

```bash
# Find what's using port 8000
# Windows:
netstat -ano | findstr :8000

# Mac/Linux:
lsof -i :8000

# Kill the process or change port in main.py
```

### Can't Connect via Tailscale

**Problem**: `Connection refused` from other devices

**Solution**:

1. Check Tailscale is running: `tailscale status`
2. Verify server is running: `curl http://localhost:8000/health`
3. Check firewall allows port 8000
4. Confirm both devices on same Tailscale network

### 401 Unauthorized Errors

**Problem**: API key not working

**Solution**:

1. Go to **Settings** in web interface
2. Re-enter your API key from `.env` file
3. Click **"Save API Key"**
4. Wait for page to reload
5. Try again

### Slow Performance

**Problem**: API requests take minutes

**Solution**:

- Reduce `MAX_UPLOAD_SIZE` in `.env`
- Clear old logs regularly
- Limit search results
- Consider faster storage (SSD vs HDD)

---

## API Documentation

Access interactive API docs (development only):

```bash
# Set in .env:
ENVIRONMENT=development

# Visit:
http://localhost:8000/docs
```

### Key Endpoints

| Method   | Endpoint             | Description             |
| -------- | -------------------- | ----------------------- |
| `GET`    | `/health`            | Server health check     |
| `GET`    | `/api/files`         | List files in directory |
| `GET`    | `/api/stats`         | Storage statistics      |
| `GET`    | `/api/search`        | Search files            |
| `POST`   | `/api/upload`        | Upload files            |
| `GET`    | `/api/download`      | Download file           |
| `DELETE` | `/api/delete/{path}` | Delete file/folder      |

---

## Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

- 🐛 **Report bugs** via [GitHub Issues](https://github.com/adityaa05/personal-fastNAS/issues)
- 💡 **Suggest features** or improvements
- 📝 **Improve documentation**
- 🌍 **Translate** to other languages
- 🎨 **Design** UI/UX improvements
- 💻 **Submit code** via Pull Requests

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/personal-fastNAS.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make changes and test thoroughly
5. Commit: `git commit -m "Add: your feature description"`
6. Push: `git push origin feature/your-feature-name`
7. Open a Pull Request

### Code Style

- Follow **PEP 8** for Python code
- Use **meaningful variable names**
- Add **comments** for complex logic
- Write **docstrings** for functions
- Test on **Windows, Mac, and Linux** if possible

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**TL;DR**: You can use, modify, and distribute this software freely. No warranty provided.

---

## Acknowledgments

Built with:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Tailscale](https://tailscale.com/) - Secure VPN solution
- [Uvicorn](https://www.uvicorn.org/) - ASGI server
- [Pillow](https://python-pillow.org/) - Image processing

---

## Support & Contact

- **Issues**: [GitHub Issues](https://github.com/adityaa05/personal-fastNAS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/adityaa05/personal-fastNAS/discussions)
- **Email**: [your-email@example.com](mailto:your-email@example.com)

---

## Star History

If you find this project useful, please consider giving it a ⭐️ on GitHub!

---

## Roadmap

### Current Features (v2.0)

- ✅ File browsing and management
- ✅ Upload and download
- ✅ Search functionality
- ✅ Tailscale integration
- ✅ API key authentication
- ✅ Storage statistics

### Planned Features (v3.0)

- [ ] File sharing with expiring links
- [ ] Thumbnail preview for images
- [ ] Video streaming with player
- [ ] Multiple user accounts
- [ ] File versioning
- [ ] Mobile app (Android/iOS)
- [ ] Backup automation
- [ ] HTTPS support
- [ ] Docker deployment

Vote on features in [GitHub Discussions](https://github.com/adityaa05/personal-fastNAS/discussions)!

---

## Support the Project

If you love this project:

- ⭐ **Star** the repository
- 🐦 **Share** on social media
- 💬 **Tell** your friends
- 🤝 **Contribute** code or docs
- ☕ **Buy me a coffee** (if you're feeling generous!)

---

<div align="center">

**Made by [Aditya](https://github.com/adityaa05)**

Turn your old tech into something useful.

[Back to Top](#personal-fastnas)

</div>
