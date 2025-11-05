# Quick Start Guide

Get your Personal FastNAS running in a few minutes.

## For Complete Beginners (Non-Tech)

### What You Need

- Old laptop (Windows, Mac, or Linux)
- A few minutes

### Steps

#### Download Everything

**Option A: Download ZIP**

1. Click the green "Code" button at top of the page
2. Click "Download ZIP"
3. Unzip the folder

**Option B: Use Git** (if you know how)

```bash
git clone https://github.com/adityaa05/personal-fastNAS.git
```

#### Install Python

If you don't have Python, download from https://www.python.org/downloads/

IMPORTANT: Check "Add Python to PATH" during installation on Windows.

Verify:

```bash
python --version
```

Should show: `Python 3.11` or higher

#### Quick Setup (Copy & Paste)

Open Terminal (Mac/Linux) or Command Prompt (Windows) in the project folder.

**All Platforms:**

```bash
# Create virtual environment
python -m venv venv

# Activate it (choose your OS):

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# Install required packages
pip install fastapi uvicorn pillow python-multipart

# Create storage folder
mkdir nas-storage
```

#### Configure (2 Minutes)

1. Copy the example file:

```bash
# Windows:
copy .env.example .env

# Mac/Linux:
cp .env.example .env
```

2. Edit the `.env` file and set `NAS_BASE_DIR` and `API_KEY`.

Example:

```env
NAS_BASE_DIR=C:\nas-storage
API_KEY=my-super-secret-password-12345
ENABLE_AUTH=true
```

#### Run It

```bash
python main.py
```

You should see server logs indicating Uvicorn is running.

#### Access Your NAS

Open browser and go to: `http://localhost:8000/app`

---

## Access From Phone or Other Devices

### Using Tailscale (Easiest & Secure)

1. Install Tailscale on your NAS laptop and on client devices.
2. Sign in with the same account on all devices.
3. On the NAS laptop run:

```bash
tailscale ip -4
```

4. Open browser on a client and go to: `http://<TAILSCALE-IP>:8000/app`
5. In the app Settings enter the Server URL and API Key from `.env`.

---

## Running as a Windows Service

For 24/7 operation on Windows, you can set up the NAS server as a Windows Service using NSSM.

### Method 1: Using NSSM (Recommended - Easiest)

1. **Download & Install NSSM**

   - Go to https://nssm.cc/download
   - Download NSSM 2.24
   - Extract to `C:\nssm`

2. **Create Server Script**
   - Create a new file named `server.py` in your NAS folder
   - Copy this code into it:

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

3. **Prepare Log Directory**

   ```cmd
   mkdir logs
   ```

4. **Create the Windows Service**

   - Open Command Prompt as Administrator
   - Run these commands:

   ```cmd
   cd C:\nssm\win64
   nssm install NASServer
   ```

   When the NSSM window opens, set these options:

   In "Application":

   - Path: Select your Python from venv (e.g., `C:\path\to\personal-fastNAS\venv\Scripts\python.exe`)
   - Directory: Your NAS folder
   - Arguments: `server.py`

   In "Details":

   - Name: Personal NAS Server
   - Start: Automatic

   In "I/O":

   - Output: `logs\output.log`
   - Error: `logs\error.log`

5. **Start Everything**

   ```cmd
   nssm start NASServer
   ```

6. **Useful Commands**

   ```cmd
   # Check if it's running
   nssm status NASServer

   # Stop the server
   nssm stop NASServer

   # Restart
   nssm restart NASServer

   # Remove if needed
   nssm remove NASServer confirm
   ```

7. **Check the Logs**
   ```cmd
   type logs\output.log
   type logs\error.log
   ```

You can also use Windows Services (type `services.msc` in Run) to manage the service.

---

## Common First-Time Issues

"Python is not recognized"

- Reinstall Python and check "Add Python to PATH"

"Port 8000 is already in use"

- Find and stop the process or change the port in `main.py`.

"401 Unauthorized"

- Re-enter the API key in the app Settings and ensure `.env` is correct.

Can't connect via Tailscale

- Ensure Tailscale is running on both devices and the server is up.

---

## What to Do Next

If you want basic local storage, you're done. For more advanced setup, see `README.md` sections on running as a service and securing the server.

### Keep Your Server Running

- Configure the system service (see README) for 24/7 uptime.

### Secure It Better

1. Generate a strong API key: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Update `.env` and restart server.

---

## Using on Phone

1. Install Tailscale and sign in
2. Open browser and go to: `http://YOUR-LAPTOP-IP:8000/app`

---

## Pro Tips

- Upload multiple files via drag and drop
- Search by typing at least 2 characters and pressing Enter
- Check storage in the app's Storage view

---

## Need Help?

1. Read the full `README.md`
2. Check the Troubleshooting section
3. Open an Issue on GitHub

---

## Quick Reference Commands

```bash
# Start server
python main.py

# Stop server
Ctrl+C

# Check if server is running
curl http://localhost:8000/health

# Generate API key
python -c "import secrets; print(secrets.token_hex(32))"

# Get Tailscale IP
tailscale ip -4
```

---

That's it. You now have your own private cloud.

[Back to README](README.md)
