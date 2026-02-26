"""
ATM Merchant Onboarding Web App
- Merchants fill out intake form
- Documents generated on submit
- Merchant emailed: LLC Guide, EIN Sheet, Bank Letter, Checklist, Cover Sheet
- You emailed: Exhibit 2, Exhibit 3, W-9
"""

import os
import sys
import json
import uuid
import shutil
import smtplib
import zipfile
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, request, render_template, jsonify, send_from_directory

# Add app dir to path so generator modules resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
ADMIN_EMAIL     = "documents@acmeatm.com"
SMTP_HOST       = os.environ.get("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT       = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER       = os.environ.get("SMTP_USER", "apikey")
SMTP_PASS       = os.environ.get("SMTP_PASS", "")      # set in Railway env vars
FROM_EMAIL      = os.environ.get("FROM_EMAIL", "noreply@acmeatm.com")
OUTPUT_BASE_DIR = os.path.join(os.path.dirname(__file__), "output_docs")
SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))

os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

STATES = [
    ("AL","Alabama"),("AK","Alaska"),("AZ","Arizona"),("CA","California"),
    ("CO","Colorado"),("CT","Connecticut"),("DE","Delaware"),("FL","Florida"),
    ("GA","Georgia"),("HI","Hawaii"),("ID","Idaho"),("IL","Illinois"),
    ("IN","Indiana"),("IA","Iowa"),("KS","Kansas"),("KY","Kentucky"),
    ("LA","Louisiana"),("MD","Maryland"),("MA","Massachusetts"),("MI","Michigan"),
    ("MN","Minnesota"),("MO","Missouri"),("MT","Montana"),("NE","Nebraska"),
    ("NV","Nevada"),("NJ","New Jersey"),("NY","New York"),("NC","North Carolina"),
    ("OH","Ohio"),("PA","Pennsylvania"),("TX","Texas"),("WA","Washington"),
]

# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", states=STATES)


@app.route("/submit", methods=["POST"])
def submit():
    try:
        form = request.form

        today = datetime.today().strftime("%m/%d/%Y")

        data = {
            "date": today,
            "merchant": {
                "company_name":       form["company_name"],
                "dba_name":           form.get("dba_name", form["company_name"]),
                "entity_creator_name": form["owner_name"],
                "title":              form.get("title", "Managing Member"),
                "company_address":    form["company_address"],
                "company_city":       form["company_city"],
                "company_state":      form["company_state"],
                "company_zip":        form["company_zip"],
                "location_address":   form.get("location_address", form["company_address"]),
                "location_city":      form.get("location_city", form["company_city"]),
                "location_state":     form.get("location_state", form["company_state"]),
                "location_zip":       form.get("location_zip", form["company_zip"]),
                "location_phone":     form["phone"],
                "fein":               form.get("fein", ""),
                "email":              form["merchant_email"],
                "ssn":                form.get("ssn", ""),
                "business_type":      "LLC",
                "merchandise_services": "ATM Services",
                "date_of_incorporation": form.get("date_of_incorporation", ""),
            },
            "bank": {
                "bank_name":      form.get("bank_name", ""),
                "routing_number": form.get("routing_number", ""),
                "account_number": form.get("account_number", ""),
            }
        }

        # Create unique output folder for this submission
        job_id     = uuid.uuid4().hex[:8]
        slug       = data["merchant"]["company_name"].replace(" ", "_").replace(",", "")
        output_dir = os.path.join(OUTPUT_BASE_DIR, f"{job_id}_{slug}")
        os.makedirs(output_dir, exist_ok=True)

        # Write merchant JSON for the generator
        json_path = os.path.join(output_dir, "merchant_data.json")
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

        # ── Generate all documents ────────────────────────────────────────
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "merchant_onboarding.py"),
             json_path, output_dir],
            capture_output=True, text=True, cwd=SCRIPT_DIR
        )

        if result.returncode != 0:
            app.logger.error(f"Generation error: {result.stderr}")
            return jsonify({"success": False, "error": "Document generation failed. Please try again."}), 500

        # ── Find generated files ──────────────────────────────────────────
        files = {f: os.path.join(output_dir, f) for f in os.listdir(output_dir)
                 if f.endswith(('.pdf', '.docx', '.txt'))}

        # Categorize
        merchant_files = []
        admin_files    = []

        for fname, fpath in files.items():
            lower = fname.lower()
            if any(x in lower for x in ['exhibit2', 'exhibit3', 'w9']):
                admin_files.append((fname, fpath))
            else:
                merchant_files.append((fname, fpath))

        # ── Send emails ───────────────────────────────────────────────────
        merchant_email = data["merchant"]["email"]
        company_name   = data["merchant"]["company_name"]

        email_errors = []

        if SMTP_PASS:
            # Email to merchant
            try:
                send_email(
                    to=merchant_email,
                    subject=f"Your ATM Onboarding Documents — {company_name}",
                    body=merchant_email_body(company_name, data["merchant"]["entity_creator_name"]),
                    attachments=merchant_files
                )
            except Exception as e:
                email_errors.append(f"Merchant email: {e}")
                app.logger.error(f"Merchant email failed: {e}")

            # Email to admin
            try:
                send_email(
                    to=ADMIN_EMAIL,
                    subject=f"New Merchant Submission — {company_name}",
                    body=admin_email_body(data),
                    attachments=admin_files
                )
            except Exception as e:
                email_errors.append(f"Admin email: {e}")
                app.logger.error(f"Admin email failed: {e}")
        else:
            app.logger.warning("SMTP_PASS not set — emails skipped")

        return jsonify({
            "success": True,
            "company_name": company_name,
            "merchant_email": merchant_email,
            "email_sent": len(email_errors) == 0,
            "email_errors": email_errors,
        })

    except Exception as e:
        app.logger.error(f"Submit error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ── Email helpers ───────────────────────────────────────────────────────────

def send_email(to: str, subject: str, body: str, attachments: list):
    msg = MIMEMultipart()
    msg["From"]    = FROM_EMAIL
    msg["To"]      = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    for fname, fpath in attachments:
        with open(fpath, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{fname}"')
        msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, to, msg.as_string())


def merchant_email_body(company_name: str, owner_name: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #222;">
      <div style="background: #1A3C5E; padding: 24px 32px; border-radius: 6px 6px 0 0;">
        <h2 style="color: #fff; margin: 0; font-size: 20px;">ATM Merchant Onboarding</h2>
      </div>
      <div style="padding: 32px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 6px 6px;">
        <p>Hi {owner_name},</p>
        <p>Thank you for starting the onboarding process for <strong>{company_name}</strong>.
        Please find your onboarding documents attached.</p>

        <p><strong>Your next steps:</strong></p>
        <ol>
          <li>Review the <strong>Cover Sheet</strong> for an overview of the full process</li>
          <li>Follow the <strong>LLC Filing Guide</strong> to register your LLC in your state</li>
          <li>Use the <strong>EIN Answer Sheet</strong> to apply for your EIN at irs.gov/ein</li>
          <li>Bring the <strong>Banking Relationship Letter</strong> to your bank to open a business checking account and get it signed and stamped</li>
          <li>Return the signed Banking Relationship Letter to us when complete</li>
        </ol>

        <p>If you have any questions, reply to this email or contact us directly.</p>
        <p style="margin-top: 32px; color: #666; font-size: 13px;">— ACME ATM Onboarding Team</p>
      </div>
    </div>
    """


def admin_email_body(data: dict) -> str:
    m = data["merchant"]
    today = data.get("date", "")
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #222;">
      <div style="background: #1A3C5E; padding: 24px 32px; border-radius: 6px 6px 0 0;">
        <h2 style="color: #fff; margin: 0; font-size: 20px;">New Merchant Submission</h2>
      </div>
      <div style="padding: 32px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 6px 6px;">
        <table style="width:100%; border-collapse: collapse; font-size: 14px;">
          <tr><td style="padding:6px 0; color:#666; width:160px;">Company</td><td><strong>{m['company_name']}</strong></td></tr>
          <tr><td style="padding:6px 0; color:#666;">Owner</td><td>{m['entity_creator_name']}</td></tr>
          <tr><td style="padding:6px 0; color:#666;">State</td><td>{m['company_state']}</td></tr>
          <tr><td style="padding:6px 0; color:#666;">Email</td><td>{m['email']}</td></tr>
          <tr><td style="padding:6px 0; color:#666;">Phone</td><td>{m['location_phone']}</td></tr>
          <tr><td style="padding:6px 0; color:#666;">Bank</td><td>{data['bank']['bank_name']}</td></tr>
          <tr><td style="padding:6px 0; color:#666;">Submitted</td><td>{today}</td></tr>
        </table>
        <p style="margin-top: 24px;">Exhibit 2, Exhibit 3, and W-9 are attached and ready to submit.</p>
      </div>
    </div>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
