# ATM Merchant Onboarding App

A web app that collects merchant info via a form, generates all 8 onboarding documents, and emails them to the right people automatically.

---

## What It Does

1. Merchant fills out a 4-step intake form at your URL
2. App generates all 8 documents instantly
3. **Merchant receives** (via email): LLC Filing Guide, EIN Answer Sheet, Banking Relationship Letter, Onboarding Checklist, Cover Sheet
4. **You receive** (at documents@acmeatm.com): Exhibit 2, Exhibit 3, W-9

---

## Deployment on Railway (Recommended)

### Step 1 — GitHub
1. Create a free account at github.com
2. Create a new repository called `atm-onboarding`
3. Upload all files in this folder to the repository

### Step 2 — Railway
1. Create a free account at railway.app
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `atm-onboarding` repository
4. Railway will detect the Procfile and deploy automatically

### Step 3 — Environment Variables
In Railway, go to your project → **Variables** tab and add:

| Variable     | Value                          |
|-------------|-------------------------------|
| `SMTP_HOST` | `smtp.sendgrid.net`           |
| `SMTP_PORT` | `587`                         |
| `SMTP_USER` | `apikey`                      |
| `SMTP_PASS` | *(your SendGrid API key)*     |
| `FROM_EMAIL` | `noreply@acmeatm.com`        |

### Step 4 — SendGrid (Free Email)
1. Create a free account at sendgrid.com
2. Go to **Settings** → **API Keys** → **Create API Key**
3. Give it Full Access, copy the key
4. Paste it as `SMTP_PASS` in Railway
5. In SendGrid, go to **Settings** → **Sender Authentication** and verify `acmeatm.com` or use a single sender email

### Step 5 — Custom Domain (Optional)
In Railway → **Settings** → **Domains** → add `onboarding.acmeatm.com`
Then add a CNAME record at your domain registrar pointing to the Railway URL.

---

## Files Required on Server

All these files must be in the same folder:

```
app.py
merchant_onboarding.py
generate_llc_guide.py
generate_bank_letter.js
generate_ein_sheet.js
generate_cover_sheet.js
Exhibit2.pdf
Exhibit3.pdf
W9.pdf
requirements.txt
Procfile
nixpacks.toml
templates/
  index.html
```

---

## Local Testing

```bash
pip install flask reportlab pypdf python-docx
npm install docx
python app.py
```

Open http://localhost:5000

To test without email (emails are skipped if SMTP_PASS is not set):
```bash
python app.py
```

---

## Environment Variables Reference

| Variable     | Description                          | Required |
|-------------|--------------------------------------|----------|
| `SMTP_HOST` | SMTP server hostname                  | Yes      |
| `SMTP_PORT` | SMTP port (587 for TLS)               | Yes      |
| `SMTP_USER` | SMTP username (`apikey` for SendGrid) | Yes      |
| `SMTP_PASS` | SMTP password / SendGrid API key      | Yes      |
| `FROM_EMAIL` | Sender email address                 | Yes      |
| `PORT`      | Port to run on (set by Railway auto)  | Auto     |
