# Smart Billing AI — Deployment Guide

## What's New
- **Single-server deployment**: Backend now serves the frontend HTML/CSS/JS directly — no separate frontend server needed.
- **Secure passwords**: Shop passwords are now hashed with bcrypt.
- **Relative API paths**: Frontend auto-detects when served from the same host and uses relative URLs.
- **Docker support**: One-command containerization.

## Local Development (No Docker)
```bash
pip install -r requirements.txt
python billing_api.py
```
Open http://localhost:8001

## Docker
```bash
docker build -t smart-billing .
docker run -p 8001:8001 smart-billing
```
Open http://localhost:8001

## Render.com (Recommended Free Host)
1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New +** → **Web Service**.
3. Connect your GitHub repo.
4. **Runtime**: Docker
5. **Plan**: Free
6. Click **Deploy**. Render auto-detects the `Dockerfile`.
7. Your app will be live at `https://<your-service>.onrender.com`.

> **Note**: On the free plan, the instance sleeps after 15 min of inactivity. First request may take ~30s to wake up.

## Railway
1. Push repo to GitHub.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. Railway auto-detects the `Dockerfile` and deploys.

## Live Demo
The app is publicly accessible at: **https://billify-cooj.onrender.com**

> Note: On the free Render plan, the instance sleeps after 15 min of inactivity. The first request may take ~30 seconds to wake up.

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `PORT`   | `8001`  | HTTP port the server binds to. Render/Railway override this automatically. |

## Post-Deployment
1. Visit the root URL (`/`).
2. Go to **Signup** → register your shop.
3. Log in and start billing!

