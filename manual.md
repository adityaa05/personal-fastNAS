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
