# Complete Windows 11 Server Deployment Guide
## FastAPI NAS with Remote Access (Tailscale Recommended)

This guide will help you set up your Lenovo laptop as a 24/7 server accessible from anywhere.

---

## 🎯 Quick Answer to Your Key Questions

### **Is Tailscale the best solution?**
**YES**, Tailscale is the MOST recommended option for your use case. Here's why:

✅ **Zero Configuration** - No port forwarding, no router setup, no firewall rules
✅ **Secure by Default** - WireGuard-based encryption, no exposed ports to internet
✅ **Simple Setup** - 5 minutes to complete setup
✅ **Cross-Platform** - Works seamlessly on Windows, Android, iOS, macOS, Linux
✅ **Free Tier** - Up to 100 devices, perfect for personal use
✅ **Fast** - Direct peer-to-peer connections when possible
✅ **Reliable** - Automatic failover, works behind complex NATs

### **Alternatives Comparison:**

| Solution | Security | Setup Complexity | Cost | Speed | Recommendation |
|----------|----------|------------------|------|-------|----------------|
| **Tailscale** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ Easy | Free | ⭐⭐⭐⭐⭐ | **✅ BEST** |
| Port Forwarding | ⭐⭐ Risky | ⭐⭐ Complex | Free | ⭐⭐⭐⭐⭐ | ❌ Not Recommended |
| Cloudflare Tunnel | ⭐⭐⭐⭐ | ⭐⭐⭐ Moderate | Free | ⭐⭐⭐ | ⚠️ Good alternative |
| ngrok | ⭐⭐⭐ | ⭐⭐⭐⭐ Easy | Paid | ⭐⭐⭐ | ⚠️ For testing only |

**Verdict:** Use Tailscale. It's the perfect balance of security, simplicity, and performance.

---

## 📋 Part 1: Prerequisites on Lenovo Laptop (Windows 11)

### Step 1: Install Python 3.11+

1. **Download Python:**
   - Visit: https://www.python.org/downloads/
   - Download Python 3.11 or 3.12 (latest stable)

2. **Install Python:**
   - Run installer
   - ✅ **CHECK** "Add Python to PATH" (CRITICAL!)
   - Click "Install Now"

3. **Verify Installation:**
   ```cmd
   python --version
   pip --version
   ```

### Step 2: Install Git (Optional but Recommended)

Download from: https://git-scm.com/download/win

---

## 🚀 Part 2: Setting Up Your FastAPI Server

### Step 1: Create Project Directory

```cmd
:: Create a dedicated folder
mkdir C:\nas-server
cd C:\nas-server

:: Create storage directory (or use existing SSD location)
mkdir C:\nas-storage
```

### Step 2: Set Up Python Environment

```cmd
:: Create virtual environment
python -m venv venv

:: Activate it
venv\Scripts\activate

:: Your prompt should now show (venv)
```

### Step 3: Install Dependencies

```cmd
:: Upgrade pip
python -m pip install --upgrade pip

:: Install required packages
pip install fastapi uvicorn[standard] pillow python-multipart

:: Verify installation
pip list | findstr "fastapi uvicorn pillow"
```

### Step 4: Create Your Files

1. **Save your backend code as `main.py`** in `C:\nas-server\`

2. **Save your frontend code as `index.html`** in `C:\nas-server\`

3. **Create `.env` file:**

```cmd
notepad .env
```

Add this content:
```env
# Storage Configuration
NAS_BASE_DIR=C:\nas-storage

# File Upload Settings
MAX_UPLOAD_SIZE=104857600

# Security Settings (IMPORTANT!)
ENABLE_AUTH=true
API_KEY=your-secure-api-key-change-this-now

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production
```

**Generate secure API key:**
```cmd
:: Open Python
python

>>> import secrets
>>> print(secrets.token_hex(32))
>>> exit()

:: Copy the generated key and paste in .env file
```

### Step 5: Test Your Server

```cmd
cd C:\nas-server
venv\Scripts\activate
python main.py
```

Visit in browser:
- http://localhost:8000 - API root
- http://localhost:8000/health - Health check

Press `Ctrl+C` to stop.

---

## 🔄 Part 3: Serving Frontend with Backend

### Option A: Serve Frontend from FastAPI (Recommended)

Update your `main.py` to serve the HTML file:

Add this import at the top:
```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
```

Add this route before your other routes:
```python
@app.get("/app", response_class=HTMLResponse, tags=["Frontend"])
async def serve_frontend():
    """Serve the frontend interface"""
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
```

Now you can access:
- **Frontend:** http://localhost:8000/app
- **API:** http://localhost:8000/api/...

### Option B: Separate Static File Server

Create a `static` folder and move `index.html` there, then add to `main.py`:

```python
# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("static/index.html")
```

---

## 🌐 Part 4: Installing Tailscale

### Step 1: Install Tailscale on Lenovo Laptop

1. **Download Tailscale:**
   - Visit: https://tailscale.com/download/windows
   - Download and run installer

2. **Install:**
   - Run the installer
   - Follow the prompts
   - Sign in with Google, Microsoft, or create account

3. **Verify Installation:**
   - Tailscale icon should appear in system tray
   - Click it and ensure it says "Connected"

### Step 2: Get Your Tailscale IP

```cmd
:: Open Command Prompt
tailscale ip -4

:: Example output: 100.x.x.x
:: Save this IP - you'll use it to access your server!
```

### Step 3: Set a Friendly Hostname (Optional)

```cmd
:: Set a memorable name
tailscale set --hostname lenovo-nas

:: Now you can access via: http://lenovo-nas:8000
```

### Step 4: Install Tailscale on Other Devices

**On Your Main Laptop (Windows/Mac/Linux):**
- Download from https://tailscale.com/download
- Install and sign in with SAME account

**On Your Phone (Android/iOS):**
- Download "Tailscale" from App Store or Play Store
- Sign in with SAME account

**Verify Connection:**
- All devices should appear in: https://login.tailscale.com/admin/machines
- You can now ping each device from any other device!

---

## 🔧 Part 5: Running Server as Windows Service (24/7)

### Method 1: Using NSSM (Recommended - Easiest)

#### Step 1: Download NSSM

1. Visit: https://nssm.cc/download
2. Download NSSM 2.24
3. Extract to `C:\nssm`

#### Step 2: Create Service Entry Point

Create `server.py` in `C:\nas-server\`:

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

#### Step 3: Install the Service

```cmd
:: Open Command Prompt AS ADMINISTRATOR
cd C:\nssm\win64

:: Install service
nssm install NASServer

:: This opens a GUI configuration window
```

**In the NSSM GUI:**

**Application Tab:**
- Path: `C:\nas-server\venv\Scripts\python.exe`
- Startup directory: `C:\nas-server`
- Arguments: `server.py`

**Details Tab:**
- Display name: `Personal NAS Server`
- Description: `FastAPI NAS Server for file storage and access`
- Startup type: `Automatic`

**I/O Tab:**
- Output (stdout): `C:\nas-server\logs\output.log`
- Error (stderr): `C:\nas-server\logs\error.log`

**Environment Tab:**
- Add environment file: `C:\nas-server\.env`

Click "Install service"

#### Step 4: Create Log Directory

```cmd
mkdir C:\nas-server\logs
```

#### Step 5: Start the Service

```cmd
:: Start service
nssm start NASServer

:: Check status
nssm status NASServer

:: View in Services
services.msc
```

#### Step 6: Useful Service Commands

```cmd
:: Stop service
nssm stop NASServer

:: Restart service
nssm restart NASServer

:: Remove service (if needed)
nssm remove NASServer confirm

:: View logs
type C:\nas-server\logs\output.log
type C:\nas-server\logs\error.log
```

### Method 2: Using Python Windows Service (Advanced)

If you prefer native Windows service:

1. Install `pywin32`:
   ```cmd
   pip install pywin32
   ```

2. Create service file (see GitHub examples)
3. Register using `pythonservice.exe`

**Recommendation:** Use NSSM for simplicity.

---

## ⚡ Part 6: Windows 11 Power Settings (24/7 Operation)

### Step 1: Prevent Sleep When Lid Closed

1. **Open Settings** → **System** → **Power**
2. Click **"Power mode"** → Set to **"Best performance"**
3. Click **"Screen and sleep"**:
   - When plugged in, put device to sleep: **Never**
   - When plugged in, turn off screen: **Never** (or 30 min)

### Step 2: Advanced Power Settings

1. **Control Panel** → **Power Options**
2. Click **"Change plan settings"** → **"Change advanced power settings"**
3. Expand these options:
   - **Hard disk** → Turn off after: **Never**
   - **Sleep** → Sleep after: **Never**
   - **Sleep** → Hibernate after: **Never**
   - **USB settings** → Selective suspend: **Disabled**
   - **Processor power management** → Min state: **50%**

### Step 3: Lid Close Action

1. **Control Panel** → **Power Options**
2. Click **"Choose what closing the lid does"**
3. Set both options to **"Do nothing"**

### Step 4: Disable Fast Startup (Recommended)

Fast Startup can cause issues with services:

1. **Control Panel** → **Power Options**
2. **"Choose what the power buttons do"**
3. Click **"Change settings that are currently unavailable"**
4. Uncheck **"Turn on fast startup"**
5. Click **Save changes**

### Step 5: Keep Laptop Ventilated

⚠️ **IMPORTANT:** 
- Place laptop on hard, flat surface
- Ensure good airflow
- Consider a laptop cooling pad
- Monitor temperature regularly

---

## 🔐 Part 7: Firewall Configuration

### Option 1: Windows Firewall (Simple)

```cmd
:: Open Command Prompt AS ADMINISTRATOR

:: Allow FastAPI through firewall
netsh advfirewall firewall add rule name="FastAPI NAS Server" dir=in action=allow protocol=TCP localport=8000

:: Allow Tailscale (usually auto-configured)
netsh advfirewall firewall add rule name="Tailscale" dir=in action=allow program="%ProgramFiles%\Tailscale\tailscaled.exe"
```

### Option 2: Windows Defender Firewall GUI

1. Open **Windows Security** → **Firewall & network protection**
2. Click **"Advanced settings"**
3. **Inbound Rules** → **New Rule**
4. Port → TCP → 8000 → Allow → All profiles
5. Name: "FastAPI NAS Server"

**Note:** With Tailscale, you don't need to expose port 8000 to public internet!

---

## 📱 Part 8: Accessing Your Server

### From Tailscale Network

**Your Main Laptop:**
```
http://100.x.x.x:8000/app
```

**Your Phone:**
1. Install Tailscale app
2. Sign in
3. Open browser
4. Go to: `http://100.x.x.x:8000/app`

### Update Frontend for Remote Access

Edit `index.html` line ~290:

```javascript
// Original (works only on same machine)
const CONFIG = {
    baseUrl: window.location.origin,
    apiKey: localStorage.getItem('nas_api_key') || ''
};

// Updated for Tailscale (works from anywhere)
const CONFIG = {
    baseUrl: 'http://100.x.x.x:8000',  // Your Tailscale IP
    apiKey: localStorage.getItem('nas_api_key') || ''
};
```

Or make it smart:

```javascript
const CONFIG = {
    // Auto-detect if on same machine or remote
    baseUrl: window.location.hostname === 'localhost' 
        ? window.location.origin 
        : 'http://100.x.x.x:8000',  // Your Tailscale IP
    apiKey: localStorage.getItem('nas_api_key') || ''
};
```

---

## 🧪 Part 9: Testing Everything

### Step 1: Verify Service is Running

```cmd
:: Check service status
nssm status NASServer

:: Should output: "SERVICE_RUNNING"
```

### Step 2: Test Local Access

Open browser on Lenovo laptop:
```
http://localhost:8000/app
http://localhost:8000/health
```

### Step 3: Test Tailscale Access

**From your main laptop:**
1. Ensure Tailscale is running
2. Open browser
3. Visit: `http://100.x.x.x:8000/app`
4. You should see your interface!

**From your phone:**
1. Ensure Tailscale app is running
2. Open browser
3. Visit: `http://100.x.x.x:8000/app`
4. Test uploading/downloading files

### Step 4: Test API Key Authentication

1. Go to Settings in the interface
2. Enter your API key from `.env` file
3. Save
4. Test all features:
   - Browse files
   - Upload a file
   - Search files
   - View storage stats
   - Download a file

### Step 5: Test 24/7 Operation

```cmd
:: Restart Lenovo laptop
shutdown /r /t 0

:: After restart, check if service auto-started
nssm status NASServer

:: Should be running automatically!
```

---

## 🔍 Part 10: Monitoring & Maintenance

### Check Server Logs

```cmd
:: View recent activity
type C:\nas-server\logs\output.log | more

:: View errors
type C:\nas-server\logs\error.log | more

:: Clear old logs (run monthly)
del C:\nas-server\logs\*.log
```

### Monitor System Resources

```cmd
:: Open Task Manager
taskmgr

:: Look for "python.exe" under Details tab
:: Check CPU, Memory, Disk usage
```

### Monitor Disk Space

```cmd
:: Check storage directory
dir C:\nas-storage

:: Check disk space
wmic logicaldisk get size,freespace,caption
```

### Create Health Check Script

Save as `check_health.bat` in `C:\nas-server\`:

```batch
@echo off
echo === NAS Server Health Check ===
echo.

echo Service Status:
nssm status NASServer
echo.

echo Tailscale Status:
tailscale status
echo.

echo API Health Check:
curl http://localhost:8000/health
echo.

echo Disk Space:
wmic logicaldisk where "DeviceID='C:'" get freespace,size
echo.

echo Recent Logs (last 10 lines):
powershell -Command "Get-Content C:\nas-server\logs\output.log -Tail 10"

pause
```

Run this weekly to verify everything is working.

---

## 🚨 Part 11: Troubleshooting

### Service Won't Start

```cmd
:: Check service status
nssm status NASServer

:: View service logs
type C:\nas-server\logs\error.log

:: Common issues:
:: 1. Python path incorrect
:: 2. Virtual environment not activated
:: 3. Port 8000 already in use
```

**Fix port conflict:**
```cmd
:: Find what's using port 8000
netstat -ano | findstr :8000

:: Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Can't Access via Tailscale

```cmd
:: Check Tailscale is running
tailscale status

:: Restart Tailscale
net stop Tailscale
net start Tailscale

:: Verify IP
tailscale ip -4

:: Ping from another device
ping 100.x.x.x
```

### Frontend Not Loading

1. **Check baseUrl in frontend:**
   - Open browser DevTools (F12)
   - Check Console for errors
   - Verify baseUrl is correct

2. **Check API key:**
   - Go to Settings
   - Re-enter API key
   - Save and refresh

3. **Check CORS:**
   - Backend should allow all origins
   - Already configured in your FastAPI code

### High CPU Usage

```cmd
:: Reduce workers in server.py
:: Change from:
workers=2
:: To:
workers=1
```

### Service Crashes Frequently

1. **Check logs for errors:**
   ```cmd
   type C:\nas-server\logs\error.log
   ```

2. **Increase service restart delay:**
   ```cmd
   nssm set NASServer AppThrottle 10000
   nssm set NASServer AppRestartDelay 5000
   ```

---

## 🎯 Part 12: Best Practices & Security

### Security Checklist

- ✅ Use strong API key (32+ characters, random)
- ✅ Enable authentication (`ENABLE_AUTH=true`)
- ✅ Don't expose port 8000 to public internet
- ✅ Use Tailscale for remote access (not port forwarding)
- ✅ Keep Windows 11 updated
- ✅ Install antivirus software
- ✅ Regularly backup your storage directory
- ✅ Use strong Windows password
- ✅ Enable BitLocker on SSD (optional)
- ✅ Review Tailscale access logs monthly

### Performance Optimization

**For Old Laptop:**
```env
# In .env file
MAX_UPLOAD_SIZE=52428800  # 50MB
RATE_LIMIT_REQUESTS=30    # Conservative
```

**In server.py:**
```python
workers=1  # Single worker for old hardware
```

**Windows Optimization:**
- Disable unnecessary startup programs
- Run Disk Cleanup monthly
- Defragment HDD (or TRIM SSD) quarterly
- Keep 20%+ free space on system drive

### Backup Strategy

**Weekly Backup:**
1. Copy `C:\nas-storage` to external drive
2. Backup `.env` file securely
3. Export Tailscale configuration

**Automated Backup Script** (`backup.bat`):
```batch
@echo off
set BACKUP_DIR=D:\Backups\%date:~-4,4%-%date:~-10,2%-%date:~-7,2%
mkdir "%BACKUP_DIR%"
xcopy C:\nas-storage "%BACKUP_DIR%\storage" /E /I /Y
copy C:\nas-server\.env "%BACKUP_DIR%\.env"
echo Backup completed: %BACKUP_DIR%
```

Schedule with Task Scheduler to run weekly.

---

## 📊 Part 13: Network Performance Tips

### Optimize Tailscale

```cmd
:: Enable direct connections (reduce relay usage)
tailscale set --accept-routes

:: Check connection quality
tailscale ping 100.x.x.x
```

### Test Network Speed

1. **From main laptop to Lenovo server:**
   - Upload a large file
   - Note upload speed
   - Download the same file
   - Note download speed

2. **Expected Performance:**
   - Direct connection (same network): 50-100 MB/s
   - Tailscale (direct): 20-80 MB/s
   - Tailscale (via relay): 5-20 MB/s

### Improve Speed

- Ensure both devices have good internet connection
- Use 5GHz WiFi instead of 2.4GHz
- Consider ethernet cable for server
- Close bandwidth-heavy applications

---

## ✅ Final Checklist

Before considering deployment complete:

- [ ] Python 3.11+ installed on Lenovo laptop
- [ ] FastAPI server tested locally
- [ ] Frontend interface works at `/app` endpoint
- [ ] `.env` file configured with secure API key
- [ ] NSSM service installed and running
- [ ] Service auto-starts on boot (tested with restart)
- [ ] Windows power settings configured (no sleep)
- [ ] Firewall allows port 8000
- [ ] Tailscale installed on Lenovo laptop
- [ ] Tailscale installed on main laptop and phone
- [ ] All devices connected to same Tailscale network
- [ ] Can access server via Tailscale IP from all devices
- [ ] Frontend baseUrl updated for remote access
- [ ] API key configured in frontend settings
- [ ] Tested all features: browse, upload, search, download
- [ ] Logs directory created and writable
- [ ] Health check script created
- [ ] Backup strategy in place

---

## 🎉 Success!

You now have a production-ready, 24/7 accessible personal NAS server that:
- ✅ Runs continuously on your Lenovo laptop
- ✅ Accessible from anywhere via Tailscale
- ✅ Secure with encryption and authentication
- ✅ Works on laptop and mobile devices
- ✅ Provides access to entire SSD contents
- ✅ Auto-starts on system boot
- ✅ Monitors health and logs activity

**Access URLs:**
- **Local:** http://localhost:8000/app
- **Remote:** http://100.x.x.x:8000/app (your Tailscale IP)
- **Health:** http://100.x.x.x:8000/health

Your engineering project is now deployed at an enterprise-grade level! 🚀