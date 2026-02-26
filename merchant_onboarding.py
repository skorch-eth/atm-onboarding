#!/usr/bin/env python3
"""
Acme ATM Merchant Onboarding Automation
Generates 6 documents from a single JSON input:
  1. Exhibit 2 - ATM Operator / Source of Funds Provider Agreement (PDF)
  2. Exhibit 3 - ACH Authorization Form (PDF)
  3. W-9 - Taxpayer ID Form (PDF)
  4. Onboarding Checklist (TXT)
  5. Banking Relationship Letter (DOCX) — merchant brings to bank visit
  6. EIN Application Answer Sheet (DOCX) — step-by-step guide for IRS online form

Requires generate_bank_letter.js and generate_ein_sheet.js in the same directory.
Node.js must be installed for documents 5 and 6.

Usage:
    python merchant_onboarding.py merchant_data.json [output_dir]
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io
from datetime import date

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


# ─────────────────────────────────────────────
# Source PDF paths (relative to this script)
# ─────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

EXHIBIT2_SRC = os.path.join(SCRIPT_DIR, "Exhibit_2_-_ATM_Operator___Source_of_Funds_Provider_Agreement.PDF")
EXHIBIT3_SRC = os.path.join(SCRIPT_DIR, "Exhibit_3_-_ACH_Authorization_Form.PDF")
W9_SRC       = os.path.join(SCRIPT_DIR, "W-9_Form__Rev__March_2024_.PDF")


# ─────────────────────────────────────────────
# Helper: fill a PDF's form fields
# ─────────────────────────────────────────────
def fill_pdf_fields(src_path: str, field_values: dict) -> PdfWriter:
    """Read src PDF, fill the listed fields, return a PdfWriter."""
    reader = PdfReader(src_path)
    writer = PdfWriter()
    writer.append(reader)

    # Update form fields
    for page in writer.pages:
        writer.update_page_form_field_values(page, field_values, auto_regenerate=False)

    return writer


# ─────────────────────────────────────────────
# Helper: overlay text on top of a PDF page
# ─────────────────────────────────────────────
def make_overlay(page_width: float, page_height: float, items: list) -> io.BytesIO:
    """
    Create a reportlab overlay canvas.
    items: list of dicts with keys:
      - x, y: position in PDF points (y=0 at bottom)
      - text: string to draw
      - font: font name (default Helvetica)
      - size: font size (default 9)
      - color: (r, g, b) tuple 0-1 (default black)
    Returns a BytesIO PDF buffer.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))

    for item in items:
        font = item.get("font", "Helvetica")
        size = item.get("size", 9)
        color = item.get("color", (0, 0, 0))
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        c.drawString(item["x"], item["y"], item["text"])

    c.save()
    buf.seek(0)
    return buf


def merge_overlay(writer: PdfWriter, page_index: int, overlay_buf: io.BytesIO):
    """Merge an overlay PDF page onto the given page of the writer."""
    overlay_reader = PdfReader(overlay_buf)
    overlay_page = overlay_reader.pages[0]
    writer.pages[page_index].merge_page(overlay_page)


# ─────────────────────────────────────────────
# State LLC database (32 states)
# ─────────────────────────────────────────────
STATE_LLC_DB = {
    "AL": {"agency": "Alabama Secretary of State", "url": "https://www.sos.alabama.gov", "fee": "$200", "form": "Certificate of Formation", "online": True},
    "AK": {"agency": "Alaska Division of Corporations", "url": "https://www.commerce.alaska.gov/web/cbpl/BusinessLicensing.aspx", "fee": "$250", "form": "Articles of Organization", "online": True},
    "AZ": {"agency": "Arizona Corporation Commission", "url": "https://azcc.gov", "fee": "$50", "form": "Articles of Organization", "online": True},
    "CA": {"agency": "California Secretary of State", "url": "https://bizfileonline.sos.ca.gov", "fee": "$70", "form": "Articles of Organization (LLC-1)", "online": True},
    "CO": {"agency": "Colorado Secretary of State", "url": "https://www.sos.state.co.us", "fee": "$50", "form": "Articles of Organization", "online": True},
    "CT": {"agency": "Connecticut Secretary of State", "url": "https://business.ct.gov", "fee": "$120", "form": "Certificate of Organization", "online": True},
    "DE": {"agency": "Delaware Division of Corporations", "url": "https://icis.corp.delaware.gov", "fee": "$110", "form": "Certificate of Formation", "online": True},
    "FL": {"agency": "Florida Division of Corporations", "url": "https://dos.myflorida.com/sunbiz", "fee": "$125", "form": "Articles of Organization", "online": True},
    "GA": {"agency": "Georgia Secretary of State", "url": "https://sos.ga.gov/business-services-division", "fee": "$100", "form": "Articles of Organization", "online": True},
    "HI": {"agency": "Hawaii Department of Commerce", "url": "https://cca.hawaii.gov/breg", "fee": "$50", "form": "Articles of Organization", "online": True},
    "ID": {"agency": "Idaho Secretary of State", "url": "https://sos.idaho.gov", "fee": "$100", "form": "Certificate of Organization", "online": True},
    "IL": {"agency": "Illinois Secretary of State", "url": "https://www.ilsos.gov/departments/business_services", "fee": "$150", "form": "Articles of Organization (LLC-5.5)", "online": True},
    "IN": {"agency": "Indiana Secretary of State", "url": "https://inbiz.in.gov", "fee": "$98", "form": "Articles of Organization", "online": True},
    "IA": {"agency": "Iowa Secretary of State", "url": "https://sos.iowa.gov", "fee": "$50", "form": "Certificate of Organization", "online": True},
    "KS": {"agency": "Kansas Secretary of State", "url": "https://sos.ks.gov", "fee": "$165", "form": "Articles of Organization", "online": True},
    "KY": {"agency": "Kentucky Secretary of State", "url": "https://sos.ky.gov/bus/business-filings", "fee": "$90", "form": "Articles of Organization", "online": True},
    "LA": {"agency": "Louisiana Secretary of State", "url": "https://www.sos.la.gov", "fee": "$100", "form": "Articles of Organization", "online": True},
    "MD": {"agency": "Maryland State Department of Assessments and Taxation", "url": "https://dat.maryland.gov", "fee": "$100", "form": "Articles of Organization", "online": True},
    "MA": {"agency": "Massachusetts Secretary of State", "url": "https://corp.sec.state.ma.us", "fee": "$500", "form": "Certificate of Organization", "online": True},
    "MI": {"agency": "Michigan Department of Licensing and Regulatory Affairs", "url": "https://www.michigan.gov/lara", "fee": "$50", "form": "Articles of Organization", "online": True},
    "MN": {"agency": "Minnesota Secretary of State", "url": "https://www.sos.state.mn.us", "fee": "$135", "form": "Articles of Organization", "online": True},
    "MO": {"agency": "Missouri Secretary of State", "url": "https://www.sos.mo.gov/business", "fee": "$50", "form": "Articles of Organization", "online": True},
    "MT": {"agency": "Montana Secretary of State", "url": "https://sosmt.gov", "fee": "$70", "form": "Articles of Organization", "online": True},
    "NE": {"agency": "Nebraska Secretary of State", "url": "https://sos.nebraska.gov", "fee": "$110", "form": "Certificate of Organization", "online": True},
    "NV": {"agency": "Nevada Secretary of State", "url": "https://esos.nv.gov", "fee": "$425", "form": "Articles of Organization", "online": True},
    "NJ": {"agency": "New Jersey Division of Revenue", "url": "https://www.njportal.com/dor/businessformation", "fee": "$125", "form": "Public Records Filing for New Business Entity", "online": True},
    "NY": {"agency": "New York Department of State", "url": "https://www.dos.ny.gov/corps", "fee": "$200", "form": "Articles of Organization", "online": True},
    "NC": {"agency": "North Carolina Secretary of State", "url": "https://www.sosnc.gov", "fee": "$125", "form": "Articles of Organization", "online": True},
    "OH": {"agency": "Ohio Secretary of State", "url": "https://www.ohiosos.gov", "fee": "$99", "form": "Articles of Organization", "online": True},
    "PA": {"agency": "Pennsylvania Department of State", "url": "https://www.dos.pa.gov/business", "fee": "$125", "form": "Certificate of Organization", "online": True},
    "TX": {"agency": "Texas Secretary of State", "url": "https://www.sos.state.tx.us/corp/forms_boc.shtml", "fee": "$300", "form": "Certificate of Formation (Form 205)", "online": True},
    "WA": {"agency": "Washington Secretary of State", "url": "https://ccfs.sos.wa.gov", "fee": "$200", "form": "Certificate of Formation", "online": True},
}


# ─────────────────────────────────────────────
# EXHIBIT 2
# ─────────────────────────────────────────────
def generate_exhibit2(data: dict, output_path: str):
    """Fill and output Exhibit 2 PDF."""
    m = data["merchant"]
    sig_name = m["entity_creator_name"]
    today = data.get("date", date.today().strftime("%m/%d/%Y"))

    # Section A: Terminal Deployment Location (fields 1-7)
    # Section D: Company/Applicant info (fields 18-24)
    # Signature section

    field_values = {
        # Section A
        "1 Name of Location Doing Business As":
            m.get("dba_name", m["company_name"]),
        "2 Physical Street Address of Location":
            m["location_address"],
        "3 C ty State Zip of Location":
            f"{m['location_city']}, {m['location_state']} {m['location_zip']}",
        "4 Location Phone Number":
            m["location_phone"],
        "5 Business Tax ID Number of Merchant":
            m["fein"],
        "6 Type of Business (Sole Proprietor, Partnership, LLC, Corp, Financial Institution)":
            m.get("business_type", "LLC"),
        "7 MerchandiseServ ces Sold where terminal is deployed":
            m.get("merchandise_services", "ATM Services"),

        # Section D: Company info (fields 18-23)
        "18 Company Legal Name as stated on Articles of Incorporation":
            m["company_name"],
        "19 Company Address as stated on Articles of Incorporation":
            m["company_address"],
        "20 Company City State Zip as stated on Articles of Incorporation":
            f"{m['company_city']}, {m['company_state']} {m['company_zip']}",
        # Field 21 (FEIN) has no text box — will be overlaid below
        "22. Company Date of Incorporation":
            m.get("date_of_incorporation", ""),
        "23. Company State of Incorporation":
            m["company_state"],

        # Entity Type dropdown: L = Limited Liability Company
        "Entity Type": "L",

        # Section D checkboxes: Select "Applicant is a Company" radio (/1)
        # and "Both ATM Operator and ATM Source of Funds Provider" (/2)
        "Group1": "/1",   # Applicant is a Company
        "Group2": "/2",   # Both ATM Operator and Source of Funds Provider

        # Business Tax ID checkbox (for Section D row)
        "Business TaxID": "/Yes",

        # Signature of ATM Operator — we use an overlay for the styled italic blue sig,
        # so leave this fillable field blank to avoid double rendering.
        # "Signature of ATM OperatorATM Source of Funds Provider": "",
        # "Signature": "",
        "Name": sig_name,
        "TitleDate": f"{m.get('title', 'Owner')} / {today}",
    }

    writer = fill_pdf_fields(EXHIBIT2_SRC, field_values)

    # ── Overlay: Field 21 FEIN (no fillable text box exists) ──
    # Also render the signature in italic dark blue
    # PDF page dimensions (letter = 612 x 792)
    page = writer.pages[0]
    pw = float(page.mediabox.width)
    ph = float(page.mediabox.height)

    # The field 21 rect in the original is approx [311.4, 316.56, 606.48, 330.6]
    # That's in PDF coords where y=0 is bottom.
    # We need to place text just inside that box.
    fein_x = 315.0
    fein_y = 320.0  # slightly above the bottom of the cell

    # Signature overlay (italic dark blue) — Signature field rect y≈75-87
    sig_x = 20.0
    sig_y = 79.0

    overlay_items = [
        # FEIN text
        {
            "x": fein_x, "y": fein_y,
            "text": m["fein"],
            "font": "Helvetica", "size": 9,
            "color": (0, 0, 0)
        },
        # E-signature in italic dark blue
        {
            "x": sig_x, "y": sig_y,
            "text": sig_name,
            "font": "Helvetica-Oblique", "size": 10,
            "color": (0, 0, 0.5)
        },
    ]

    overlay_buf = make_overlay(pw, ph, overlay_items)
    merge_overlay(writer, 0, overlay_buf)

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"  ✓ Exhibit 2 → {output_path}")


# ─────────────────────────────────────────────
# EXHIBIT 3
# ─────────────────────────────────────────────
def generate_exhibit3(data: dict, output_path: str):
    """Fill and output Exhibit 3 ACH Authorization Form PDF."""
    m = data["merchant"]
    b = data["bank"]
    today = data.get("date", date.today().strftime("%m/%d/%Y"))
    sig_name = m["entity_creator_name"]

    # Field mapping (from extracted field IDs):
    # Text1 = Location Name (≈ company name)
    # 3     = Contact
    # 2     = Address
    # 4     = City, 5 = State, 6 = Zip (actually State), 7 = Phone#
    # Wait — let me map carefully:
    #   field "4"  rect [57.75, 621, 226.5, 637.5]  → City
    #   field "5"  rect [256.5, 621, 303, 638.25]   → State  (but labeled "State" in form)
    #   field "6"  rect [324.75, 620.25, 381, 637.5] → Zip   (but labeled "Zip")
    #   field "7"  rect [423, 621, 572.25, 637.5]   → Phone#
    # Actually from the image: City | State | Zip | Phone# across one row.
    # "5" is very narrow — that's State. "6" is also narrow — that's Zip.
    # Let's trust the layout.

    # Legal name in the authorization paragraph:
    # field "Text3" rect [35.88, 582.62, 198.51, 597.1] — the blank line before ", legal name"
    # field "3"     rect [431.25, 658.5, 571.5, 676.5]  — Contact (right of Location Name row)

    # Bottom section:
    # field "11" = Print Name  rect [90.75, 274.5, 435, 291]
    # field "12" = Date        rect [461.25, 273.75, 574.5, 293.25]
    # field "13" = Signature   rect [81, 252, 469.5, 270.75]
    # field "15" = Bank Name   rect [360, 223.5, 575.25, 238.5]
    # field "14" = Name on Account  rect [116.25, 222.75, 303, 240.75]
    # field "16" = City (bank address row — but spec says NO bank address)
    # field "17" = City (bank addr), "18" = State, "19" = Zip — SKIP per spec
    # field "20" = Routing #   rect [38.25, 144.387, 262.5, 162.387]
    # field "21" = Account #   rect [270.75, 144, 570.75, 162.75]
    # field "25" = User Name (PAI reports)  rect [88.5, 100.5, 291.75, 119.25]
    # field "30" = Email       rect [323.25, 99, 573.75, 117]

    # CheckBox1 = Vault Cash, CheckBox2 = Surcharge, CheckBox3 = Wireless
    # CheckBox4 = Yes (changing acct), CheckBox5 = No (changing acct) — SKIP per spec
    # CheckBox6 = Checking, CheckBox7 = Savings
    # CheckBox8 = Lumped,   CheckBox9 = Separate

    field_values = {
        # Header checkboxes — we leave Vault Cash/Surcharge/Wireless unchecked
        # (or set per data if present)

        # Location info
        "Text1": m.get("dba_name", m["company_name"]),  # Location Name
        "3":     m["entity_creator_name"],               # Contact
        "2":     m["location_address"],                  # Address
        "4":     m["location_city"],                     # City
        "5":     m["location_state"],                    # State
        "6":     m["location_zip"],                      # Zip
        "7":     m["location_phone"],                    # Phone#

        # Legal name in body paragraph
        "Text3": m["company_name"],

        # Signature block
        "11":    sig_name,           # Print Name
        "12":    today,              # Date
        # field "13" = Signature — we'll overlay italic blue (see below)

        # Bank section
        "14":    m["company_name"],  # Name on Account
        "15":    b["bank_name"],     # Bank Name
        # NO bank address fields per spec

        # Account type: Checking=CheckBox6, Lumped=CheckBox8
        "CheckBox6": "/Yes",  # Checking
        "CheckBox8": "/Yes",  # Lumped

        # Routing and Account numbers
        "20": b["routing_number"],
        "21": b["account_number"],

        # PAI Reports section (optional)
        "25": m.get("pai_username", ""),
        "30": m.get("email", ""),
    }

    writer = fill_pdf_fields(EXHIBIT3_SRC, field_values)

    # Overlay: e-signature in italic dark blue on the Signature line
    page = writer.pages[0]
    pw = float(page.mediabox.width)
    ph = float(page.mediabox.height)

    # Field "13" rect: [81, 252, 469.5, 270.75] — y in PDF coords (0=bottom)
    sig_x = 84.0
    sig_y = 256.0

    overlay_items = [
        {
            "x": sig_x, "y": sig_y,
            "text": sig_name,
            "font": "Helvetica-Oblique", "size": 10,
            "color": (0, 0, 0.5)
        },
    ]

    overlay_buf = make_overlay(pw, ph, overlay_items)
    merge_overlay(writer, 0, overlay_buf)

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"  ✓ Exhibit 3 → {output_path}")


# ─────────────────────────────────────────────
# W-9
# ─────────────────────────────────────────────
def generate_w9(data: dict, output_path: str):
    """Fill and output W-9 PDF."""
    m = data["merchant"]
    today = data.get("date", date.today().strftime("%m/%d/%Y"))
    sig_name = m["entity_creator_name"]

    # Parse FEIN into two parts: XX-XXXXXXX → part1="XX", part2="XXXXXXX"
    fein_raw = m["fein"].replace("-", "")
    fein_part1 = fein_raw[:2] if len(fein_raw) >= 2 else fein_raw
    fein_part2 = fein_raw[2:] if len(fein_raw) > 2 else ""

    # W-9 field IDs (from extracted w9_fields.json):
    # f1_01 = Line 1 entity name
    # f1_02 = Line 2 (business/DBA name, if different)
    # c1_1[0]=Individual, [1]=C corp, [2]=S corp, [3]=Partnership, [4]=Trust/estate, [5]=LLC checkbox, [6]=Other
    # f1_03 = LLC tax classification entry (C/S/P)
    # c1_2[0] = Line 3b checkbox
    # f1_07 = Line 5 address
    # f1_08 = Line 6 city/state/zip
    # f1_11, f1_12, f1_13 = SSN boxes (3 parts — skip for LLC/EIN)
    # f1_14, f1_15 = EIN parts (XX and XXXXXXX)
    # Signature and date are NOT standard form fields on the W-9 —
    #   the "Sign Here" section uses overlay

    field_values = {
        "topmostSubform[0].Page1[0].f1_01[0]": m["company_name"],       # Line 1
        # Line 2 left blank (no DBA different from company name)
        # Line 3a: LLC checkbox (index 5 = LLC)
        "topmostSubform[0].Page1[0].Boxes3a-b_ReadOrder[0].c1_1[5]": "/6",
        # LLC tax classification: P (single-member treated as partnership) or as specified
        "topmostSubform[0].Page1[0].Boxes3a-b_ReadOrder[0].f1_03[0]": m.get("llc_tax_class", ""),
        # Line 5 address
        "topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_07[0]": m["company_address"],
        # Line 6 city, state, zip
        "topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_08[0]":
            f"{m['company_city']}, {m['company_state']} {m['company_zip']}",
        # EIN (two-part field)
        "topmostSubform[0].Page1[0].f1_14[0]": fein_part1,
        "topmostSubform[0].Page1[0].f1_15[0]": fein_part2,
    }

    writer = fill_pdf_fields(W9_SRC, field_values)

    # Overlay: e-signature + date on Sign Here line
    # The W-9 "Sign Here" area is near the bottom of the form.
    # From the image, the signature line appears around y=355-370 in PDF coords.
    # "Signature of U.S. person" label is at roughly y≈368, and the date is to the right.
    page = writer.pages[0]
    pw = float(page.mediabox.width)
    ph = float(page.mediabox.height)

    # Sign Here line is at approximately image y=740 out of 1000px tall image.
    # PDF page height=792, image height=1000.
    # pdf_y = (1000 - image_y) * (792 / 1000) = (1000-740)*0.792 = 205.9
    overlay_items = [
        # Signature on Sign Here line
        {
            "x": 120.0, "y": 208.0,
            "text": sig_name,
            "font": "Helvetica-Oblique", "size": 11,
            "color": (0, 0, 0.5)
        },
        # Date to the right of signature
        {
            "x": 490.0, "y": 208.0,
            "text": today,
            "font": "Helvetica", "size": 9,
            "color": (0, 0, 0)
        },
    ]

    overlay_buf = make_overlay(pw, ph, overlay_items)
    merge_overlay(writer, 0, overlay_buf)

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"  ✓ W-9       → {output_path}")


# ─────────────────────────────────────────────
# ONBOARDING CHECKLIST (TXT)
# ─────────────────────────────────────────────
def generate_checklist(data: dict, output_path: str):
    """Generate the onboarding checklist text file."""
    m = data["merchant"]
    b = data["bank"]
    state = m["company_state"]
    today = data.get("date", date.today().strftime("%m/%d/%Y"))
    company = m["company_name"]

    # Lookup state LLC info
    llc_info = STATE_LLC_DB.get(state, None)

    lines = []
    lines.append("=" * 70)
    lines.append(f"  ACME ATM MERCHANT ONBOARDING CHECKLIST")
    lines.append(f"  Merchant: {company}")
    lines.append(f"  Date: {today}")
    lines.append("=" * 70)
    lines.append("")

    # ── SECTION 1: State LLC Filing ──────────────────────────────────────
    lines.append("SECTION 1: STATE LLC FILING INSTRUCTIONS")
    lines.append("-" * 50)
    if llc_info:
        lines.append(f"State: {state}")
        lines.append(f"Filing Agency: {llc_info['agency']}")
        lines.append(f"Website: {llc_info['url']}")
        lines.append(f"Filing Fee: {llc_info['fee']}")
        lines.append(f"Form Name: {llc_info['form']}")
        lines.append(f"Online Filing Available: {'Yes' if llc_info['online'] else 'No'}")
        lines.append("")
        lines.append("Steps to file:")
        lines.append(f"  1. Go to {llc_info['url']}")
        lines.append(f"  2. Navigate to 'Business Filings' or 'Form an LLC'")
        lines.append(f"  3. Complete the {llc_info['form']}")
        lines.append(f"     - Entity name: {company}")
        lines.append(f"     - Registered Agent required in {state}")
        lines.append(f"  4. Pay the filing fee: {llc_info['fee']}")
        lines.append(f"  5. Download and save your Certificate/Articles once approved")
        lines.append(f"  6. Order a Certified Copy — required for bank account opening")
    else:
        lines.append(f"State '{state}' not found in database.")
        lines.append("Please consult your state's Secretary of State website.")
    lines.append("")

    # ── SECTION 2: EIN Walkthrough ────────────────────────────────────────
    lines.append("SECTION 2: EIN (EMPLOYER IDENTIFICATION NUMBER) WALKTHROUGH")
    lines.append("-" * 50)
    if m.get("fein"):
        lines.append(f"  EIN on file: {m['fein']}")
        lines.append("  ✓ EIN already obtained — no action needed.")
    else:
        lines.append("  EIN not yet obtained. Follow these steps:")
        lines.append("")
        lines.append("  1. Go to: https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online")
        lines.append("  2. Click 'Apply Online Now' (Mon–Fri 7am–10pm ET)")
        lines.append("  3. Select 'Limited Liability Company' as entity type")
        lines.append(f"  4. Enter company name exactly: {company}")
        lines.append(f"  5. Enter registered state: {state}")
        lines.append("  6. Complete the responsible party information")
        lines.append("  7. Your EIN will be issued immediately")
        lines.append("  8. Print/save the EIN confirmation letter (CP575)")
        lines.append("     — Required for bank account opening")
    lines.append("")

    # ── SECTION 3: Bank Visit Script ─────────────────────────────────────
    lines.append("SECTION 3: BANK VISIT SCRIPT")
    lines.append("-" * 50)
    lines.append(f"  Target Bank: {b.get('bank_name', '[Your Bank]')}")
    lines.append("")
    lines.append("  Documents to bring:")
    lines.append("    □ LLC Articles of Organization / Certificate of Formation")
    lines.append("    □ Certified copy of Articles (if required by bank)")
    lines.append("    □ EIN Confirmation Letter (IRS Form CP575)")
    lines.append("    □ Government-issued photo ID (all members present)")
    lines.append("    □ Operating Agreement (bank may require)")
    lines.append("    □ Initial deposit (ask branch for minimum)")
    lines.append("")
    lines.append("  Talking points at the bank:")
    lines.append(f"    • 'I'd like to open a business checking account for {company}, an LLC.'")
    lines.append(f"    • 'We are an ATM operator and will need ACH debit/credit capability.'")
    lines.append(f"    • 'We need the routing and account numbers for our ACH Authorization Form.'")
    lines.append(f"    • 'Please confirm the account supports same-day ACH if possible.'")
    lines.append("")
    lines.append("  Information to collect at the bank:")
    lines.append(f"    □ Bank Name: {b.get('bank_name', '________________')}")
    lines.append(f"    □ Routing Number: {b.get('routing_number', '________________')}")
    lines.append(f"    □ Account Number: {b.get('account_number', '________________')}")
    lines.append(f"    □ Account Type: Checking")
    lines.append("")

    # ── SECTION 4: Timeline ───────────────────────────────────────────────
    lines.append("SECTION 4: ONBOARDING TIMELINE")
    lines.append("-" * 50)
    lines.append("  Week 1:")
    lines.append("    □ File LLC with state (online if available)")
    lines.append("    □ Obtain EIN from IRS (same day, online)")
    lines.append("    □ Draft Operating Agreement")
    lines.append("")
    lines.append("  Week 2:")
    lines.append("    □ Receive LLC approval documents from state")
    lines.append("    □ Open business bank account")
    lines.append("    □ Collect routing and account numbers")
    lines.append("")
    lines.append("  Week 3:")
    lines.append("    □ Complete and sign Exhibit 2 (ATM Operator Agreement)")
    lines.append("    □ Complete and sign Exhibit 3 (ACH Authorization Form)")
    lines.append("    □ Complete and sign W-9")
    lines.append("    □ Submit full packet to PAI/ISO")
    lines.append("")
    lines.append("  Week 4+:")
    lines.append("    □ Await approval from Pathward National Association")
    lines.append("    □ Arrange ATM terminal deployment at location")
    lines.append("    □ Confirm terminal ID and processor info")
    lines.append("")
    lines.append("=" * 70)
    lines.append("  Generated by Acme ATM Merchant Onboarding System")
    lines.append("=" * 70)

    content = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(content)

    print(f"  ✓ Checklist → {output_path}")


# ─────────────────────────────────────────────
# BANK LETTER  (calls Node.js generator)
# ─────────────────────────────────────────────
def generate_bank_letter(data: dict, output_path: str):
    """Generate the banking relationship letter as a .docx file."""
    import subprocess, json as _json, shutil

    js_script = os.path.join(SCRIPT_DIR, "generate_bank_letter.js")
    if not os.path.exists(js_script):
        print(f"  ⚠ Skipping bank letter — generate_bank_letter.js not found next to script")
        return

    node = shutil.which("node") or "node"
    result = subprocess.run(
        [node, js_script, _json.dumps(data), output_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ✗ Bank letter error: {result.stderr or result.stdout}")
    else:
        print(f"  ✓ Bank Letter → {output_path}")


# ─────────────────────────────────────────────
# EIN ANSWER SHEET  (calls Node.js generator)
# ─────────────────────────────────────────────
def generate_ein_sheet(data: dict, output_path: str):
    """Generate the EIN application answer sheet as a .docx file."""
    import subprocess, json as _json, shutil

    js_script = os.path.join(SCRIPT_DIR, "generate_ein_sheet.js")
    if not os.path.exists(js_script):
        print(f"  ⚠ Skipping EIN sheet — generate_ein_sheet.js not found next to script")
        return

    node = shutil.which("node") or "node"
    result = subprocess.run(
        [node, js_script, _json.dumps(data), output_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ✗ EIN sheet error: {result.stderr or result.stdout}")
    else:
        print(f"  ✓ EIN Sheet → {output_path}")


def generate_cover_sheet(data: dict, output_path: str):
    """Generate the cover sheet as a .docx file."""
    import subprocess, json as _json, shutil

    js_script = os.path.join(SCRIPT_DIR, "generate_cover_sheet.js")
    if not os.path.exists(js_script):
        print(f"  ⚠ Skipping cover sheet — generate_cover_sheet.js not found next to script")
        return

    node = shutil.which("node") or "node"
    result = subprocess.run(
        [node, js_script, _json.dumps(data), output_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ✗ Cover sheet error: {result.stderr or result.stdout}")
    else:
        print(f"  ✓ Cover Sheet → {output_path}")



def generate_llc_guide(data: dict, output_path: str):
    """Generate the state-specific LLC filing guide PDF."""
    import importlib.util, sys as _sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("generate_llc_guide", os.path.join(script_dir, "generate_llc_guide.py"))
    if spec is None:
        print(f"  ⚠ Skipping LLC guide — generate_llc_guide.py not found next to script")
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.generate_llc_guide(data, output_path)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python merchant_onboarding.py merchant_data.json [output_dir]")
        sys.exit(1)

    json_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(json_path) or "."

    os.makedirs(output_dir, exist_ok=True)

    with open(json_path) as f:
        data = json.load(f)

    company_slug = data["merchant"]["company_name"].replace(" ", "_").replace(",", "")[:30]

    print(f"\nGenerating onboarding packet for: {data['merchant']['company_name']}")
    print(f"Output directory: {output_dir}\n")

    generate_exhibit2(data, os.path.join(output_dir, f"{company_slug}_Exhibit2.pdf"))
    generate_exhibit3(data, os.path.join(output_dir, f"{company_slug}_Exhibit3.pdf"))
    generate_w9(data,       os.path.join(output_dir, f"{company_slug}_W9.pdf"))
    generate_checklist(data, os.path.join(output_dir, f"{company_slug}_Checklist.txt"))
    generate_bank_letter(data, os.path.join(output_dir, f"{company_slug}_BankLetter.docx"))
    generate_ein_sheet(data,   os.path.join(output_dir, f"{company_slug}_EIN_Sheet.docx"))
    generate_cover_sheet(data, os.path.join(output_dir, f"{company_slug}_CoverSheet.docx"))
    generate_llc_guide(data,   os.path.join(output_dir, f"{company_slug}_LLCGuide.pdf"))

    print("\n✅ All documents generated successfully.")


if __name__ == "__main__":
    main()
