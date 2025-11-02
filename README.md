# Patient Management System (PMS)
This is a minimal Patient Management System built with Flask, MongoDB and Stripe (Checkout).
It includes:
- Add / Edit / Delete patients
- Create appointments
- Create invoice and pay via Stripe Checkout
- Simple Bootstrap frontend

## Setup (local)
1. Create a Python venv and install requirements:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill values (do NOT commit secrets).
3. Run locally:
   ```
   python app.py
   ```
4. For webhooks testing, use `stripe-cli` to forward events to `/webhook/stripe`.

## Deploying to Render
- Push this repo to GitHub.
- Create a new Web Service on Render connected to the repo.
- Add env vars: MONGO_URI, SECRET_KEY, STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET (optional), BASE_URL.
- Start command (Render): `gunicorn app:app --bind 0.0.0.0:$PORT`
